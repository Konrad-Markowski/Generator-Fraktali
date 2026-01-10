import numpy as np

def sierpinski_triangle_chaos_game(n_points=10000):
    """
    Generuje trójkąt Sierpińskiego metodą chaos game.
    
    Args:
        n_points: liczba punktów do wygenerowania
    
    Returns:
        numpy array kształtu (n_points, 2) z współrzędnymi punktów
    """
    # pomijamy pierwsze 20 iteracji - punkt startowy i pierwsze iteracje nie są częścią fraktala
    # (są tylko pomocnicze do "rozgrzania" algorytmu), więc nie zapisujemy ich do wyników
    vertices = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3)/2]])
    current_point = np.array([0.5, np.sqrt(3)/6])
    
    skip_iterations = 20
    for _ in range(skip_iterations):
        vertex = vertices[np.random.randint(3)]
        current_point = (current_point + vertex) / 2
    
    points = []
    for _ in range(n_points):
        vertex = vertices[np.random.randint(3)]
        current_point = (current_point + vertex) / 2
        points.append(current_point.copy())
    
    return np.array(points)


def sierpinski_triangle_recursive(n):
    """
    Generuje trójkąt Sierpińskiego metodą rekurencyjną.
    Zwraca listę trójkątów (każdy trójkąt to 3 wierzchołki) do rysowania linii.
    
    Args:
        n: poziom rekursji (głębokość podziału)
    
    Returns:
        lista trójkątów, każdy trójkąt to lista 3 wierzchołków (punkty [x, y])
    """
    def generate_triangles(vertices, depth):
        if depth == 0:
            return [vertices]
        

        mid1 = (vertices[0] + vertices[1]) / 2
        mid2 = (vertices[1] + vertices[2]) / 2
        mid3 = (vertices[2] + vertices[0]) / 2

        triangles = []
        triangles.extend(generate_triangles([vertices[0], mid1, mid3], depth - 1))
        triangles.extend(generate_triangles([mid1, vertices[1], mid2], depth - 1))
        triangles.extend(generate_triangles([mid3, mid2, vertices[2]], depth - 1))
        
        return triangles
    
    main_vertices = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3)/2]])
    triangles = generate_triangles(main_vertices, n)
    
    return triangles
