#app/core/steam_handler.py
import subprocess
import re
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable

class SteamCMDWorkerSignals(QObject):
    """Clase separada que hereda de QObject para poder definir y emitir señales."""
    output = pyqtSignal(str)      # Emite cada línea de la salida de la consola
    finished = pyqtSignal(str)    # Emite el log completo cuando el proceso termina
    error = pyqtSignal(str)       # Emite mensajes de error críticos

class SteamCMDWorker(QRunnable):
    """
    Ejecuta el proceso de SteamCMD en un hilo separado para no bloquear la UI,
    emitiendo la salida de la consola en tiempo real.
    """
    def __init__(self, steamcmd_path: str, script_path: str):
        super().__init__()
        
        # --- LÍNEA CRÍTICA AÑADIDA ---
        # Aquí creamos una instancia del objeto de señales. Esto crea el atributo
        # 'signals' que estaba faltando y causaba el AttributeError.
        self.signals = SteamCMDWorkerSignals()
        
        self.steamcmd_path = steamcmd_path
        # Convertir la ruta del script a una ruta absoluta para evitar problemas
        # de directorio de trabajo con SteamCMD.
        self.script_path = str(Path(script_path).resolve())
        self.process = None

    def run(self):
        """El método principal que se ejecuta en el hilo del QThreadPool."""
        if not Path(self.steamcmd_path).exists():
            self.signals.error.emit(f"Error: La ruta de SteamCMD no es válida: '{self.steamcmd_path}'")
            return

        if not Path(self.script_path).exists():
            self.signals.error.emit(f"Error: El archivo de script no se encuentra: '{self.script_path}'")
            return

        command = [
            self.steamcmd_path,
            "+runscript", self.script_path
        ]
        
        try:
            # Iniciar el proceso de SteamCMD
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Redirigir errores al stream de salida estándar
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) # Seguro para Windows y otros SO
            )

            full_output = ""
            # Leer la salida línea por línea en tiempo real mientras el proceso se ejecuta
            for line in iter(self.process.stdout.readline, ''):
                self.signals.output.emit(line) # Emitir cada línea a la consola de la UI
                full_output += line
            
            # Esperar a que el proceso termine
            self.process.wait()
            # Emitir la señal de finalización con el log completo
            self.signals.finished.emit(full_output)

        except FileNotFoundError:
            self.signals.error.emit("Error: No se encontró el ejecutable de SteamCMD en la ruta especificada.")
        except Exception as e:
            self.signals.error.emit(f"Ocurrió una excepción inesperada al ejecutar SteamCMD: {e}")
            
    def cancel(self):
        """Permite cancelar el proceso de SteamCMD desde la UI."""
        if self.process and self.process.poll() is None: # Si el proceso existe y sigue en ejecución
            self.process.terminate()
            self.signals.output.emit("\n\n--- TAREA CANCELADA POR EL USUARIO ---\n")