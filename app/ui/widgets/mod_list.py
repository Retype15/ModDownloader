from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout, QListWidgetItem, QMenu
from PyQt6.QtCore import pyqtSignal, Qt, QPoint

class ModListWidget(QWidget):
    """Panel derecho que contiene las listas de mods y el botón de descarga."""
    mod_selected_signal = pyqtSignal(str)
    download_mods_signal = pyqtSignal(list)
    remove_pending_mod_signal = pyqtSignal(str)
    remove_installed_mod_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(QLabel("<b>Mods Instalados</b> (Clic derecho para opciones)"))
        self.installed_mods_list = QListWidget()
        self.installed_mods_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.installed_mods_list.customContextMenuRequested.connect(self._show_installed_mod_context_menu)
        self.installed_mods_list.currentItemChanged.connect(self._on_mod_selected)
        layout.addWidget(self.installed_mods_list)
        
        layout.addWidget(QLabel("<b>Mods Pendientes</b> (Marca los que quieres descargar)"))
        self.pending_mods_list = QListWidget()
        self.pending_mods_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pending_mods_list.customContextMenuRequested.connect(self._show_pending_mod_context_menu)
        self.pending_mods_list.currentItemChanged.connect(self._on_mod_selected)
        layout.addWidget(self.pending_mods_list)
        
        self.download_button = QPushButton("Descargar Mods Marcados")
        self.download_button.clicked.connect(self._on_download_clicked)
        layout.addWidget(self.download_button)

    @pyqtSlot(list)
    def update_lists(self, all_mods: list[dict]):
        self.installed_mods_list.clear()
        self.pending_mods_list.clear()
        for mod in sorted(all_mods, key=lambda x: x.get('name', '').lower()):
            item = QListWidgetItem(f"{mod.get('name', 'N/A')} (ID: {mod.get('workshop_id', 'N/A')})")
            item.setData(Qt.ItemDataRole.UserRole, mod.get('workshop_id'))
            if mod.get('status') == 'installed':
                self.installed_mods_list.addItem(item)
            elif mod.get('status') == 'pending':
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                self.pending_mods_list.addItem(item)
    
    def _on_mod_selected(self, current_item, previous_item=None):
        if current_item:
            workshop_id = current_item.data(Qt.ItemDataRole.UserRole)
            if workshop_id:
                self.mod_selected_signal.emit(workshop_id)

    def _on_download_clicked(self):
        mods_to_download = []
        for i in range(self.pending_mods_list.count()):
            item = self.pending_mods_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                mods_to_download.append({
                    'workshop_id': item.data(Qt.ItemDataRole.UserRole),
                    'name': item.text().split(" (ID:")[0]
                })
        self.download_mods_signal.emit(mods_to_download)

    def _show_pending_mod_context_menu(self, pos: QPoint):
        item = self.pending_mods_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            remove_action = menu.addAction("Quitar de Pendientes")
            workshop_id = item.data(Qt.ItemDataRole.UserRole)
            remove_action.triggered.connect(lambda: self.remove_pending_mod_signal.emit(workshop_id))
            menu.exec(self.pending_mods_list.mapToGlobal(pos))

    def _show_installed_mod_context_menu(self, pos: QPoint):
        item = self.installed_mods_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            remove_action = menu.addAction("Eliminar Mod")
            workshop_id = item.data(Qt.ItemDataRole.UserRole)
            remove_action.triggered.connect(lambda: self.remove_installed_mod_signal.emit(workshop_id))
            menu.exec(self.installed_mods_list.mapToGlobal(pos))