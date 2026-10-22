"""
Módulo de persistencia y exportación de listas de reproducción.

¿QUÉ HACE ESTE ARCHIVO?
- Proporciona funciones de lectura y escritura en disco para guardar y cargar playlists:
  1. Serialización y deserialización en formato JSON (datos estructurados completos).
  2. Exportación a formato M3U estándar (compatible con reproductores multimedia como VLC, Windows Media Player, etc.).

¿POR QUÉ LO HACE?
- Permite que las listas creadas por el usuario no se pierdan al cerrar el programa y puedan ser
  reutilizadas tanto dentro de la aplicación como en reproductores externos.
"""

import json
from typing import Any, Dict, List


def guardar_playlist_json(ruta: str, canciones: List[Dict[str, Any]]) -> None:
    """
    Guarda la lista de canciones en un archivo de texto en formato JSON.

    ¿QUÉ HACE?
    - Abre el archivo en modo escritura con codificación UTF-8 y vuelca la lista 'canciones'
      con sangría legible de 2 espacios e inhabilitando el escape de caracteres no ASCII.

    ¿POR QUÉ LO HACE?
    - Proporciona una forma persistente y legible de almacenar todos los metadatos de las canciones
      (título, artista, álbum, duración, rank, links), permitiendo recuperar la lista exactamente en sesiones posteriores.
    """
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(canciones, archivo, indent=2, ensure_ascii=False)


def cargar_playlist_json(ruta: str) -> List[Dict[str, Any]]:
    """
    Carga y devuelve una lista de canciones desde un archivo JSON existente.

    ¿QUÉ HACE?
    - Abre el archivo en modo lectura con codificación UTF-8 y analiza su contenido con json.load().

    ¿POR QUÉ LO HACE?
    - Permite al usuario reanudar o consultar una lista de reproducción guardada previamente en el disco.
    """
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def exportar_playlist_m3u(ruta: str, canciones: List[Dict[str, Any]]) -> None:
    """
    Exporta la lista de canciones al formato estándar de lista de reproducción M3U con directivas extendidas.

    ¿QUÉ HACE?
    - Escribe la cabecera '#EXTM3U'.
    - Para cada pista, escribe la directiva '#EXTINF:<duración>,<Artista> - <Título>'.
    - Escribe la URL de transmisión directa (preview MP3 de Deezer o link web).

    ¿POR QUÉ LO HACE?
    - El formato M3U es el estándar universal de listas de reproducción reconocido por reproductores como VLC.
      Al incluir la URL del preview de Deezer, el usuario puede reproducir directamente la lista de canciones
      en su reproductor multimedia favorito sin requerir archivos locales descargados.
    """
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write("#EXTM3U\n")
        for cancion in canciones:
            # Línea de metadatos de la pista (duración en segundos y nombre legible)
            archivo.write(
                f"#EXTINF:{cancion.get('duration', 0)},"
                f"{cancion.get('artist', 'Desconocido')} - {cancion.get('title', 'Sin título')}\n"
            )
            # URL de reproducción (se prioriza el enlace al preview de audio MP3)
            url_reproduccion = cancion.get("preview") or cancion.get("link", "")
            archivo.write(f"{url_reproduccion}\n")
