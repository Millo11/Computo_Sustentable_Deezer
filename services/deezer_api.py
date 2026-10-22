"""
Servicio de comunicación y consulta con la API REST pública de Deezer.

¿QUÉ HACE ESTE ARCHIVO?
- Realiza peticiones HTTP GET a los endpoints oficiales de Deezer sin necesidad de librerías externas (usa urllib y json estándar).
- Proporciona métodos para buscar artistas, obtener las canciones más populares de un artista, buscar canciones por texto y formatear los datos obtenidos en una estructura uniforme.

¿POR QUÉ LO HACE?
- Centraliza toda la lógica de red y serialización de datos de Deezer en una sola capa de servicio, facilitando su consumo por parte de la interfaz gráfica y permitiendo un manejo robusto de excepciones y límites de consulta.
"""

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


class DeezerAPI:
    """Cliente estático para consultar los servicios web públicos de Deezer."""
    
    BASE_URL = "https://api.deezer.com"

    @staticmethod
    def _get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Ejecuta una petición HTTP GET al endpoint indicado de la API de Deezer.

        ¿QUÉ HACE?
        - Construye la URL completa concatenando el endpoint y codificando los parámetros de consulta.
        - Agrega una cabecera 'User-Agent' para identificar adecuadamente la aplicación cliente.
        - Establece un tiempo de espera (timeout) de 10 segundos y decodifica la respuesta JSON en caso de éxito.

        ¿POR QUÉ LO HACE?
        - Evita repetir lógica de conexión en cada método de búsqueda.
        - Usa únicamente la biblioteca estándar de Python (urllib), asegurando que el proyecto no requiera dependencias pesadas adicionales (como 'requests'), reduciendo la huella de software (principio de cómputo sustentable).
        """
        url = f"{DeezerAPI.BASE_URL}{endpoint}"
        if params:
            # Codifica los parámetros como query string seguro (ej. ?q=Daft+Punk&limit=10)
            url += f"?{urllib.parse.urlencode(params)}"

        # Especificamos User-Agent para cumplir con buenas prácticas y evitar bloqueos por parte de la API
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DeezerPlaylistOrganizer/2.0 (Python/Tkinter)"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = response.read().decode("utf-8")
                    return json.loads(data)
        except Exception as e:
            # Notificamos el error en consola para depuración y relanzamos para manejo en capas superiores
            print(f"Error al conectar con Deezer: {e}")
            raise e

        return None

    @classmethod
    def buscar_artistas(cls, query: str) -> List[Dict[str, Any]]:
        """
        Busca artistas por nombre y devuelve la lista de coincidencias.

        ¿QUÉ HACE?
        - Llama al endpoint '/search/artist' de Deezer con el nombre solicitado.

        ¿POR QUÉ LO HACE?
        - Permite localizar el identificador único (ID) del artista ingresado por el usuario
          para posteriormente consultar su discografía o canciones destacadas.
        """
        res = cls._get("/search/artist", {"q": query, "limit": 10})
        return res.get("data", []) if res else []

    @classmethod
    def obtener_top_canciones(cls, artist_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las canciones más populares (Top Tracks) de un artista usando su identificador numérico.

        ¿QUÉ HACE?
        - Consulta el endpoint '/artist/{artist_id}/top' limitando los resultados según el parámetro dado.

        ¿POR QUÉ LO HACE?
        - Permite al usuario descubrir rápidamente los éxitos de un artista para incorporarlos a su lista.
        """
        res = cls._get(f"/artist/{artist_id}/top", {"limit": limit})
        return res.get("data", []) if res else []

    @classmethod
    def buscar_canciones(cls, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Realiza una búsqueda general de canciones por término o palabra clave.

        ¿QUÉ HACE?
        - Consulta el endpoint general '/search' con el término indicado.

        ¿POR QUÉ LO HACE?
        - Permite al usuario buscar canciones directas cuando no busca un artista específico
          sino una canción por su nombre o temática.
        """
        res = cls._get("/search", {"q": query, "limit": limit})
        return res.get("data", []) if res else []

    @classmethod
    def buscar_top_artista_formateado(cls, query: str, limit: int = 10) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Busca un artista, obtiene su top de canciones y las devuelve estructuradas de forma normalizada.

        ¿QUÉ HACE?
        - Busca primero los artistas que coincidan con la búsqueda.
        - Toma el primer resultado (la mejor coincidencia) y consulta sus mejores pistas.
        - Mapea y normaliza cada canción obtenida usando 'formatear_cancion'.

        ¿POR QUÉ LO HACE?
        - Automatiza el flujo de dos pasos (buscar ID -> obtener top pistas) en una sola llamada de conveniencia
          para mantener limpio el código de la interfaz gráfica.
        """
        artistas = cls.buscar_artistas(query)
        if not artistas:
            return None, []

        artista = artistas[0]
        canciones = cls.obtener_top_canciones(artista["id"], limit=limit)
        formateadas = [
            formatear_cancion(
                cancion,
                nombre_artista=artista.get("name", query),
                album_default="Desconocido",
            )
            for cancion in canciones
        ]

        return artista, formateadas

    @classmethod
    def buscar_canciones_formateadas(cls, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Busca canciones por texto y devuelve una lista de canciones normalizadas.

        ¿QUÉ HACE?
        - Llama a 'buscar_canciones' y transforma la lista de respuestas usando 'formatear_cancion'.

        ¿POR QUÉ LO HACE?
        - Garantiza que cualquier lista de pistas en la aplicación tenga el mismo formato estandarizado,
          evitando errores por claves faltantes en la UI o en los archivos guardados.
        """
        canciones = cls.buscar_canciones(query, limit=limit)
        return [formatear_cancion(cancion) for cancion in canciones]


def formatear_cancion(cancion: Dict[str, Any], nombre_artista: Optional[str] = None, album_default: str = "") -> Dict[str, Any]:
    """
    Estandariza los datos brutos de una canción recibida desde la API de Deezer a un diccionario homogéneo.

    ¿QUÉ HACE?
    - Extrae únicamente los campos necesarios para la aplicación:
      * 'id': Identificador único en Deezer.
      * 'title': Nombre de la canción.
      * 'artist': Nombre del artista o banda.
      * 'album': Nombre del álbum.
      * 'duration': Duración en segundos.
      * 'rank': Nivel de popularidad en el catálogo de Deezer.
      * 'link': Enlace web directo a Deezer.
      * 'preview': Enlace al clip de audio de 30 segundos en formato MP3.

    ¿POR QUÉ LO HACE?
    - La API de Deezer devuelve docenas de campos que no son necesarios y consumen memoria adicional.
    - Asegura que los nombres de las claves sean uniformes y confiables a través de toda la aplicación,
      simplificando el código de la vista y almacenamiento.
    """
    if nombre_artista is None:
        nombre_artista = cancion.get("artist", {}).get("name", "")

    return {
        "id": cancion.get("id"),
        "title": cancion.get("title", ""),
        "artist": nombre_artista,
        "album": cancion.get("album", {}).get("title", album_default),
        "duration": cancion.get("duration", 0),
        "rank": cancion.get("rank", 0),
        "link": cancion.get("link", ""),
        "preview": cancion.get("preview", ""),
    }
