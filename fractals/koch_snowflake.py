import numpy as np

_COS_60 = 0.5
_SIN_60 = np.sqrt(3) / 2
_ROTATION = np.array(
    [[_COS_60, _SIN_60], [-_SIN_60, _COS_60]],
    dtype=np.float64,
)


def _generate_segment(p1: np.ndarray, p2: np.ndarray, depth: int) -> list[np.ndarray]:
    """Zwraca punkty jednego segmentu krzywej Kocha."""
    if depth == 0:
        return [p2]

    vector = (p2 - p1) / 3.0
    p_a = p1 + vector
    p_c = p1 + 2.0 * vector
    p_d = p_a + _ROTATION @ vector

    points: list[np.ndarray] = []
    points.extend(_generate_segment(p1, p_a, depth - 1))
    points.extend(_generate_segment(p_a, p_d, depth - 1))
    points.extend(_generate_segment(p_d, p_c, depth - 1))
    points.extend(_generate_segment(p_c, p2, depth - 1))
    return points


def koch_snowflake_points(order: int, side_length: float = 1.0) -> np.ndarray:
    """
    Generuje punkty należące do płatka śniegu Kocha.

    Args:
        order: poziom rekursji (>=0).
        side_length: długość początkowego boku trójkąta równobocznego.

    Returns:
        np.ndarray shape (N, 2) zawierająca kolejne punkty krzywej.
    """
    if order < 0:
        raise ValueError("Order must be non-negative.")
    if side_length <= 0.0:
        raise ValueError("Side length must be positive.")

    height = side_length * np.sqrt(3) / 2.0
    v1 = np.array([0.0, 0.0], dtype=np.float64)
    v2 = np.array([side_length, 0.0], dtype=np.float64)
    v3 = np.array([side_length / 2.0, height], dtype=np.float64)

    points: list[np.ndarray] = [v1]
    for start, end in ((v1, v2), (v2, v3), (v3, v1)):
        points.extend(_generate_segment(start, end, order))

    return np.vstack(points)