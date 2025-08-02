from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSlot

class ConsoleDialog(QDialog):
    """
    Un diálogo que simula una consola para mostrar la salida en vivo de un proceso
    como SteamCMD.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Salida de SteamCMD")
        self.setMinimumSize(800, 600)

        self.full_log = ""
        
        layout = QVBoxLayout(self)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc; font-family: Consolas, 'Courier New', monospace;")
        layout.addWidget(self.log_output)

        button_layout = QHBoxLayout()
        self.clear_button = QPushButton("Limpiar Log")
        self.clear_button.clicked.connect(self.log_output.clear)
        self.cancel_button = QPushButton("Cancelar Tarea")
        
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    @pyqtSlot(str)
    def append_log(self, text: str):
        """Añade una línea de texto al log y guarda el log completo."""
        self.full_log += text
        self.log_output.append(text.strip())
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def closeEvent(self, event):
        """Evita que el usuario cierre la ventana mientras el proceso se está ejecutando."""
        if self.cancel_button.isEnabled():
            # Idealmente, aquí se pediría confirmación
            event.ignore()
        else:
            event.accept()