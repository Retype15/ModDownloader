import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from app.ui.main_window import MainWindow
from app.core.config_manager import config_manager

def initial_setup_check():
    """Verifica la configuración inicial crítica, como la ruta de SteamCMD."""
    steamcmd_path = config_manager.get("Paths", "steamcmd_path")
    if not steamcmd_path or not os.path.exists(steamcmd_path):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText("SteamCMD no está configurado.")
        msg_box.setInformativeText("La ruta de SteamCMD no está configurada o no es válida. "
                                   "Por favor, configúrala en el menú 'Archivo > Configuración' "
                                   "para poder descargar mods.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        # En una app completa, aquí se abriría directamente el diálogo de configuración.

def main():
    # Crear carpetas necesarias si no existen
    os.makedirs("gamedata", exist_ok=True)
    os.makedirs("assets/js", exist_ok=True)
    
    app = QApplication(sys.argv)
    
    # Aquí iría el código para crear `injector.js` si no existe
    
    window = MainWindow()
    window.show()
    
    # Comprobar configuración después de mostrar la ventana
    app.lastWindowClosed.connect(app.quit) # Asegura que la app se cierra bien
    QApplication.instance().processEvents() # Permite que la ventana se dibuje
    initial_setup_check()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()