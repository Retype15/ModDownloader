from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QSplitter,
                             QToolBar, QMessageBox, QListWidgetItem)
from PyQt6.QtCore import pyqtSignal, QUrl, Qt
from PyQt6.QtGui import QAction, QIcon
from app.core.local_server import ServerThread, LocalServerSignals, SERVER_PORT
from .web_view.steam_browser import SteamBrowser

class BrowserWindow(QMainWindow):
    """
    Ventana de sesión que combina una barra de herramientas nativa inteligente
    con la inyección de botones en las listas de mods.
    """
    confirm_mods_signal = pyqtSignal(list)
    download_mods_signal = pyqtSignal(list)

    def __init__(self, url: str, managed_mod_ids: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Mods desde Steam Workshop")
        self.setGeometry(150, 150, 1280, 800)

        self.staged_mods = {}
        self.managed_mod_ids = managed_mod_ids
        self.parent_window = parent # Guardar referencia a MainWindow

        self.server_signals = LocalServerSignals()
        self.server_thread = ServerThread(self.server_signals, self.staged_mods, self.managed_mod_ids)
        self.server_signals.mod_received.connect(self._add_mod_to_stage)
        self.server_signals.mod_removed.connect(self._remove_mod_from_stage)
        self.server_thread.start()

        self._setup_ui(url)
        self._create_toolbar()
        
    def _setup_ui(self, url):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_splitter = QSplitter()
        main_layout.addWidget(main_splitter)

        self.browser = SteamBrowser(self, server_port=SERVER_PORT) 
        self.browser.load(QUrl(url))
        main_splitter.addWidget(self.browser)

        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)
        side_panel.setMinimumWidth(300)
        side_panel.setMaximumWidth(450)
        side_layout.addWidget(QLabel("<b>Mods para Añadir (Carrito):</b>"))
        self.staged_list_widget = QListWidget()
        side_layout.addWidget(self.staged_list_widget)
        button_layout = QVBoxLayout()
        confirm_button = QPushButton("Confirmar y Cerrar")
        confirm_button.clicked.connect(self._confirm_and_close)
        download_button = QPushButton("Descargar Directamente")
        download_button.setStyleSheet("background-color: #28a745; color: white;")
        download_button.clicked.connect(self._download_and_close)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(download_button)
        side_layout.addLayout(button_layout)
        
        main_splitter.addWidget(side_panel)
        main_splitter.setSizes([900, 380])

    def _create_toolbar(self):
        toolbar = QToolBar("Navegación")
        self.addToolBar(toolbar)

        back_action = QAction(QIcon.fromTheme("go-previous"), "Atrás", self)
        back_action.triggered.connect(self.browser.back)
        toolbar.addAction(back_action)

        forward_action = QAction(QIcon.fromTheme("go-next"), "Adelante", self)
        forward_action.triggered.connect(self.browser.forward)
        toolbar.addAction(forward_action)

        reload_action = QAction(QIcon.fromTheme("view-refresh"), "Recargar", self)
        reload_action.triggered.connect(self.browser.reload)
        toolbar.addAction(reload_action)

        toolbar.addSeparator()

        self.add_current_mod_action = QAction(QIcon.fromTheme("add"), "Añadir Mod de esta Página", self)
        self.add_current_mod_action.triggered.connect(self._add_current_page_mod)
        toolbar.addAction(self.add_current_mod_action)

        self.browser.urlChanged.connect(self._update_toolbar_state)
        # Conectar el cambio en el carrito para actualizar el botón de la toolbar
        self.server_signals.mod_received.connect(lambda: self._update_toolbar_state(self.browser.url()))
        self.server_signals.mod_removed.connect(lambda: self._update_toolbar_state(self.browser.url()))
        
        self._update_toolbar_state(self.browser.url())

    def _update_toolbar_state(self, url: QUrl):
        """Habilita, deshabilita y actualiza el texto/icono del botón 'Añadir'."""
        url_string = url.toString()
        if "/sharedfiles/filedetails/?id=" in url_string:
            try:
                workshop_id = url.query(QUrl.ComponentFormattingOption.PrettyDecoded).split('id=')[1].split('&')[0]
                
                if workshop_id in self.managed_mod_ids:
                    self.add_current_mod_action.setEnabled(False)
                    self.add_current_mod_action.setText("✓ Ya Gestionado")
                    self.add_current_mod_action.setIcon(QIcon.fromTheme("emblem-ok"))
                elif workshop_id in self.staged_mods:
                    self.add_current_mod_action.setEnabled(True) # Permitir quitarlo
                    self.add_current_mod_action.setText("Quitar del Carrito")
                    self.add_current_mod_action.setIcon(QIcon.fromTheme("remove"))
                else:
                    self.add_current_mod_action.setEnabled(True)
                    self.add_current_mod_action.setText("Añadir Mod de esta Página")
                    self.add_current_mod_action.setIcon(QIcon.fromTheme("add"))
            except IndexError:
                self.add_current_mod_action.setEnabled(False)
                self.add_current_mod_action.setText("(URL de mod inválida)")
        else:
            self.add_current_mod_action.setEnabled(False)
            self.add_current_mod_action.setText("(Navega a una página de mod)")
            self.add_current_mod_action.setIcon(QIcon.fromTheme("add"))

    def _add_current_page_mod(self):
        """Añade o quita el mod de la página actual del carrito."""
        url = self.browser.url()
        try:
            app_id = self.parent_window.current_app_id
            workshop_id = url.query(QUrl.ComponentFormattingOption.PrettyDecoded).split('id=')[1].split('&')[0]
            mod_name = self.browser.page().title().replace("Steam Workshop::", "").strip()
            
            mod_data = {'appId': app_id, 'workshopId': workshop_id, 'modName': mod_name}

            # Lógica Toggle: si ya está en el carrito, lo quitamos. Si no, lo añadimos.
            if workshop_id in self.staged_mods:
                self._remove_mod_from_stage(mod_data)
            else:
                self._add_mod_to_stage(mod_data)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo procesar la URL actual.\nError: {e}")

    def _add_mod_to_stage(self, mod_data: dict):
        workshop_id = mod_data.get('workshopId')
        if workshop_id and workshop_id not in self.managed_mod_ids and workshop_id not in self.staged_mods:
            self.staged_mods[workshop_id] = mod_data
            item = QListWidgetItem(f"{mod_data.get('modName', 'N/A')} ({workshop_id})")
            item.setData(Qt.ItemDataRole.UserRole, workshop_id)
            self.staged_list_widget.addItem(item)
            
    def _remove_mod_from_stage(self, mod_data: dict):
        workshop_id = mod_data.get('workshopId')
        if workshop_id and workshop_id in self.staged_mods:
            del self.staged_mods[workshop_id]
            for i in range(self.staged_list_widget.count()):
                item = self.staged_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == workshop_id:
                    self.staged_list_widget.takeItem(i)
                    break

    def _confirm_and_close(self):
        self.confirm_mods_signal.emit(list(self.staged_mods.values()))
        self.close()

    def _download_and_close(self):
        self.download_mods_signal.emit(list(self.staged_mods.values()))
        self.close()
        
    def closeEvent(self, event):
        self.server_thread.stop()
        self.server_thread.quit()
        self.server_thread.wait()
        super().closeEvent(event)