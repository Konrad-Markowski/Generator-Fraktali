import threading
import time
import traceback

import dearpygui.dearpygui as dpg

from barnsley_fern import barnsley_fern, get_predefined_parameters
from constants import (
    DPG_CONTROL_GROUP,
    DPG_MANDELBROT_IMG_ID,
    DPG_PLOT,
    DPG_RIGHT_PANEL,
    DPG_STATUS_TEXT,
    DPG_TEXTURE_TAG,
    FRACTAL_CUSTOM_IFS,
)
from custom_fractal import CustomIFS
from koch_snowflake import koch_snowflake_points
from mandelbrot_set import mandelbrot_set as mandelbrot_set_numba
from renderers import (
    _create_scatter_plot,
    create_line_theme,
    create_mandelbrot_texture,
    normalize_color,
)
from sierpinski_triangle import sierpinski_triangle_chaos_game, sierpinski_triangle_recursive

# Event do anulowania generowania (prostsze niż flaga boolean)
_generation_cancel_event = threading.Event()
_generation_thread = None


def cancel_generation(_sender, _app_data):
    """Anuluje trwające generowanie fraktala."""
    _generation_cancel_event.set()
    dpg.set_value(DPG_STATUS_TEXT, "Przerywanie generowania...")

    if dpg.does_item_exist("cancel_button"):
        dpg.hide_item("cancel_button")
    if dpg.does_item_exist("generate_button"):
        dpg.show_item("generate_button")


def render_contraction_report(group_tag, report_list, summary, is_ok):
    """Aktualizuje grupę z raportem kontrakcji (kolory: zielony/ czerwony)."""
    if not dpg.does_item_exist(group_tag):
        return
    dpg.delete_item(group_tag, children_only=True)

    for item in report_list:
        color = [0, 180, 0, 255] if item["is_ok"] else [220, 80, 80, 255]
        dpg.add_text(item["text"], parent=group_tag, color=color, wrap=450)

    dpg.add_separator(parent=group_tag)
    summary_color = [0, 180, 0, 255] if is_ok else [220, 80, 80, 255]
    dpg.add_text(summary, parent=group_tag, color=summary_color, wrap=450)


def _clear_previous_render():
    if dpg.does_item_exist(DPG_PLOT):
        dpg.delete_item(DPG_PLOT)
    if dpg.does_item_exist(DPG_MANDELBROT_IMG_ID):
        dpg.delete_item(DPG_MANDELBROT_IMG_ID)


def _normalize_probabilities(probabilities):
    total_prob = sum(probabilities)
    if total_prob <= 0:
        raise ValueError("Suma prawdopodobienstw musi byc dodatnia.")
    return [p / total_prob for p in probabilities]


def _render_mandelbrot():
    if _generation_cancel_event.is_set():
        return
    
    xmin, xmax = -2.0, 1.0
    ymin, ymax = -1.5, 1.5
    max_iter = dpg.get_value("mandel_max_iter")
    width, height = 1000, 1000

    mandelbrot_img = mandelbrot_set_numba(xmin, xmax, ymin, ymax, width, height, max_iter)
    
    if _generation_cancel_event.is_set():
        _clear_previous_render()
        return
    
    texture_data = create_mandelbrot_texture(mandelbrot_img, max_iter)

    if dpg.does_item_exist(DPG_TEXTURE_TAG):
        dpg.delete_item(DPG_TEXTURE_TAG)

    with dpg.texture_registry(show=False):
        dpg.add_raw_texture(
            width,
            height,
            texture_data,
            format=dpg.mvFormat_Float_rgba,  # type: ignore
            tag=DPG_TEXTURE_TAG,
        )

    dpg.add_image(DPG_TEXTURE_TAG, width=width, height=height, tag=DPG_MANDELBROT_IMG_ID, parent=DPG_RIGHT_PANEL)


