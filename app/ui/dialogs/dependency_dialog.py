from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget, 
                             QDialogButtonBox, QListWidgetItem)
from PyQt6.QtCore import Qt

class DependencyDialog(QDialog):
    """
    Diálogo que muestra las dependencias de mods que faltan y permite
    al usuario seleccionarlas para añadirlas a la cola de descarga.
    """
    def __init__(self, missing_deps: dict[str, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dependencias Faltantes Encontradas")
        self.setMinimumWidth(500)
        
        self.selected_deps = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Se encontraron las siguientes dependencias que no están ni instaladas ni en la cola de descarga.\n"
            "Por favor, selecciona las que deseas añadir:"
        ))

        self.deps_list_widget = QListWidget()
        for workshop_id, name in missing_deps.items():
            item = QListWidgetItem(f"{name} (ID: {workshop_id})")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked) # Marcadas por defecto
            item.setData(Qt.ItemDataRole.UserRole, workshop_id) # Guardar ID
            self.deps_list_widget.addItem(item)
        
        layout.addWidget(self.deps_list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        """Recopila las dependencias seleccionadas por el usuario."""
        for i in range(self.deps_list_widget.count()):
            item = self.deps_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                workshop_id = item.data(Qt.ItemDataRole.UserRole)
                name = item.text().split(' (ID:')[0]
                self.selected_deps.append({'workshop_id': workshop_id, 'name': name})
        super().accept()