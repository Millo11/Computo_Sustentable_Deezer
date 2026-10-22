"""
Módulo de lógica central para la gestión y manipulación de canciones en una lista de reproducción (Playlist).

¿QUÉ HACE ESTE ARCHIVO?
- Proporciona funciones puras para operar sobre listas de canciones (diccionarios):
  ordenamiento por diversos criterios, cálculo de duración total, inserción, eliminación,
  limpieza y desplazamiento de posición (subir/bajar).

¿POR QUÉ LO HACE?
- Desacopla las operaciones de datos de la interfaz de usuario (Tkinter), facilitando pruebas unitarias,
  reutilización de código y mantenimiento bajo el principio de responsabilidad única (Clean Architecture).
"""

from typing import List, Dict, Any


def ordenar_canciones(canciones: List[Dict[str, Any]], criterio: str) -> List[Dict[str, Any]]:
    """
    Ordena una lista de canciones según el criterio especificado sin alterar la lista original.

    ¿QUÉ HACE?
    - Crea una copia superficial de la lista recibida y aplica un criterio de ordenamiento:
      * "Título": Orden alfabético ascendente (A-Z) ignorando mayúsculas/minúsculas.
      * "Artista": Orden alfabético ascendente (A-Z) ignorando mayúsculas/minúsculas.
      * "Menor": De menor duración en segundos a mayor duración.
      * "Mayor": De mayor duración en segundos a menor duración.
      * "Popularidad": De mayor puntaje 'rank' a menor (canciones más escuchadas primero).

    ¿POR QUÉ LO HACE?
    - Permite al usuario organizar visualmente su lista de reproducción según sus preferencias
      (por ejemplo, escuchar primero las más populares o en orden de artista). No muta la lista
      directamente hasta que se devuelve el resultado para evitar efectos secundarios inesperados.
    """
    canciones_ordenadas = list(canciones)

    if "Título" in criterio:
        # Usamos .lower() para asegurar que la ordenación alfabética sea insensible a mayúsculas
        canciones_ordenadas.sort(key=lambda cancion: cancion.get("title", "").lower())
    elif "Artista" in criterio:
        canciones_ordenadas.sort(key=lambda cancion: cancion.get("artist", "").lower())
    elif "Menor" in criterio:
        # Orden ascendente por duración en segundos
        canciones_ordenadas.sort(key=lambda cancion: cancion.get("duration", 0))
    elif "Mayor" in criterio:
        # Orden descendente por duración en segundos
        canciones_ordenadas.sort(
            key=lambda cancion: cancion.get("duration", 0),
            reverse=True,
        )
    elif "Popularidad" in criterio:
        # Orden descendente por popularidad según el rank de Deezer
        canciones_ordenadas.sort(
            key=lambda cancion: cancion.get("rank", 0),
            reverse=True,
        )

    return canciones_ordenadas


def calcular_duracion_total(canciones: List[Dict[str, Any]]) -> int:
    """
    Calcula la suma total de la duración de todas las canciones en la lista.

    ¿QUÉ HACE?
    - Itera sobre la lista acumulando el valor del campo 'duration' (en segundos).

    ¿POR QUÉ LO HACE?
    - Cumple con el requisito del proyecto de mostrar el tiempo total que durará la playlist creada.
    """
    return sum(cancion.get("duration", 0) for cancion in canciones)


def agregar_canciones(playlist: List[Dict[str, Any]], canciones: List[Dict[str, Any]]) -> None:
    """
    Agrega una lista de canciones al final de la playlist existente.

    ¿QUÉ HACE?
    - Extiende la lista 'playlist' agregando los elementos recibidos en 'canciones'.

    ¿POR QUÉ LO HACE?
    - Permite añadir una o múltiples pistas seleccionadas desde los resultados de búsqueda a la playlist activa.
    """
    playlist.extend(canciones)


def quitar_cancion(playlist: List[Dict[str, Any]], indice: int) -> Dict[str, Any]:
    """
    Elimina y devuelve la canción situada en la posición especificada por el índice.

    ¿QUÉ HACE?
    - Extrae el elemento en 'indice' mediante pop().

    ¿POR QUÉ LO HACE?
    - Permite al usuario descartar una canción que ya no desee en su lista de reproducción.
    """
    return playlist.pop(indice)


def limpiar_playlist(playlist: List[Dict[str, Any]]) -> None:
    """
    Vacía por completo la playlist.

    ¿QUÉ HACE?
    - Invoca clear() sobre la lista mutándola a una lista vacía.

    ¿POR QUÉ LO HACE?
    - Permite al usuario reiniciar su playlist desde cero sin tener que borrar pista por pista.
    """
    playlist.clear()


def mover_cancion(playlist: List[Dict[str, Any]], indice: int, desplazamiento: int) -> int:
    """
    Mueve una canción de posición hacia arriba o hacia abajo en la lista.

    ¿QUÉ HACE?
    - Calcula el nuevo índice sumando el desplazamiento (-1 para subir, +1 para bajar).
    - Valida que el nuevo índice se encuentre dentro de los límites válidos de la lista.
    - Intercambia los elementos de lugar mediante asignación simultánea (tupla swap).

    ¿POR QUÉ LO HACE?
    - Permite al usuario reordenar manualmente el orden de reproducción de su playlist.
    - Devuelve el índice resultante para que la interfaz gráfica pueda mantener la pista seleccionada.
    """
    nuevo_indice = indice + desplazamiento

    # Validamos que no se salga de los límites de la lista (por ejemplo, subir el primer elemento o bajar el último)
    if nuevo_indice < 0 or nuevo_indice >= len(playlist):
        return indice

    # Intercambio in-place de elementos
    playlist[indice], playlist[nuevo_indice] = (
        playlist[nuevo_indice],
        playlist[indice],
    )
    return nuevo_indice