def _read_barnsley_inputs():
    n_points = dpg.get_value("barnsley_points")
    if n_points > 2000000:
        dpg.set_value(DPG_STATUS_TEXT, f"Generowanie {n_points} punktow... (moze to chwile potrwac)")
        n_points = 2000000

    probabilities = [
        dpg.get_value("barnsley_prob_1"),
        dpg.get_value("barnsley_prob_2"),
        dpg.get_value("barnsley_prob_3"),
        dpg.get_value("barnsley_prob_4"),
    ]

    default_params = get_predefined_parameters()
    for i, prob in enumerate(probabilities):
        if prob is None:
            prob = default_params["probabilities"][i]
            dpg.set_value(f"barnsley_prob_{i + 1}", prob)
            probabilities[i] = prob
        if prob < 0 or prob > 1:
            raise ValueError(
                f"Prawdopodobienstwo dla transformacji {i + 1} musi byc miedzy 0 a 1 (obecna wartosc: {prob})"
            )

    normalized_probs = _normalize_probabilities(probabilities)

    transforms = []
    for i in range(4):
        transforms.append(
            {
                "a": dpg.get_value(f"barnsley_t{i}_a"),
                "b": dpg.get_value(f"barnsley_t{i}_b"),
                "c": dpg.get_value(f"barnsley_t{i}_c"),
                "d": dpg.get_value(f"barnsley_t{i}_d"),
                "e": dpg.get_value(f"barnsley_t{i}_e"),
                "f": dpg.get_value(f"barnsley_t{i}_f"),
            }
        )

    barnsley_params = {"probabilities": normalized_probs, "transforms": transforms}
    return n_points, barnsley_params


def _render_barnsley():
    if _generation_cancel_event.is_set():
        return
    
    n_points, barnsley_params = _read_barnsley_inputs()

    barnsley_ifs = CustomIFS()
    for prob, t in zip(barnsley_params["probabilities"], barnsley_params["transforms"]):
        barnsley_ifs.add_transformation(t["a"], t["b"], t["c"], t["d"], t["e"], t["f"], probability=prob)
    
    if _generation_cancel_event.is_set():
        _clear_previous_render()
        return
    
    barnsley_ok, barnsley_report, barnsley_summary = barnsley_ifs.check_contraction()
    render_contraction_report("barnsley_check_results_group", barnsley_report, barnsley_summary, barnsley_ok)
    if not barnsley_ok:
        print("Ostrzezenie: Paproc Barnsleya nie spelnia warunku kontrakcji.")
        dpg.set_value(DPG_STATUS_TEXT, "Ostrzezenie: kontrakcja niespelniona – generuje mimo to...")

    dpg.set_value(DPG_STATUS_TEXT, f"Generowanie {n_points} punktow...")
    points = barnsley_fern(n_points, barnsley_params)
    
    if _generation_cancel_event.is_set():
        _clear_previous_render()
        return
    
    _create_scatter_plot(points, n_points, "Paproc Barnsleya", "barnsley_color", "barnsley_size", "barnsley_theme")


def _render_sierpinski_chaos():
    if _generation_cancel_event.is_set():
        return
    
    n_points = dpg.get_value("sierpinski_chaos_points")
    if n_points > 2000000:
        dpg.set_value(DPG_STATUS_TEXT, f"Generowanie {n_points} punktow... (moze to chwile potrwac)")
        n_points = 2000000

    dpg.set_value(DPG_STATUS_TEXT, f"Generowanie {n_points} punktow...")
    points = sierpinski_triangle_chaos_game(n_points)
    
    if _generation_cancel_event.is_set():
        _clear_previous_render()
        return
    
    _create_scatter_plot(
        points,
        n_points,
        "Trojkat Sierpinskiego - Chaos",
        "sierpinski_chaos_color",
        "sierpinski_chaos_size",
        "sierpinski_chaos_theme",
    )


def _render_koch():
    if _generation_cancel_event.is_set():
        return
    
    order = dpg.get_value("koch_order")
    dpg.set_value(DPG_STATUS_TEXT, f"Generowanie platka Kocha (poziom {order})...")

    # Uzywamy domyslnej dlugosci boku w funkcji koch_snowflake_points
    points = koch_snowflake_points(order)
    
    if _generation_cancel_event.is_set():
        _clear_previous_render()
        return
    
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError(f"Nieprawidlowy ksztalt danych: {points.shape}, oczekiwano (n, 2)")

    x_data = points[:, 0].tolist()
    y_data = points[:, 1].tolist()

    dpg.add_plot(
        label=f"Platek Sniegu Kocha (Poziom {order})",
        height=-1,
        width=-1,
        tag=DPG_PLOT,
        parent=DPG_RIGHT_PANEL,
        equal_aspects=True,
    )
    primary_x = dpg.add_plot_axis(dpg.mvXAxis, label="X", parent=DPG_PLOT)
    primary_y = dpg.add_plot_axis(dpg.mvYAxis, label="Y", parent=DPG_PLOT)

    color = normalize_color(dpg.get_value("koch_color"))
    line_width = dpg.get_value("koch_line_width")
    line_tag = dpg.add_line_series(x_data, y_data, parent=primary_y)
    create_line_theme(line_tag, color, line_width, "koch_theme")

    dpg.fit_axis_data(primary_x)
    dpg.fit_axis_data(primary_y)


