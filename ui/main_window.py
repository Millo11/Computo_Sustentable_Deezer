"""
Interfaz Gráfica de Usuario (GUI) para la aplicación Deezer Playlist Organizer.

¿QUÉ HACE ESTE ARCHIVO?
- Implementa la ventana principal y todos los componentes visuales interactivos usando Tkinter y ttk:
  * Panel izquierdo: Buscador integrado con Deezer (por artista o por canción) y tabla de resultados.
  * Panel derecho: Tabla de la playlist personalizada del usuario, herramientas de reordenamiento
    (subir, bajar, eliminar, limpiar, ordenar por criterios) y botones de persistencia/exportación (JSON y M3U).
  * Barra de estado inferior con retroalimentación en tiempo real.
  * Hilos de ejecución (threading) para realizar búsquedas en segundo plano sin congelar la ventana.

¿POR QUÉ LO HACE?
- Proporciona una interfaz moderna, responsiva, amigable e intuitiva para que el usuario pueda
  interactuar de forma gráfica con las funciones del sistema sin recurrir a la línea de comandos.
"""

import os
import sys
import threading
import webbrowser
from datetime import timedelta
from typing import Any, Dict, List

from core.playlist import (
    agregar_canciones,
    calcular_duracion_total,
    limpiar_playlist as limpiar_lista,
    mover_cancion,
    ordenar_canciones,
    quitar_cancion,
)
from services.deezer_api import DeezerAPI
from storage.playlist_files import (
    cargar_playlist_json,
    exportar_playlist_m3u,
    guardar_playlist_json,
)

# Verificación de soporte de Tkinter (en algunos entornos Linux puede requerir python3-tk)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    print("ERROR: Tkinter no está instalado.")
    print("En Ubuntu/Debian ejecuta: sudo apt install python3-tk")
    sys.exit(1)


