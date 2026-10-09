def ordenar_canciones(canciones, criterio):
    canciones_ordenadas = list(canciones)

    if "Título" in criterio:
        canciones_ordenadas.sort(key=lambda cancion: cancion["title"].lower())
    elif "Artista" in criterio:
        canciones_ordenadas.sort(key=lambda cancion: cancion["artist"].lower())
    elif "Menor" in criterio:
        canciones_ordenadas.sort(key=lambda cancion: cancion["duration"])
    elif "Mayor" in criterio:
        canciones_ordenadas.sort(
            key=lambda cancion: cancion["duration"],
            reverse=True,
        )
    elif "Popularidad" in criterio:
        canciones_ordenadas.sort(
            key=lambda cancion: cancion["rank"],
            reverse=True,
        )
    return canciones_ordenadas

def calcular_duracion_total(canciones):
    return sum(cancion["duration"] for cancion in canciones)

def agregar_canciones(playlist, canciones):
    playlist.extend(canciones)

def quitar_cancion(playlist, indice):
    playlist.pop(indice)

def limpiar_playlist(playlist):
    playlist.clear()

def mover_cancion(playlist, indice, desplazamiento):
    nuevo_indice = indice + desplazamiento

    if nuevo_indice < 0 or nuevo_indice >= len(playlist):
        return indice

    playlist[indice], playlist[nuevo_indice] = (
        playlist[nuevo_indice],
        playlist[indice],
    )
    return nuevo_indice