def _render_sierpinski_recursive():
    n = dpg.get_value("sierpinski_n")
    
    if _generation_cancel_event.is_set():
        return
    
    dpg.set_value(DPG_STATUS_TEXT, f"Generowanie trojkatow (poziom {n})...")
    triangles = sierpinski_triangle_recursive(n, lambda: _generation_cancel_event.is_set())
    
    if _generation_cancel_event.is_set() or triangles is None:
        _clear_previous_render()
        return

    dpg.add_plot(
        label=f"Trojkat Sierpinskiego - Rekurencja (Poziom {n})",
        height=-1,
        width=-1,
        tag=DPG_PLOT,
        parent=DPG_RIGHT_PANEL,
        equal_aspects=True,
    )
    primary_x = dpg.add_plot_axis(dpg.mvXAxis, label="X", parent=DPG_PLOT)
    primary_y = dpg.add_plot_axis(dpg.mvYAxis, label="Y", parent=DPG_PLOT)

    color = normalize_color(dpg.get_value("sierpinski_recursive_color"))
    line_width = dpg.get_value("sierpinski_recursive_size")
    
    for i, triangle in enumerate(triangles):
        if _generation_cancel_event.is_set():
            _clear_previous_render()
            return
        
        v0, v1, v2 = triangle[0], triangle[1], triangle[2]
        x_line = [v0[0], v1[0], v2[0], v0[0]]
        y_line = [v0[1], v1[1], v2[1], v0[1]]

        line_tag = dpg.add_line_series(x_line, y_line, parent=primary_y)
        create_line_theme(line_tag, color, line_width, "sierpinski_recursive_line_theme")

    dpg.fit_axis_data(primary_x)
    dpg.fit_axis_data(primary_y)


def _render_custom_ifs():
    if _generation_cancel_event.is_set():
        return
    
    n_points = dpg.get_value("custom_points")
    if n_points > 2000000:
        dpg.set_value(DPG_STATUS_TEXT, f"Generowanie {n_points} punktow... (moze to chwile potrwac)")
        n_points = 2000000

    dpg.set_value(DPG_STATUS_TEXT, f"Generowanie {n_points} punktow...")

    ifs = get_custom_ifs_from_gui()
    
    if _generation_cancel_event.is_set():
        _clear_previous_render()
        return

    is_contraction, report, summary = ifs.check_contraction()
    render_contraction_report("custom_check_results_group", report, summary, is_contraction)
    if not is_contraction:
        print("Ostrzezenie: Generowany IFS moze nie byc kontrakcja.")
        dpg.set_value(DPG_STATUS_TEXT, "Ostrzezenie: kontrakcja niespelniona – generuje mimo to...")

    points = ifs.generate(n_points)
    
    if _generation_cancel_event.is_set():
        _clear_previous_render()
        return

    if len(points) == 0:
        dpg.set_value(DPG_STATUS_TEXT, "Brak punktow (sprawdz parametry).")
        return

    _create_scatter_plot(
        points,
        n_points,
        "Wlasny Fraktal IFS",
        "custom_color",
        "custom_size",
        "custom_theme",
        equal_aspects=False,
    )


_FRACTAL_HANDLERS = {
    "Zbior Mandelbrota": _render_mandelbrot,
    "Paproc Barnsleya": _render_barnsley,
    "Trojkat Sierpinskiego (Chaos Game)": _render_sierpinski_chaos,
    "Platek Sniegu Kocha": _render_koch,
    "Trojkat Sierpinskiego (Rekurencyjnie)": _render_sierpinski_recursive,
    FRACTAL_CUSTOM_IFS: _render_custom_ifs,
}


