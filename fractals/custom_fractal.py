import numpy as np
from numba import jit

class CustomIFS:
    """
    Klasa do obsługi własnych systemów funkcji iterowanych (IFS).
    Pozwala definiować transformacje, sprawdzać czy są kontrakcjami
    i generować odpowiadające im fraktale.
    """
    def __init__(self):
        self.transforms = []
        self.probabilities = []

    def add_transformation(self, a, b, c, d, e, f, probability=1.0):
        """
        Dodaje nową transformację afiniczną do systemu.
        x' = ax + by + e
        y' = cx + dy + f
        """
        self.transforms.append({
            'a': float(a), 'b': float(b), 
            'c': float(c), 'd': float(d), 
            'e': float(e), 'f': float(f)
        })
        self.probabilities.append(float(probability))

    def check_contraction(self):
        """
        Sprawdza, czy zdefiniowany system IFS składa się z odwzorowań zwężających (kontrakcji).
        
        Returns:
            tuple: (is_guaranteed (bool), report_list (list), summary_msg (str))
        """
        if not self.transforms:
            return False, [], "Brak zdefiniowanych transformacji."

        is_fractal_guaranteed = True
        report_list = []
        
        for i, t in enumerate(self.transforms):
            matrix = np.array([
                [t['a'], t['b']],
                [t['c'], t['d']]
            ])
            

            spectral_norm = np.linalg.norm(matrix, 2)
            
            is_contraction = spectral_norm < 1.0
            
            status = "OK (Kontrakcja)" if is_contraction else "UWAGA: Nie jest kontrakcja"
            if not is_contraction:
                is_fractal_guaranteed = False
                
            report_list.append({
                'text': f"Transformacja {i+1}: Norma = {spectral_norm:.4f} -> {status}",
                'is_ok': is_contraction
            })

        if is_fractal_guaranteed:
            final_msg = "Wnioski: Wszystkie transformacje sa kontrakcjami.\nSystem IFS zagwarantuje powstanie poprawnego fraktala."
        else:
            final_msg = "Wnioski: Niektore transformacje rozszerzaja przestrzen (norma >= 1).\nFraktal moze nie powstac lub byc nieograniczony."

        return is_fractal_guaranteed, report_list, final_msg

    def generate(self, n_points=100000):
        """
        Generuje punkty fraktala metodą Chaos Game.
        """
        if not self.transforms:
            return np.array([])

        probs = np.array(self.probabilities, dtype=np.float64)

        if len(probs) != len(self.transforms):
            raise ValueError("Liczba prawdopodobienstw nie zgadza sie z liczba transformacji.")

        probs = np.clip(probs, 0.0, np.inf)
        total_prob = np.sum(probs)
        if total_prob <= 0.0:
            raise ValueError("Suma prawdopodobienstw musi byc > 0.")

        probs = probs / total_prob

        transforms_array = np.zeros((len(self.transforms), 6), dtype=np.float64)
        for i, t in enumerate(self.transforms):
            transforms_array[i] = [t['a'], t['b'], t['c'], t['d'], t['e'], t['f']]

        return _generate_ifs_numba(n_points, probs, transforms_array)

@jit(nopython=True)
def _generate_ifs_numba(n_points, probabilities, transforms):
    """
    Implementacja Chaos Game używająca Numba.
    """
    cumsum_probs = np.cumsum(probabilities)
    points = np.zeros((n_points, 2), dtype=np.float64)
    valid_count = 0
    limit = 10000.0
    
    x, y = 0.0, 0.0
    
    for _ in range(100):
        r = np.random.rand()
        idx = 0
        for i in range(len(cumsum_probs)):
            if r <= cumsum_probs[i]:
                idx = i
                break
        
        t = transforms[idx]
        nx = t[0] * x + t[1] * y + t[4]
        ny = t[2] * x + t[3] * y + t[5]
        x, y = nx, ny


    for k in range(n_points):
        r = np.random.rand()
        idx = 0
        for i in range(len(cumsum_probs)):
            if r <= cumsum_probs[i]:
                idx = i
                break
        
        t = transforms[idx]
        # x' = ax + by + e
        # y' = cx + dy + f
        nx = t[0] * x + t[1] * y + t[4]
        ny = t[2] * x + t[3] * y + t[5]
        
        x, y = nx, ny
        
        # Filtrowanie punktów, które "uciekły" zbyt daleko - żeby nie skalować wykresu do dużych wartości
        if abs(x) < limit and abs(y) < limit:
            points[valid_count, 0] = x
            points[valid_count, 1] = y
            valid_count += 1
        
        if abs(x) > 1e15 or abs(y) > 1e15:
            x, y = 0.0, 0.0
        
    return points[:valid_count]


if __name__ == "__main__":
    ifs = CustomIFS()
    
    ifs.add_transformation(0, 0, 0, 0.16, 0, 0, 0.01)
    ifs.add_transformation(0.85, 0.04, -0.04, 0.85, 0, 1.6, 0.85)
    ifs.add_transformation(0.2, -0.26, 0.23, 0.22, 0, 1.6, 0.07)
    ifs.add_transformation(-0.15, 0.28, 0.26, 0.24, 0, 0.44, 0.07)
    
    is_valid, report, message = ifs.check_contraction()
    print(message)
    for r in report:
        print(r['text'])
    
    if is_valid:
        print("\nGenerowanie punktów...")
        pts = ifs.generate(1000)
        print(f"Wygenerowano {len(pts)} punktów.")

