import json


def guardar_playlist_json(ruta, canciones):
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(canciones, archivo, indent=2, ensure_ascii=False)


def cargar_playlist_json(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)

def exportar_playlist_m3u(ruta, canciones):
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write("#EXTM3U\n")
        for cancion in canciones:
            archivo.write(
                f"#EXTINF:{cancion['duration']},"
                f"{cancion['artist']} - {cancion['title']}\n"
            )
            archivo.write(
                f"{cancion.get('preview') or cancion.get('link')}\n"
            )