def _generate_in_thread(fractal_type, start_time):
    """Funkcja wykonywana w osobnym wątku do generowania fraktala."""
    try:
        handler = _FRACTAL_HANDLERS.get(fractal_type)
        if handler is None:
            raise ValueError(f"Nieznany typ fraktala: {fractal_type}")
        
        if _generation_cancel_event.is_set():
            dpg.set_value(DPG_STATUS_TEXT, "Generowanie anulowane.")
            return
        
        handler()
        
        if _generation_cancel_event.is_set():
            dpg.set_value(DPG_STATUS_TEXT, "Generowanie anulowane.")
            return

        elapsed = time.time() - start_time
        dpg.set_value(DPG_STATUS_TEXT, f"Wygenerowano w: {elapsed:.3f} s")
    except Exception as e:
        if not _generation_cancel_event.is_set():
            error_msg = f"Blad Generowania: {e}"
            dpg.set_value(DPG_STATUS_TEXT, error_msg)
            print(f"Blad generowania: {e}")
            traceback.print_exc()
    finally:
        if dpg.does_item_exist("cancel_button"):
            dpg.hide_item("cancel_button")
        if dpg.does_item_exist("generate_button"):
            dpg.show_item("generate_button")
        _generation_cancel_event.clear()


def generate_and_plot(_sender, _app_data):
    global _generation_thread
    
    if _generation_thread is not None and _generation_thread.is_alive():
        return
    
    _generation_cancel_event.clear()
    
    fractal_type = dpg.get_value("fractal_selector")
    start_time = time.time()

    _clear_previous_render()
    dpg.set_value(DPG_STATUS_TEXT, "Generowanie... Czekaj.")
    
    if dpg.does_item_exist("cancel_button"):
        dpg.show_item("cancel_button")
    if dpg.does_item_exist("generate_button"):
        dpg.hide_item("generate_button")

    _generation_thread = threading.Thread(target=_generate_in_thread, args=(fractal_type, start_time), daemon=True)
    _generation_thread.start()


def validate_color_rgba(sender, app_data):
    """Waliduje wartości RGBA - jeśli przekraczają 255, ustawia na 255. Jeśli < 0, ustawia na 0."""
    try:
        color = dpg.get_value(sender)
        if color is None or not isinstance(color, (list, tuple)) or len(color) < 4:
            return
        
        validated_color = [
            max(0, min(255, int(round(float(color[0]))))),
            max(0, min(255, int(round(float(color[1]))))),
            max(0, min(255, int(round(float(color[2]))))),
            max(0, min(255, int(round(float(color[3]))))),
        ]
        
        if validated_color != list(color):
            dpg.set_value(sender, validated_color)
    except (ValueError, TypeError, IndexError):
        pass


def validate_barnsley_prob(sender, app_data):
    try:
        value = dpg.get_value(sender)
        tag = sender
        if tag.startswith("barnsley_prob_"):
            prob_index = int(tag.split("_")[-1]) - 1

            if value < 0.0 or value > 1.0:
                default_params = get_predefined_parameters()
                default_value = default_params["probabilities"][prob_index]
                dpg.set_value(sender, default_value)

        update_barnsley_prob_sum(sender, app_data)
    except (ValueError, TypeError, KeyError):
        pass


def update_barnsley_prob_sum(_sender, _app_data):
    if dpg.does_item_exist("barnsley_prob_sum_text"):
        try:
            prob_sum = sum(
                [
                    dpg.get_value("barnsley_prob_1"),
                    dpg.get_value("barnsley_prob_2"),
                    dpg.get_value("barnsley_prob_3"),
                    dpg.get_value("barnsley_prob_4"),
                ]
            )
            dpg.set_value(
                "barnsley_prob_sum_text",
                f"Suma prawdopodobienstw: {prob_sum:.3f} (zostanie znormalizowana)",
            )
        except (ValueError, TypeError):
            pass


def reset_barnsley_defaults(_sender, _app_data):
    default_params = get_predefined_parameters()

    for i, prob in enumerate(default_params["probabilities"]):
        dpg.set_value(f"barnsley_prob_{i + 1}", prob)

    for i, transform in enumerate(default_params["transforms"]):
        dpg.set_value(f"barnsley_t{i}_a", transform["a"])
        dpg.set_value(f"barnsley_t{i}_b", transform["b"])
        dpg.set_value(f"barnsley_t{i}_c", transform["c"])
        dpg.set_value(f"barnsley_t{i}_d", transform["d"])
        dpg.set_value(f"barnsley_t{i}_e", transform["e"])
        dpg.set_value(f"barnsley_t{i}_f", transform["f"])

    update_barnsley_prob_sum(None, None)