class DeezerApp(tk.Tk):
    """
    Ventana principal de la aplicación organizadora de listas de reproducción de Deezer.
    Hereda de tk.Tk para actuar como ventana raíz.
    """

    def __init__(self) -> None:
        """
        Inicializa la ventana principal, estilos visuales, estado en memoria y controles de interfaz.
        """
        super().__init__()

        # Configuración básica de la ventana
        self.title("Deezer Playlist Organizer - Python Desktop")
        self.geometry("1100x700")
        self.minsize(960, 600)

        # Cargar ícono de la app (soporta ejecución directa y binario empaquetado por PyInstaller)
        base_dir = getattr(sys, '_MEIPASS', os.path.abspath("."))
        icon_path = os.path.join(base_dir, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Paleta de colores Dark Slate moderna para reducir el cansancio visual
        self.colors = {
            "bg": "#121214",            # Fondo principal oscuro
            "card": "#1a1a1e",          # Fondo de paneles contenedores
            "card_light": "#26262b",    # Fondo para botones secundarios y cabeceras
            "text": "#f4f4f5",          # Texto claro principal
            "text_muted": "#a1a1aa",    # Texto secundario / grisáceo
            "accent": "#e11d48",        # Rojo/Rosa distintivo estilo Deezer
            "accent_hover": "#be123c",
            "secondary": "#2563eb",     # Azul para acciones principales
            "border": "#2e2e36"         # Borde sutil de separación
        }

        self.configure(bg=self.colors["bg"])

        # Estado en memoria de la sesión
        self.playlist: List[Dict[str, Any]] = []            # Canciones añadidas a la playlist actual
        self.resultados_busqueda: List[Dict[str, Any]] = [] # Últimos resultados obtenidos de Deezer

        # Métodos de inicialización modular
        self._configurar_estilos()
        self._construir_interfaz()

    def _configurar_estilos(self) -> None:
        """
        Aplica tema y estilos personalizados a los componentes ttk (tablas Treeview, etc.).

        ¿POR QUÉ LO HACE?
        - Asegura una apariencia visual homogénea y moderna en toda la aplicación.
        """
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure(
            ".",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10)
        )
        self.style.configure(
            "Treeview",
            background=self.colors["card"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["card"],
            rowheight=28,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        self.style.map(
            "Treeview",
            background=[("selected", self.colors["accent"])],
            foreground=[("selected", "#ffffff")]
        )
        self.style.configure(
            "Treeview.Heading",
            background=self.colors["card_light"],
            foreground=self.colors["text"],
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )

    def _construir_interfaz(self) -> None:
        """
        Distribuye los bloques principales de la interfaz: cabecera superior, paneles divisores y barra de estado.
        """
        # 1. ENCABEZADO SUPERIOR
        header = tk.Frame(self, bg=self.colors["card"], height=60, padx=20, pady=12)
        header.pack(fill="x", side="top")

        tk.Label(
            header,
            text="🎵 Deezer Playlist Organizer",
            font=("Segoe UI", 15, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["card"]
        ).pack(side="left")

        tk.Label(
            header,
            text="·  Explorador & Organizador con API Libre",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["card"]
        ).pack(side="left", padx=10)

        # 2. CONTENEDOR DIVIDIDO EN 2 PANELES (IZQUIERDA Y DERECHA)
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=15, pady=10)

        left_frame = tk.Frame(main_paned, bg=self.colors["card"], padx=15, pady=15)
        main_paned.add(left_frame, weight=1)

        right_frame = tk.Frame(main_paned, bg=self.colors["card"], padx=15, pady=15)
        main_paned.add(right_frame, weight=1)

        # Construcción de los contenidos de cada panel
        self._crear_panel_izquierdo(left_frame)
        self._crear_panel_derecho(right_frame)

        # 3. BARRA DE ESTADO INFERIOR
        self._crear_barra_estado()

    def _crear_panel_izquierdo(self, parent: tk.Widget) -> None:
        """
        Construye el panel de búsqueda y catálogo de pistas de Deezer.
        """
        tk.Label(
            parent,
            text="1. Buscar en Deezer",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card"]
        ).pack(anchor="w")

        # Barra de entrada de búsqueda
        search_box = tk.Frame(parent, bg=self.colors["card"], pady=8)
        search_box.pack(fill="x")

        self.entry_busqueda = tk.Entry(
            search_box,
            font=("Segoe UI", 10),
            bg=self.colors["bg"],
            fg=self.colors["text"],
            insertbackground="#fff",
            relief="flat",
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
        self.entry_busqueda.insert(0, "Daft Punk")
        self.entry_busqueda.bind("<Return>", lambda e: self.ejecutar_busqueda())

        # Selector de modalidad de búsqueda
        self.tipo_busqueda = tk.StringVar(value="Top 10 Artista")
        combo = ttk.Combobox(
            search_box,
            textvariable=self.tipo_busqueda,
            values=["Top 10 Artista", "Top 25 Artista", "Buscar Canciones"],
            state="readonly",
            width=14,
            font=("Segoe UI", 9)
        )
        combo.pack(side="left", padx=(0, 8))
        combo.current(0)

        # Botón para ejecutar la búsqueda
        btn_buscar = tk.Button(
            search_box,
            text="🔍 Buscar",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent"],
            fg="#ffffff",
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.ejecutar_busqueda
        )
        btn_buscar.pack(side="left")

        self.lbl_artista_info = tk.Label(
            parent,
            text="Escribe un artista o canción y presiona Buscar.",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["card"]
        )
        self.lbl_artista_info.pack(anchor="w", pady=(2, 6))

        # Tabla (Treeview) con scrollbar para mostrar resultados
        table_frame = tk.Frame(parent, bg=self.colors["card"])
        table_frame.pack(fill="both", expand=True)

        cols = ("num", "titulo", "album", "duracion", "rank")
        self.tree_resultados = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.tree_resultados.heading("num", text="#")
        self.tree_resultados.heading("titulo", text="Título")
        self.tree_resultados.heading("album", text="Álbum")
        self.tree_resultados.heading("duracion", text="Duración")
        self.tree_resultados.heading("rank", text="Popularidad")

        self.tree_resultados.column("num", width=35, anchor="center")
        self.tree_resultados.column("titulo", width=180, anchor="w")
        self.tree_resultados.column("album", width=140, anchor="w")
        self.tree_resultados.column("duracion", width=65, anchor="center")
        self.tree_resultados.column("rank", width=80, anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_resultados.yview)
        self.tree_resultados.configure(yscrollcommand=scroll_y.set)
        self.tree_resultados.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Doble clic en una fila agrega directamente la canción a la playlist
        self.tree_resultados.bind("<Double-1>", lambda e: self.agregar_cancion_seleccionada())

        # Botones de acción sobre los resultados
        btn_box = tk.Frame(parent, bg=self.colors["card"], pady=10)
        btn_box.pack(fill="x")

        btn_add = tk.Button(
            btn_box,
            text="➕ Agregar a Mi Playlist",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["secondary"],
            fg="#ffffff",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.agregar_cancion_seleccionada
        )
        btn_add.pack(side="left", padx=(0, 6))

        btn_add_all = tk.Button(
            btn_box,
            text="➕ Agregar Todas",
            font=("Segoe UI", 9),
            bg=self.colors["card_light"],
            fg=self.colors["text"],
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.agregar_todas_las_canciones
        )
        btn_add_all.pack(side="left", padx=(0, 6))

        btn_preview = tk.Button(
            btn_box,
            text="▶ Preview 30s",
            font=("Segoe UI", 9),
            bg=self.colors["card_light"],
            fg=self.colors["text"],
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.escuchar_preview_seleccionada
        )
        btn_preview.pack(side="left")

    def _crear_panel_derecho(self, parent: tk.Widget) -> None:
        """
        Construye el panel de la playlist del usuario: tabla, herramientas de ordenación y exportación.
        """
        top_bar = tk.Frame(parent, bg=self.colors["card"])
        top_bar.pack(fill="x")

        tk.Label(
            top_bar,
            text="2. Mi Lista de Reproducción",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card"]
        ).pack(side="left")

        # Etiqueta que muestra en tiempo real la cantidad de canciones y duración acumulada
        self.lbl_stats = tk.Label(
            top_bar,
            text="0 canciones · 00:00",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["card"]
        )
        self.lbl_stats.pack(side="right")

        tk.Label(
            parent,
            text="Usa los botones para reordenar o cambiar el orden de las pistas.",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["card"]
        ).pack(anchor="w", pady=(2, 8))

        # Tabla de Playlist del usuario
        table_frame = tk.Frame(parent, bg=self.colors["card"])
        table_frame.pack(fill="both", expand=True)

        cols = ("num", "titulo", "artista", "album", "duracion")
        self.tree_playlist = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.tree_playlist.heading("num", text="#")
        self.tree_playlist.heading("titulo", text="Título")
        self.tree_playlist.heading("artista", text="Artista")
        self.tree_playlist.heading("album", text="Álbum")
        self.tree_playlist.heading("duracion", text="Duración")

        self.tree_playlist.column("num", width=35, anchor="center")
        self.tree_playlist.column("titulo", width=160, anchor="w")
        self.tree_playlist.column("artista", width=120, anchor="w")
        self.tree_playlist.column("album", width=130, anchor="w")
        self.tree_playlist.column("duracion", width=65, anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_playlist.yview)
        self.tree_playlist.configure(yscrollcommand=scroll_y.set)
        self.tree_playlist.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Herramientas de Organización manual y automática
        tools_frame = tk.Frame(parent, bg=self.colors["card"], pady=8)
        tools_frame.pack(fill="x")

        btn_up = tk.Button(
            tools_frame,
            text="▲ Subir",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card_light"],
            fg=self.colors["text"],
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.mover_arriba
        )
        btn_up.pack(side="left", padx=(0, 5))

        btn_down = tk.Button(
            tools_frame,
            text="▼ Bajar",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card_light"],
            fg=self.colors["text"],
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.mover_abajo
        )
        btn_down.pack(side="left", padx=(0, 5))

        btn_del = tk.Button(
            tools_frame,
            text="🗑 Eliminar",
            font=("Segoe UI", 9),
            bg=self.colors["card_light"],
            fg="#ef4444",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.eliminar_cancion
        )
        btn_del.pack(side="left", padx=(0, 5))

        btn_clear = tk.Button(
            tools_frame,
            text="Limpiar",
            font=("Segoe UI", 9),
            bg=self.colors["card_light"],
            fg=self.colors["text_muted"],
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.limpiar_playlist
        )
        btn_clear.pack(side="left", padx=(0, 10))

        # Menú desplegable para ordenar automáticamente por criterio
        self.orden_var = tk.StringVar(value="Título")
        combo_orden = ttk.Combobox(
            tools_frame,
            textvariable=self.orden_var,
            values=["Título (A-Z)", "Artista (A-Z)", "Duración (Menor)", "Duración (Mayor)", "Popularidad"],
            state="readonly",
            width=14,
            font=("Segoe UI", 8)
        )
        combo_orden.pack(side="left", padx=4)
        combo_orden.bind("<<ComboboxSelected>>", lambda e: self.ordenar_playlist())

        # Controles de Guardar / Cargar y Exportar
        export_frame = tk.Frame(parent, bg=self.colors["card"], pady=4)
        export_frame.pack(fill="x")

        btn_save_json = tk.Button(
            export_frame,
            text="💾 Guardar (.json)",
            font=("Segoe UI", 9),
            bg=self.colors["card_light"],
            fg=self.colors["text"],
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.guardar_playlist_json
        )
        btn_save_json.pack(side="left", padx=(0, 5))

        btn_load_json = tk.Button(
            export_frame,
            text="📂 Cargar (.json)",
            font=("Segoe UI", 9),
            bg=self.colors["card_light"],
            fg=self.colors["text"],
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.cargar_playlist_json
        )
        btn_load_json.pack(side="left", padx=(0, 5))

        btn_export_m3u = tk.Button(
            export_frame,
            text="🎵 Exportar M3U (VLC)",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent"],
            fg="#ffffff",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.exportar_m3u
        )
        btn_export_m3u.pack(side="right")

    def _crear_barra_estado(self) -> None:
        """
        Crea la barra inferior para mostrar avisos de progreso, mensajes de éxito o errores.
        """
        status_bar = tk.Frame(self, bg=self.colors["card_light"], height=28, padx=15)
        status_bar.pack(fill="x", side="bottom")

        self.lbl_status = tk.Label(
            status_bar,
            text="Listo.",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["card_light"]
        )
        self.lbl_status.pack(side="left")

    def ejecutar_busqueda(self) -> None:
        """
        Inicia el proceso de búsqueda en Deezer disparando un hilo en segundo plano (daemon thread).

        ¿POR QUÉ LO HACE?
        - Si la llamada HTTP se realizara en el hilo principal de Tkinter, la interfaz se congelaría
          temporalmente mientras espera la respuesta de red. Al usar un hilo secundario, la UI se mantiene fluida.
        """
        query = self.entry_busqueda.get().strip()
        if not query:
            return
        tipo = self.tipo_busqueda.get()
        self.lbl_status.config(text=f"Buscando '{query}' en Deezer...")
        threading.Thread(target=self._hilo_busqueda, args=(query, tipo), daemon=True).start()

    def _hilo_busqueda(self, query: str, tipo: str) -> None:
        """
        Método ejecutado en hilo secundario para consultar la API de Deezer sin bloquear la ventana.
        """
        try:
            if "Artista" in tipo:
                limite = 25 if "25" in tipo else 10
                artista, formateadas = DeezerAPI.buscar_top_artista_formateado(query, limit=limite)

                if artista is None:
                    # Encolamos la actualización visual en el hilo de Tkinter con .after()
                    self.after(0, lambda: self.lbl_status.config(text=f"No se encontró al artista '{query}'"))
                    return

                info = f"Artista: {artista.get('name', query)} · Top {len(formateadas)} canciones"
            else:
                formateadas = DeezerAPI.buscar_canciones_formateadas(query, limit=25)
                info = f"Resultados para '{query}': {len(formateadas)} encontradas"

            # Enviar actualización segura al hilo principal
            self.after(0, lambda: self._actualizar_resultados(formateadas, info))
        except Exception as e:
            self.after(0, lambda error=e: self.lbl_status.config(text=f"Error en la búsqueda: {error}"))

    def _actualizar_resultados(self, canciones: List[Dict[str, Any]], info: str) -> None:
        """
        Actualiza el árbol visual de resultados con las canciones obtenidas de la búsqueda.
        """
        self.resultados_busqueda = canciones
        self.lbl_artista_info.config(text=info)

        # Limpiar registros anteriores de la tabla
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)

        # Insertar los nuevos elementos
        for i, track in enumerate(canciones, 1):
            dur_min = track.get("duration", 0) // 60
            dur_seg = track.get("duration", 0) % 60
            dur_str = f"{dur_min}:{dur_seg:02d}"
            self.tree_resultados.insert(
                "",
                "end",
                iid=str(i - 1),
                values=(i, track.get("title", ""), track.get("album", ""), dur_str, f"{track.get('rank', 0):,}")
            )

        self.lbl_status.config(text=f"Cargadas {len(canciones)} pistas.")

    def agregar_cancion_seleccionada(self) -> None:
        """
        Agrega la canción seleccionada en la tabla de búsqueda hacia la lista de reproducción activa.
        """
        sel = self.tree_resultados.selection()
        if not sel:
            return
        idx = int(sel[0])
        agregar_canciones(self.playlist, [self.resultados_busqueda[idx]])
        self._refrescar_playlist()

    def agregar_todas_las_canciones(self) -> None:
        """
        Agrega todas las canciones encontradas en la búsqueda actual hacia la lista de reproducción.
        """
        if not self.resultados_busqueda:
            return
        agregar_canciones(self.playlist, self.resultados_busqueda)
        self._refrescar_playlist()

    def mover_arriba(self) -> None:
        """
        Desplaza la canción seleccionada en la playlist una posición hacia arriba.
        """
        sel = self.tree_playlist.selection()
        if not sel:
            return
        idx = int(sel[0])
        nuevo_indice = mover_cancion(self.playlist, idx, -1)
        self._refrescar_playlist()
        self.tree_playlist.selection_set(str(nuevo_indice))

    def mover_abajo(self) -> None:
        """
        Desplaza la canción seleccionada en la playlist una posición hacia abajo.
        """
        sel = self.tree_playlist.selection()
        if not sel:
            return
        idx = int(sel[0])
        nuevo_indice = mover_cancion(self.playlist, idx, 1)
        self._refrescar_playlist()
        self.tree_playlist.selection_set(str(nuevo_indice))

    def eliminar_cancion(self) -> None:
        """
        Elimina la pista seleccionada de la playlist del usuario.
        """
        sel = self.tree_playlist.selection()
        if not sel:
            return
        idx = int(sel[0])
        quitar_cancion(self.playlist, idx)
        self._refrescar_playlist()

    def limpiar_playlist(self) -> None:
        """
        Vacía completamente la lista de reproducción activa.
        """
        if not self.playlist:
            return
        limpiar_lista(self.playlist)
        self._refrescar_playlist()

    def ordenar_playlist(self) -> None:
        """
        Ordena la playlist actual según el criterio seleccionado en el Combobox.
        """
        criterio = self.orden_var.get()
        if not self.playlist:
            return
        self.playlist = ordenar_canciones(self.playlist, criterio)
        self._refrescar_playlist()

    def _refrescar_playlist(self) -> None:
        """
        Repinta la tabla de la playlist y actualiza la sumatoria de duración y pistas.

        ¿POR QUÉ LO HACE?
        - Asegura que la vista refleje con precisión cualquier cambio en la lista (altas, bajas, orden)
          y formatea la sumatoria de duración en un formato legible (ej. 35:20 o 1:12:45).
        """
        for item in self.tree_playlist.get_children():
            self.tree_playlist.delete(item)

        for i, track in enumerate(self.playlist, 1):
            dur_min = track.get("duration", 0) // 60
            dur_seg = track.get("duration", 0) % 60
            dur_str = f"{dur_min}:{dur_seg:02d}"
            self.tree_playlist.insert(
                "",
                "end",
                iid=str(i - 1),
                values=(i, track.get("title", ""), track.get("artist", ""), track.get("album", ""), dur_str)
            )

        # Cálculo y formateo de la duración acumulada
        total_seg = calcular_duracion_total(self.playlist)
        duracion_fmt = str(timedelta(seconds=total_seg))
        # Si la duración es menor a 10 horas, timedelta devuelve 0:MM:SS; simplificamos para mostrar MM:SS
        if duracion_fmt.startswith("0:"):
            duracion_fmt = duracion_fmt[2:]

        self.lbl_stats.config(text=f"{len(self.playlist)} canciones · {duracion_fmt}")

    def escuchar_preview_seleccionada(self) -> None:
        """
        Abre en el navegador predeterminado el enlace de audio preliminar (preview de 30s) de la canción seleccionada.

        ¿POR QUÉ LO HACE?
        - Permite al usuario verificar y escuchar un fragmento de la canción antes de decidir incluirla o conservarla.
        """
        sel = self.tree_resultados.selection() or self.tree_playlist.selection()
        if not sel:
            return
        idx = int(sel[0])
        lista = self.resultados_busqueda if self.tree_resultados.selection() else self.playlist
        preview_url = lista[idx].get("preview")
        if preview_url:
            webbrowser.open(preview_url)
        else:
            messagebox.showinfo("Preview", "Deezer no cuenta con muestra de audio para esta pista.")

    def exportar_m3u(self) -> None:
        """
        Abre un cuadro de diálogo de guardado y exporta la playlist en formato de archivo M3U para reproductores como VLC.
        """
        if not self.playlist:
            messagebox.showwarning("Atención", "La lista de reproducción está vacía.")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".m3u",
            filetypes=[("M3U Playlist", "*.m3u"), ("Todos los archivos", "*.*")]
        )
        if not archivo:
            return

        try:
            exportar_playlist_m3u(archivo, self.playlist)
            messagebox.showinfo("Éxito", "Playlist exportada correctamente como M3U para VLC/Media Player.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el archivo M3U: {e}")

    def guardar_playlist_json(self) -> None:
        """
        Abre un cuadro de diálogo de guardado y persiste la lista de canciones en formato JSON estructurado.
        """
        if not self.playlist:
            messagebox.showwarning("Atención", "La lista de reproducción está vacía.")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if not archivo:
            return

        try:
            guardar_playlist_json(archivo, self.playlist)
            messagebox.showinfo("Éxito", "Lista guardada correctamente en formato JSON.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo JSON: {e}")

    def cargar_playlist_json(self) -> None:
        """
        Abre un cuadro de diálogo para cargar una playlist guardada en formato JSON y la despliega en la interfaz.
        """
        archivo = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if not archivo:
            return

        try:
            self.playlist = cargar_playlist_json(archivo)
            self._refrescar_playlist()
            self.lbl_status.config(text=f"Lista cargada exitosamente desde '{os.path.basename(archivo)}'.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la playlist: {e}")
