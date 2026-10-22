"""
Punto de entrada principal para la aplicación Deezer Playlist Organizer.

¿QUÉ HACE ESTE ARCHIVO?
- Inicia el ciclo principal de la interfaz gráfica de usuario (GUI) desarrollada con Tkinter.

¿POR QUÉ LO HACE?
- Sirve como archivo ejecutable raíz del proyecto (tanto para desarrollo con 'python deezer_organizer.py'
  como para empaquetado con PyInstaller). Mantiene el punto de arranque desacoplado
  de la implementación detallada de los componentes visuales y la lógica de negocio.
"""

from ui.main_window import DeezerApp

if __name__ == "__main__":
    # Instanciamos la ventana principal de la aplicación
    app = DeezerApp()
    
    # Iniciamos el bucle de eventos de la interfaz gráfica (escucha clics, pulsaciones de teclas, etc.)
    app.mainloop()