def get_custom_ifs_from_gui():
    ifs = CustomIFS()
    try:
        num_transforms = dpg.get_value("custom_num_transforms")
        for i in range(num_transforms):
            if not dpg.does_item_exist(f"custom_t{i}_a"):
                continue
                
            a = dpg.get_value(f"custom_t{i}_a")
            b = dpg.get_value(f"custom_t{i}_b")
            c = dpg.get_value(f"custom_t{i}_c")
            d = dpg.get_value(f"custom_t{i}_d")
            e = dpg.get_value(f"custom_t{i}_e")
            f_val = dpg.get_value(f"custom_t{i}_f")
            prob = dpg.get_value(f"custom_prob_{i}")
            prob = max(0.0, min(1.0, prob))
            
            ifs.add_transformation(a, b, c, d, e, f_val, prob)
    except Exception:
        pass
    return ifs


def check_custom_contraction(_sender, _app_data):
    ifs = get_custom_ifs_from_gui()
    is_overall_contraction, report_list, summary = ifs.check_contraction()
    
    if dpg.does_item_exist("custom_check_results_group"):
        dpg.delete_item("custom_check_results_group", children_only=True)
    
    parent = "custom_check_results_group"
    
    for item in report_list:
        color = [0, 255, 0, 255] if item["is_ok"] else [255, 100, 100, 255]
        dpg.add_text(item["text"], parent=parent, color=color, wrap=420)
        
    dpg.add_separator(parent=parent)
    
    summary_color = [0, 255, 0, 255] if is_overall_contraction else [255, 100, 100, 255]
    dpg.add_text(summary, parent=parent, color=summary_color, wrap=420)


def rebuild_custom_transforms_fields(_sender, _app_data):
    container = "custom_transforms_container"
    if not dpg.does_item_exist(container):
        return

    dpg.delete_item(container, children_only=True)
    
    try:
        num_transforms = dpg.get_value("custom_num_transforms")
        if num_transforms > 20:
            num_transforms = 20
            dpg.set_value("custom_num_transforms", 20)
        elif num_transforms < 1:
            num_transforms = 1
            dpg.set_value("custom_num_transforms", 1)
            
        default_params = get_predefined_parameters()
        
        for i in range(num_transforms):
            if i < 4:
                t = default_params["transforms"][i]
                prob = default_params["probabilities"][i]
            else:
                t = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0, "f": 0}
                prob = 0.01

            with dpg.collapsing_header(label=f"Transformacja {i + 1}", parent=container, default_open=(i == 0)):
                with dpg.group(horizontal=True):
                    dpg.add_text("Prawdopodobienstwo:")
                    dpg.add_input_float(
                        default_value=prob,
                        tag=f"custom_prob_{i}",
                        width=100,
                        step=0.01,
                        min_value=0.0,
                        max_value=1.0,
                        min_clamped=True,
                        max_clamped=True,
                        format="%.2f",
                    )
                
                dpg.add_text("Macierz (a, b, c, d):")
                with dpg.group(horizontal=True):
                    dpg.add_input_float(default_value=t["a"], tag=f"custom_t{i}_a", width=120, step=0.1, label="a", format="%.2f")
                    dpg.add_input_float(default_value=t["b"], tag=f"custom_t{i}_b", width=120, step=0.1, label="b", format="%.2f")
                with dpg.group(horizontal=True):
                    dpg.add_input_float(default_value=t["c"], tag=f"custom_t{i}_c", width=120, step=0.1, label="c", format="%.2f")
                    dpg.add_input_float(default_value=t["d"], tag=f"custom_t{i}_d", width=120, step=0.1, label="d", format="%.2f")
                
                dpg.add_text("Przesuniecie (e, f):")
                with dpg.group(horizontal=True):
                    dpg.add_input_float(default_value=t["e"], tag=f"custom_t{i}_e", width=120, step=0.1, label="e", format="%.2f")
                    dpg.add_input_float(default_value=t["f"], tag=f"custom_t{i}_f", width=120, step=0.1, label="f", format="%.2f")
                    
    except Exception as e:
        print(f"Blad budowania pol transformacji: {e}")


