import numpy as np
from numba import jit

def get_predefined_parameters():
    """
    Zwraca klasyczne parametry paproci Barnsleya.
    Każda transformacja ma prawdopodobieństwo i 6 współczynników (a, b, c, d, e, f).
    """
    return {
        'probabilities': [0.01, 0.85, 0.07, 0.07],
        'transforms': [
            {'a': 0, 'b': 0, 'c': 0, 'd': 0.16, 'e': 0, 'f': 0},
            {'a': 0.85, 'b': 0.04, 'c': -0.04, 'd': 0.85, 'e': 0, 'f': 1.6},
            {'a': 0.2, 'b': -0.26, 'c': 0.23, 'd': 0.22, 'e': 0, 'f': 1.6},
            {'a': -0.15, 'b': 0.28, 'c': 0.26, 'd': 0.24, 'e': 0, 'f': 0.44},
        ]
    }

@jit(nopython=True)
def barnsley_fern_numba(n_points, probabilities, transforms):
    """
    Generuje paproć Barnsleya - zoptymalizowana wersja z Numba.
    Używa IFS (Iterated Function System) - wybiera transformację losowo na podstawie prawdopodobieństw.
    
    Args:
        n_points: liczba punktów do wygenerowania
        probabilities: prawdopodobieństwa wyboru każdej transformacji
        transforms: tablica współczynników transformacji (4x6)
    
    Returns:
        numpy array kształtu (n_points, 2) ze współrzędnymi punktów
    """
    # cumsum pozwala na łatwy wybór transformacji na podstawie przedziałów prawdopodobieństwa
    cumsum_probs = np.cumsum(probabilities)
    points = np.zeros((n_points, 2), dtype=np.float64)
    
    x = 0.0
    y = 0.0
    
    for k in range(n_points):
        r = np.random.rand()
        
        # wybieramy transformację na podstawie losowej liczby i skumulowanych prawdopodobieństw
        transform_idx = 0
        for i in range(len(cumsum_probs)):
            if r <= cumsum_probs[i]:
                transform_idx = i
                break
        
        # stosujemy przekształcenie afiniczne: [x_new, y_new] = [a b; c d] * [x; y] + [e; f]
        t = transforms[transform_idx]
        a, b, c, d, e, f = t[0], t[1], t[2], t[3], t[4], t[5]
        
        new_x = a * x + b * y + e
        new_y = c * x + d * y + f
        
        x, y = new_x, new_y
        points[k, 0] = x
        points[k, 1] = y
    
    return points


def barnsley_fern(n_points, parameters):
    """
    Opakowuje funkcję Numba - przygotowuje dane (słowniki -> numpy arrays) i wywołuje zoptymalizowaną wersję.
    
    Args:
        n_points: liczba punktów do wygenerowania
        parameters: słownik z 'probabilities' i 'transforms'
    
    Returns:
        numpy array z punktami paproci
    """
    probabilities = np.array(parameters['probabilities'], dtype=np.float64)
    transforms_list = parameters['transforms']
    # konwertujemy listę słowników na tablicę numpy (4 transformacje x 6 współczynników)
    transforms_array = np.array([[t['a'], t['b'], t['c'], t['d'], t['e'], t['f']] for t in transforms_list], dtype=np.float64)
    
    return barnsley_fern_numba(n_points, probabilities, transforms_array)
