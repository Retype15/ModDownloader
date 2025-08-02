from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QFileDialog, QMessageBox)

class AddGameDialog(QDialog):
    """Diálogo para añadir un nuevo juego manualmente."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Nuevo Juego")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.game_info = {}

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.app_id_edit = QLineEdit()
        self.app_id_edit.setPlaceholderText("Ej: 294100")
        form_layout.addRow("AppID de Steam:", self.app_id_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: RimWorld")
        form_layout.addRow("Nombre del Juego:", self.name_edit)

        self.mods_path_edit = QLineEdit()
        browse_button = QPushButton("Explorar...")
        browse_button.clicked.connect(self.browse_mods_folder)
        
        mods_path_layout = QVBoxLayout()
        mods_path_layout.addWidget(self.mods_path_edit)
        mods_path_layout.addWidget(browse_button)
        form_layout.addRow("Ruta de instalación de Mods:", mods_path_layout)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def browse_mods_folder(self):
        """Abre un diálogo para seleccionar la carpeta de mods del juego."""
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Mods")
        if dir_path:
            self.mods_path_edit.setText(dir_path.replace("/", "\\"))

    def accept(self):
        """Valida los datos y los prepara para ser recuperados."""
        app_id = self.app_id_edit.text().strip()
        name = self.name_edit.text().strip()
        mods_path = self.mods_path_edit.text().strip()

        if not all([app_id, name, mods_path]):
            QMessageBox.warning(self, "Datos incompletos", "Todos los campos son obligatorios.")
            return
            
        if not app_id.isdigit():
            QMessageBox.warning(self, "Dato inválido", "El AppID debe ser un número.")
            return

        self.game_info = {
            "app_id": app_id,
            "name": name,
            "mod_install_path": mods_path
        }
        super().accept()