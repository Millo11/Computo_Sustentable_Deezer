import json
import urllib.parse
import urllib.request


class DeezerAPI:
    BASE_URL = "https://api.deezer.com"

    @staticmethod
    def _get(endpoint, params=None):
        url = f"{DeezerAPI.BASE_URL}{endpoint}"
        if params:
            url += f"?{urllib.parse.urlencode(params)}"

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
            print(f"Error al conectar con Deezer: {e}")
            raise e

        return None

    @classmethod
    def buscar_artistas(cls, query):
        """Busca artistas por nombre y devuelve lista de coincidencias."""
        res = cls._get("/search/artist", {"q": query, "limit": 10})
        return res.get("data", []) if res else []

    @classmethod
    def obtener_top_canciones(cls, artist_id, limit=10):
        """Obtiene las canciones más populares de un artista por ID."""
        res = cls._get(f"/artist/{artist_id}/top", {"limit": limit})
        return res.get("data", []) if res else []

    @classmethod
    def buscar_canciones(cls, query, limit=25):
        """Busca canciones por término."""
        res = cls._get("/search", {"q": query, "limit": limit})
        return res.get("data", []) if res else []

    @classmethod
    def buscar_top_artista_formateado(cls, query, limit=10):
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
    def buscar_canciones_formateadas(cls, query, limit=25):
        canciones = cls.buscar_canciones(query, limit=limit)
        return [formatear_cancion(cancion) for cancion in canciones]


def formatear_cancion(cancion, nombre_artista=None, album_default=""):
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