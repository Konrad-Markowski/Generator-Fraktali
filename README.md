# Generator Fraktali

Aplikacja graficzna do generowania i wizualizacji różnych typów fraktali, stworzona jako część pracy inżynierskiej. Projekt wykorzystuje bibliotekę DearPyGui do stworzenia interfejsu użytkownika oraz NumPy i Numba do optymalizacji obliczeń.

## Funkcjonalności

Aplikacja umożliwia generowanie i wizualizację następujących fraktali:

### 1. Zbiór Mandelbrota
- Wizualizacja klasycznego zbioru Mandelbrota
- Regulacja maksymalnej liczby iteracji
- Optymalizacja przy użyciu Numba JIT
- Mapowanie kolorów z wykorzystaniem matplotlib (colormap 'hot')

### 2. Paproć Barnsleya
- Generowanie fraktala metodą IFS (Iterated Function System)
- Pełna kontrola nad parametrami transformacji (6 współczynników dla każdej z 4 transformacji)
- Regulacja prawdopodobieństw wyboru transformacji (normalizowane, sprawdzane pod kątem kontrakcji)
- Możliwość resetowania do domyślnych parametrów klasycznej paproci
- Generowanie do 2 milionów punktów
- Równoległe przetwarzanie konwersji dużych zbiorów danych

### 3. Trójkąt Sierpińskiego
Dwie metody generowania:
- **Chaos Game**: Generowanie poprzez iteracyjną metodę chaos game
- **Rekurencyjnie**: Konstrukcja poprzez rekurencyjny podział trójkątów

### 4. Płatek Śniegu Kocha
- Generowanie krzywej Kocha metodą rekurencyjną
- Regulacja poziomu rekursji (0-7)
- Konfigurowalna długość boku początkowego trójkąta

### 5. Własny Fraktal IFS
- Dowolna liczba transformacji afinicznych (IFS)
- Parametry i prawdopodobieństwa definiowane w GUI
- Automatyczny raport kontrakcji (norma spektralna < 1) przed generacją

## Technologie

- **Python 3.x**
- **DearPyGui** - biblioteka GUI do tworzenia interfejsu użytkownika
- **NumPy** - obliczenia numeryczne i manipulacja tablicami
- **Numba** - kompilacja JIT dla optymalizacji wydajności
- **Matplotlib** - mapowanie kolorów dla zbioru Mandelbrota
- **PyInstaller** - narzędzie do pakowania aplikacji w plik wykonywalny (EXE)

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/Konrad-Markowski/kody-inzynierka.git
cd kody-inzynierka
```

2. Zainstaluj wymagane zależności:
```bash
cd fractals
pip install -r requirements.txt
```

## Uruchomienie

### Opcja 1: Uruchomienie z pliku wykonywalnego (Windows)

Dla użytkowników systemu Windows dostępny jest gotowy plik wykonywalny:
- Lokalizacja: `fractals/dist/GeneratorFraktali.exe`
- Wystarczy dwukrotnie kliknąć plik `GeneratorFraktali.exe` lub uruchomić go z linii poleceń

**Uwaga:** Plik wykonywalny działa obecnie tylko na systemie Windows. Wersje dla innych systemów operacyjnych mogą być dostępne w przyszłości.

### Opcja 2: Uruchomienie z kodu źródłowego

```bash
cd fractals
python main_gui.py
```

Aplikacja automatycznie wygeneruje pierwszy fraktal (domyślnie Zbiór Mandelbrota) przy starcie.

## Struktura projektu

```
kody-inzynierka/
├── fractals/
│   ├── main_gui.py              # Główny plik z interfejsem GUI
│   ├── controllers.py           # Logika przełączania i renderowania fraktali
│   ├── renderers.py             # Wspólne funkcje renderujące (ploty, tekstury)
│   ├── constants.py             # Stałe/identyfikatory UI
│   ├── custom_fractal.py        # Obsługa własnych IFS + walidacja kontrakcji
│   ├── mandelbrot_set.py        # Implementacja zbioru Mandelbrota (Numba)
│   ├── barnsley_fern.py         # Implementacja paproci Barnsleya (Numba)
│   ├── sierpinski_triangle.py   # Trójkąt Sierpińskiego (chaos & rekurencja)
│   ├── koch_snowflake.py        # Płatek śniegu Kocha
│   ├── requirements.txt         # Zależności projektu
│   ├── GeneratorFraktali.spec   # Konfiguracja PyInstaller do budowania EXE
│   ├── build/                   # Pliki tymczasowe generowane przez PyInstaller
│   └── dist/
│       └── GeneratorFraktali.exe # Gotowy plik wykonywalny (Windows)
├── materials/                   # Materiały referencyjne i dokumentacja
│   ├── *.pdf                    # Dokumenty źródłowe dotyczące fraktali
│   └── zdjecia/                 # Obrazy i ilustracje fraktali
└── README.md                    # Ten plik
```

## Funkcje interfejsu

- **Panel kontrolny** (lewy): Wybór fraktala i konfiguracja parametrów
- **Panel wizualizacji** (prawy): Wyświetlanie wygenerowanych fraktali
- **Status generowania**: Informacja o czasie generowania fraktala
- **Dynamiczne kontrolki**: Parametry dostosowują się do wybranego typu fraktala
- **Konfiguracja wizualizacji**: Dostosowanie kolorów, rozmiaru punktów i grubości linii

## Optymalizacje

- **Numba JIT**: Kompilacja funkcji obliczeniowych dla zbioru Mandelbrota i paproci Barnsleya
- **Równoległe przetwarzanie**: Konwersja dużych tablic NumPy na listy Python przy użyciu ThreadPoolExecutor
- **Efektywne zarządzanie pamięcią**: Optymalizacja dla dużych zbiorów punktów (do 2M punktów)

## Uwagi techniczne

- Aplikacja automatycznie kompiluje funkcje Numba przy starcie, aby uniknąć opóźnień przy pierwszym użyciu
- Dla bardzo dużych zbiorów punktów (>1M) używane jest równoległe przetwarzanie podczas konwersji danych
- Wizualizacja zbioru Mandelbrota wykorzystuje tekstury RGBA w formacie float32
- Wszystkie wykresy używają równych proporcji osi (equal_aspects=True) dla zachowania kształtu fraktali

## Autor: Konrad Markowski

Projekt stworzony jako część pracy inżynierskiej.
