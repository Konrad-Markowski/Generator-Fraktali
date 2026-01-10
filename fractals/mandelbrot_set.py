import numpy as np
from numba import jit

@jit(nopython=True) 
def mandelbrot_set(xmin, xmax, ymin, ymax, width, height, max_iter):
    """
    Generuje macierz wartości iteracji dla zbioru Mandelbrota.
    Zoptymalizowane przez Numba - iteracja jest duplikowana w pętli (zamiast wywołać mandelbrot()),
    bo Numba lepiej optymalizuje inline code.
    
    Args:
        xmin, xmax: zakres osi rzeczywistej
        ymin, ymax: zakres osi urojonej
        width, height: rozmiar macierzy wynikowej
        max_iter: maksymalna liczba iteracji
    
    Returns:
        macierz int32 z wartościami iteracji dla każdego piksela
    """
    r1 = np.linspace(xmin, xmax, width)
    r2 = np.linspace(ymin, ymax, height)
    # int32 zamiast int64 - szybsze i wystarczające (wartości iteracji są małe)
    mset = np.zeros((height, width), dtype=np.int32) 

    for i in range(height):
        for j in range(width):
            c = complex(r1[j], r2[i])
            z = 0 + 0j
            n = 0
            while abs(z) <= 2 and n < max_iter:
                z = z*z + c
                n += 1
            mset[i, j] = n

    return mset
