import multiprocessing
from concurrent.futures import ThreadPoolExecutor

import dearpygui.dearpygui as dpg
import matplotlib
import numpy as np

from constants import (
    DPG_CONTROL_GROUP,
    DPG_PLOT,
    DPG_RIGHT_PANEL,
    DPG_STATUS_TEXT,
)


def _convert_batch_to_list(args):
    data_array, start_idx, end_idx = args
    return data_array[start_idx:end_idx].tolist()


def convert_array_to_list_parallel(data_array, batch_size=500000):
    data_len = len(data_array)

    if data_len < batch_size:
        return data_array.tolist()

    num_threads = min(multiprocessing.cpu_count(), 8)
    batches = []
    for i in range(0, data_len, batch_size):
        end_idx = min(i + batch_size, data_len)
        batches.append((data_array, i, end_idx))

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(_convert_batch_to_list, batches))

    result_list = []
    for batch_result in results:
        result_list.extend(batch_result)

    return result_list


def normalize_color(color):
    if not hasattr(color, "__getitem__"):
        raise ValueError(f"Nieprawidlowy format koloru: {type(color)}")

    color_list = list(color[:3])

    if any(c > 1.0 for c in color_list):
        return [int(max(0, min(255, round(c)))) for c in color_list] + [255]
    else:
        return [int(max(0, min(255, round(c * 255)))) for c in color_list] + [255]


def convert_points_to_lists(x_data, y_data, status_text_tag=DPG_STATUS_TEXT):
    if len(x_data) > 1000000:
        if dpg.does_item_exist(status_text_tag):
            dpg.set_value(status_text_tag, f"Konwertowanie danych ({len(x_data)} punktow)...")
        x_data_list = convert_array_to_list_parallel(x_data)
        y_data_list = convert_array_to_list_parallel(y_data)
        if dpg.does_item_exist(status_text_tag):
            dpg.set_value(status_text_tag, f"Tworzenie wykresu ({len(x_data_list)} punktow)...")
    else:
        if isinstance(x_data, np.ndarray):
            x_data_list = x_data.tolist()
            y_data_list = y_data.tolist()
        else:
            x_data_list = x_data
            y_data_list = y_data
    return x_data_list, y_data_list


def _create_theme_tag(color, size_value, theme_prefix):
    rounded_size = round(size_value, 2)
    color_str = f"{color[0]}_{color[1]}_{color[2]}"
    return f"{theme_prefix}_{rounded_size}_{color_str}"


def _create_plot_theme(item_tag, color, size_value, theme_prefix, component_type, style_var):
    theme_tag = _create_theme_tag(color, size_value, theme_prefix)
    if not dpg.does_item_exist(theme_tag):
        with dpg.theme(tag=theme_tag):
            with dpg.theme_component(component_type):
                dpg.add_theme_color(dpg.mvPlotCol_Line, color, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(style_var, size_value, category=dpg.mvThemeCat_Plots)
    dpg.bind_item_theme(item_tag, theme_tag)


def create_scatter_theme(scatter_tag, color, point_size, theme_prefix):
    _create_plot_theme(
        scatter_tag,
        color,
        point_size,
        theme_prefix,
        dpg.mvScatterSeries,
        dpg.mvPlotStyleVar_MarkerSize,
    )


def create_line_theme(line_tag, color, line_width, theme_prefix):
    _create_plot_theme(
        line_tag,
        color,
        line_width,
        theme_prefix,
        dpg.mvLineSeries,
        dpg.mvPlotStyleVar_LineWeight,
    )


def _create_scatter_plot(points, n_points, plot_label, color_tag, size_tag, theme_prefix, equal_aspects=True):
    points = np.array(points)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError(f"Nieprawidlowy ksztalt danych: {points.shape}, oczekiwano (n, 2)")

    dpg.set_value(DPG_STATUS_TEXT, f"Przygotowywanie wykresu ({n_points} punktow)...")

    x_data = points[:, 0]
    y_data = points[:, 1]

    dpg.add_plot(
        label=f"{plot_label} ({n_points} pkt)",
        height=-1,
        width=-1,
        tag=DPG_PLOT,
        parent=DPG_RIGHT_PANEL,
        equal_aspects=equal_aspects,
    )
    primary_x = dpg.add_plot_axis(dpg.mvXAxis, label="X", parent=DPG_PLOT)
    primary_y = dpg.add_plot_axis(dpg.mvYAxis, label="Y", parent=DPG_PLOT)

    color = normalize_color(dpg.get_value(color_tag))
    point_size = dpg.get_value(size_tag)

    x_data_list, y_data_list = convert_points_to_lists(x_data, y_data)
    scatter_tag = dpg.add_scatter_series(x_data_list, y_data_list, parent=primary_y)
    create_scatter_theme(scatter_tag, color, point_size, theme_prefix)

    dpg.fit_axis_data(primary_x)
    dpg.fit_axis_data(primary_y)


def create_mandelbrot_texture(mandelbrot_array, max_iter):
    mandelbrot_array = np.flipud(mandelbrot_array)
    normalized_array = mandelbrot_array / max_iter
    hot_colormap = matplotlib.colormaps["hot"]
    colors = hot_colormap(normalized_array)
    return colors.astype(np.float32).flatten()