def update_controls(_sender, app_data):
    dpg.delete_item(DPG_CONTROL_GROUP, children_only=True)

    if app_data == "Zbior Mandelbrota":
        dpg.add_input_int(
            label="Max Iteracji",
            default_value=100,
            min_value=10,
            tag="mandel_max_iter",
            step=10,
            parent=DPG_CONTROL_GROUP,
        )

    elif app_data == "Paproc Barnsleya":
        dpg.add_input_int(
            label="Liczba Punktow",
            default_value=50000,
            min_value=1000,
            tag="barnsley_points",
            step=1000,
            parent=DPG_CONTROL_GROUP,
        )
        dpg.add_separator(parent=DPG_CONTROL_GROUP)

        dpg.add_button(
            label="Przywroc Domyslne Parametry",
            callback=reset_barnsley_defaults,
            parent=DPG_CONTROL_GROUP,
            width=-1,
        )
        dpg.add_separator(parent=DPG_CONTROL_GROUP)

        dpg.add_text("Prawdopodobienstwa (0-1):", parent=DPG_CONTROL_GROUP)
        default_params = get_predefined_parameters()
        for i, prob in enumerate(default_params["probabilities"]):
            dpg.add_input_float(
                label=f"Transformacja {i + 1}",
                default_value=prob,
                min_value=0.0,
                max_value=1.0,
                tag=f"barnsley_prob_{i + 1}",
                parent=DPG_CONTROL_GROUP,
                width=-1,
                step=0.01,
                format="%.3f",
                callback=validate_barnsley_prob,
                min_clamped=True,
                max_clamped=True,
            )

        dpg.add_separator(parent=DPG_CONTROL_GROUP)

        dpg.add_text("Parametry Transformacji (a b c d e f):", parent=DPG_CONTROL_GROUP)
        for i, transform in enumerate(default_params["transforms"]):
            with dpg.collapsing_header(label=f"Transformacja {i + 1}", parent=DPG_CONTROL_GROUP, default_open=(i == 0)):
                dpg.add_text("a:")
                dpg.add_input_float(default_value=transform["a"], tag=f"barnsley_t{i}_a", width=-1, step=0.1, format="%.4f")
                dpg.add_text("b:")
                dpg.add_input_float(default_value=transform["b"], tag=f"barnsley_t{i}_b", width=-1, step=0.1, format="%.4f")
                dpg.add_text("c:")
                dpg.add_input_float(default_value=transform["c"], tag=f"barnsley_t{i}_c", width=-1, step=0.1, format="%.4f")
                dpg.add_text("d:")
                dpg.add_input_float(default_value=transform["d"], tag=f"barnsley_t{i}_d", width=-1, step=0.1, format="%.4f")
                dpg.add_text("e:")
                dpg.add_input_float(default_value=transform["e"], tag=f"barnsley_t{i}_e", width=-1, step=0.1, format="%.4f")
                dpg.add_text("f:")
                dpg.add_input_float(default_value=transform["f"], tag=f"barnsley_t{i}_f", width=-1, step=0.1, format="%.4f")

        dpg.add_separator(parent=DPG_CONTROL_GROUP)
        dpg.add_text("Raport kontrakcji (sprawdzany przy Generuj):", parent=DPG_CONTROL_GROUP)
        dpg.add_group(tag="barnsley_check_results_group", parent=DPG_CONTROL_GROUP)

        dpg.add_separator(parent=DPG_CONTROL_GROUP)
        dpg.add_text("Wizualizacja:", parent=DPG_CONTROL_GROUP)
        dpg.add_color_edit(
            label="Kolor punktow",
            default_value=[0, 200, 0, 255],
            tag="barnsley_color",
            parent=DPG_CONTROL_GROUP,
            width=-1,
            callback=validate_color_rgba,
        )
        dpg.add_slider_float(
            label="Rozmiar punktow",
            default_value=0.5,
            min_value=0.1,
            max_value=5.0,
            tag="barnsley_size",
            parent=DPG_CONTROL_GROUP,
            width=-1,
        )

    elif app_data == "Trojkat Sierpinskiego (Chaos Game)":
        dpg.add_input_int(
            label="Liczba Punktow",
            default_value=100000,
            min_value=1000,
            tag="sierpinski_chaos_points",
            step=10000,
            parent=DPG_CONTROL_GROUP,
        )
        dpg.add_separator(parent=DPG_CONTROL_GROUP)
        dpg.add_text("Wizualizacja:", parent=DPG_CONTROL_GROUP)
        dpg.add_color_edit(
            label="Kolor punktow",
            default_value=[0, 0, 255, 255],
            tag="sierpinski_chaos_color",
            parent=DPG_CONTROL_GROUP,
            width=-1,
            callback=validate_color_rgba,
        )
        dpg.add_slider_float(
            label="Rozmiar punktow",
            default_value=0.5,
            min_value=0.1,
            max_value=5.0,
            tag="sierpinski_chaos_size",
            parent=DPG_CONTROL_GROUP,
            width=-1,
        )

    elif app_data == "Trojkat Sierpinskiego (Rekurencyjnie)":
        dpg.add_input_int(
            label="Poziom Rekursji",
            default_value=4,
            min_value=1,
            max_value=8,
            tag="sierpinski_n",
            parent=DPG_CONTROL_GROUP,
        )
        dpg.add_separator(parent=DPG_CONTROL_GROUP)
        dpg.add_text("Wizualizacja:", parent=DPG_CONTROL_GROUP)
        dpg.add_color_edit(
            label="Kolor punktow",
            default_value=[255, 0, 0, 255],
            tag="sierpinski_recursive_color",
            parent=DPG_CONTROL_GROUP,
            width=-1,
            callback=validate_color_rgba,
        )
        dpg.add_slider_float(
            label="Rozmiar punktow",
            default_value=1.0,
            min_value=0.1,
            max_value=5.0,
            tag="sierpinski_recursive_size",
            parent=DPG_CONTROL_GROUP,
            width=-1,
        )

    elif app_data == "Platek Sniegu Kocha":
        dpg.add_input_int(
            label="Poziom rekursji",
            default_value=4,
            min_value=0,
            max_value=7,
            tag="koch_order",
            parent=DPG_CONTROL_GROUP,
        )
        dpg.add_separator(parent=DPG_CONTROL_GROUP)
        dpg.add_text("Wizualizacja:", parent=DPG_CONTROL_GROUP)
        dpg.add_color_edit(
            label="Kolor linii",
            default_value=[0, 150, 255, 255],
            tag="koch_color",
            parent=DPG_CONTROL_GROUP,
            width=-1,
            callback=validate_color_rgba,
        )
        dpg.add_slider_float(
            label="Grubosc linii",
            default_value=1.5,
            min_value=0.5,
            max_value=5.0,
            tag="koch_line_width",
            parent=DPG_CONTROL_GROUP,
            width=-1,
        )

    elif app_data == FRACTAL_CUSTOM_IFS:
        dpg.add_input_int(
            label="Liczba Punktow",
            default_value=50000,
            min_value=1000,
            tag="custom_points",
            step=1000,
            parent=DPG_CONTROL_GROUP,
        )
        dpg.add_separator(parent=DPG_CONTROL_GROUP)
        
        dpg.add_text("Konfiguracja IFS:", parent=DPG_CONTROL_GROUP)
        with dpg.group(horizontal=True, parent=DPG_CONTROL_GROUP):
            dpg.add_input_int(label="Liczba Transformacji", default_value=2, min_value=1, max_value=10, 
                              tag="custom_num_transforms", width=150)
            dpg.add_button(label="Ustaw", callback=rebuild_custom_transforms_fields)

        dpg.add_group(tag="custom_transforms_container", parent=DPG_CONTROL_GROUP)
        
        rebuild_custom_transforms_fields(None, None)
        
        dpg.add_separator(parent=DPG_CONTROL_GROUP)
        dpg.add_group(tag="custom_check_results_group", parent=DPG_CONTROL_GROUP)
        
        dpg.add_separator(parent=DPG_CONTROL_GROUP)
        dpg.add_text("Wizualizacja:", parent=DPG_CONTROL_GROUP)
        dpg.add_color_edit(label="Kolor punktow", default_value=[200, 0, 200, 255], tag="custom_color",
                           parent=DPG_CONTROL_GROUP, width=-1, callback=validate_color_rgba)
        dpg.add_slider_float(label="Rozmiar punktow", default_value=0.5, min_value=0.1, max_value=5.0,
                             tag="custom_size", parent=DPG_CONTROL_GROUP, width=-1)

    dpg.add_separator(parent=DPG_CONTROL_GROUP)

