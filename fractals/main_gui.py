import dearpygui.dearpygui as dpg

from barnsley_fern import barnsley_fern, get_predefined_parameters
from constants import (
    DPG_CONTROL_GROUP,
    DPG_RIGHT_PANEL,
    DPG_STATUS_TEXT,
    FRACTAL_CUSTOM_IFS,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)
from controllers import cancel_generation, generate_and_plot, update_controls
from mandelbrot_set import mandelbrot_set as mandelbrot_set_numba


def main_gui():
    dpg.create_context()
    dpg.create_viewport(title="Generator Fraktali", width=VIEWPORT_WIDTH, height=VIEWPORT_HEIGHT)

    with dpg.font_registry():
        font_paths = [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
        default_font = None
        for font_path in font_paths:
            try:
                default_font = dpg.add_font(font_path, 18)
                break
            except:
                continue
        
        if default_font:
            dpg.bind_font(default_font)

    with dpg.window(label="Glowne Okno", tag="main_window", no_title_bar=True, no_resize=False, no_move=True):
        with dpg.group(horizontal=True):
            with dpg.child_window(
                width=480,
                border=False,
                tag="left_panel",
                autosize_x=False,
                height=-1,
                horizontal_scrollbar=True,
            ):
                dpg.add_text("Wybor Fraktala:")
                dpg.add_combo(
                    items=[
                        "Zbior Mandelbrota",
                        "Paproc Barnsleya",
                        "Trojkat Sierpinskiego (Chaos Game)",
                        "Trojkat Sierpinskiego (Rekurencyjnie)",
                        "Platek Sniegu Kocha",
                        FRACTAL_CUSTOM_IFS,
                    ],
                    default_value="Zbior Mandelbrota",
                    callback=update_controls,
                    tag="fractal_selector",
                )
                dpg.add_separator()

                dpg.add_text("Parametry:")
                dpg.add_group(tag=DPG_CONTROL_GROUP)

                update_controls(None, dpg.get_value("fractal_selector"))

                dpg.add_separator()
                dpg.add_button(label="Generuj Fraktal", callback=generate_and_plot, width=-1, tag="generate_button")
                dpg.add_button(label="Przerwij", callback=cancel_generation, width=-1, tag="cancel_button", show=False)
                dpg.add_spacer(height=20)
                dpg.add_text("Status:", tag=DPG_STATUS_TEXT)

            with dpg.child_window(
                width=-1, height=-1, border=True, tag=DPG_RIGHT_PANEL, autosize_x=True, autosize_y=True
            ):
                dpg.add_text("Wynik wizualizacji pojawi sie ponizej", color=[100, 100, 100])

    dpg.setup_dearpygui()
    dpg.show_viewport()

    dpg.set_primary_window("main_window", True)

    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main_gui()

