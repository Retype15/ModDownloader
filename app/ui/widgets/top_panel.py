from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import pyqtSignal

class TopPanelWidget(QWidget):
    """Panel superior que contiene el selector de juego y botones de acción."""
    game_changed_signal = pyqtSignal(str)
    add_game_signal = pyqtSignal()
    open_workshop_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("<b>Juego Actual:</b>"))
        self.game_selector_combo = QComboBox()
        self.game_selector_combo.setMinimumWidth(300)
        self.game_selector_combo.currentIndexChanged.connect(self._on_game_selected)
        layout.addWidget(self.game_selector_combo)
        
        self.add_game_button = QPushButton("+")
        self.add_game_button.setToolTip("Añadir nuevo juego")
        self.add_game_button.setFixedSize(30, 30)
        self.add_game_button.clicked.connect(self.add_game_signal.emit)
        layout.addWidget(self.add_game_button)

        self.open_workshop_button = QPushButton("Abrir Workshop")
        self.open_workshop_button.setToolTip("Abrir la workshop del juego en una nueva ventana")
        self.open_workshop_button.clicked.connect(self.open_workshop_signal.emit)
        layout.addWidget(self.open_workshop_button)

        layout.addStretch()

    def _on_game_selected(self, index):
        app_id = self.game_selector_combo.itemData(index)
        if app_id:
            self.game_changed_signal.emit(app_id)

    def populate(self, games_data: list[dict]):
        self.game_selector_combo.blockSignals(True)
        self.game_selector_combo.clear()
        if not games_data:
            self.game_selector_combo.addItem("No hay juegos gestionados")
            self.game_selector_combo.setEnabled(False)
        else:
            self.game_selector_combo.setEnabled(True)
            for game in games_data:
                self.game_selector_combo.addItem(f"{game['name']} [{game['app_id']}]", userData=game['app_id'])
        self.game_selector_combo.blockSignals(False)
        # Emitir la señal para el primer juego si existe
        if games_data:
            self._on_game_selected(0)