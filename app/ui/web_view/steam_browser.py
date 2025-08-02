#app/ui/web_view/steam_browser.py
from PyQt6.QtCore import QUrl, QObject
from PyQt6.QtWebEngineCore import QWebEngineScript
from PyQt6.QtWebEngineWidgets import QWebEngineView
from pathlib import Path

class SteamBrowser(QWebEngineView):
    """
    Widget del navegador que inyecta el script del lado del cliente.
    Usa un WorldId explícito y rutas absolutas para máxima compatibilidad.
    """
    def __init__(self, parent: QObject | None = None, server_port: int = 0):
        super().__init__(parent)
        self.server_port = server_port
        self._prepare_and_inject_injector_script()

    def _prepare_and_inject_injector_script(self):
        """
        Lee el script injector.js y lo inyecta en la página, pasando el puerto del servidor.
        """
        try:
            # Construir rutas absolutas para máxima fiabilidad
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            injector_path = project_root / "assets" / "js" / "injector.js"

            if not injector_path.exists():
                print(f"ADVERTENCIA: No se encontró '{injector_path}'.")
                return

            with open(injector_path, 'r', encoding='utf-8') as f:
                injector_source = f.read()

            # Preparamos el código que define el puerto para que el script JS lo pueda usar
            port_definition_script = f"const MOD_MANAGER_PORT = {self.server_port};\n"
            
            # Combinamos la definición del puerto con el resto del script
            combined_source = port_definition_script + injector_source

            # Crear el objeto de script
            script = QWebEngineScript()
            script.setSourceCode(combined_source)
            script.setName("ModManagerInjector")
            
            # --- LA CORRECCIÓN CRÍTICA Y DEFINITIVA ---
            # Reemplazamos la referencia al enum 'QWebEngineScript.WorldId.MainWorld'
            # con su valor entero subyacente '0'. Esto es compatible con todas las versiones
            # de PyQt6 que soportan esta funcionalidad y resuelve el AttributeError.
            # Volvemos a MainWorld porque ya no usamos QWebChannel y la nueva comunicación
            # vía servidor local no contamina el entorno de la página.
            script.setWorldId(0) # 0 = MainWorld
            
            script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
            
            self.page().scripts().insert(script)
            
            print(f"INFO: Inyector configurado para usar el puerto {self.server_port} e inyectado correctamente.")

        except Exception as e:
            # Imprimir la traza completa del error para una depuración más fácil
            import traceback
            print(f"ERROR al preparar/inyectar injector.js: {e}")
            traceback.print_exc()