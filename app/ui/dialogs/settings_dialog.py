#app/ui/dialogs/settings_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QDialogButtonBox, QFileDialog, QHBoxLayout)
from app.core.config_manager import config_manager

class SettingsDialog(QDialog):
    """Diálogo para configurar los ajustes globales de la aplicación."""
    def __init__(self, parent=None): # CORREGIDO: __init__
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Campo para la ruta de SteamCMD
        steamcmd_layout = QHBoxLayout()
        self.steamcmd_path_edit = QLineEdit()
        browse_button = QPushButton("...")
        browse_button.setFixedWidth(30)
        browse_button.clicked.connect(self.browse_steamcmd)
        steamcmd_layout.addWidget(self.steamcmd_path_edit)
        steamcmd_layout.addWidget(browse_button)
        form_layout.addRow("Ruta de steamcmd.exe:", steamcmd_layout)

        # Campo para la clave de API de Steam
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Opcional, pero necesario para buscar actualizaciones")
        form_layout.addRow("Clave de API de Steam:", self.api_key_edit)
        layout.addLayout(form_layout)

        # Botones de Aceptar y Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.load_settings()

    def browse_steamcmd(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar steamcmd.exe", "", "Ejecutables (*.exe);;Todos los archivos (*)")
        if filepath:
            self.steamcmd_path_edit.setText(filepath.replace("/", "\\"))

    def load_settings(self):
        self.steamcmd_path_edit.setText(config_manager.get("Paths", "steamcmd_path", fallback=""))
        self.api_key_edit.setText(config_manager.get("API", "steam_api_key", fallback=""))

    def accept(self):
        config_manager.set("Paths", "steamcmd_path", self.steamcmd_path_edit.text())
        config_manager.set("API", "steam_api_key", self.api_key_edit.text())
        config_manager.save()
        super().accept()