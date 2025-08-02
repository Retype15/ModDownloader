import sys
import os
import shutil
import re
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QSplitter,
    QStatusBar, QMessageBox, QLineEdit, QProgressBar,
    QComboBox, QListWidgetItem, QMenu, QTextBrowser,
    QToolBar
)
from PyQt6.QtCore import Qt, pyqtSlot, QUrl, QSize, QThreadPool, QPoint
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest

# Importaciones de módulos del proyecto
from app.core.data_manager import data_manager
from app.core.config_manager import config_manager
from app.core.steam_api_handler import steam_api_handler
from app.core.steam_web_scraper import SteamWebScraper
from app.core.cache_manager import cache_manager
from app.core.steam_handler import SteamCMDWorker
from app.core.dependency_resolver import resolve_dependencies
from app.ui.web_view.steam_browser import SteamBrowser
from app.ui.dialogs.settings_dialog import SettingsDialog
from app.ui.dialogs.add_game_dialog import AddGameDialog
from app.ui.dialogs.dependency_dialog import DependencyDialog
from app.ui.dialogs.console_dialog import ConsoleDialog
from app.ui.web_view.steam_browser import SteamBrowser 
from app.ui.browser_window import BrowserWindow

class WorkshopBrowserWindow(QMainWindow):
    """Ventana independiente para el navegador de la Workshop de Steam."""
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Navegador de Steam Workshop")
        self.setGeometry(150, 150, 1024, 768)
        
        self.browser = SteamBrowser(self)
        self.setCentralWidget(self.browser)
        self.browser.load(QUrl(url))
        
        if parent and hasattr(parent, 'handle_add_mod_from_url'):
            self.browser.modActionRequested.connect(parent.handle_add_mod_from_url)

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación Steam Workshop Mod Manager."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Workshop Mod Manager")
        self.setGeometry(100, 100, 1400, 800)
        self.setMinimumSize(1024, 600)

        # Estado de la aplicación
        self.current_app_id: str | None = None
        self.console_dialog: ConsoleDialog | None = None
        self.steam_cmd_worker: SteamCMDWorker | None = None
        self.browser_window: WorkshopBrowserWindow | None = None

        self.network_manager = QNetworkAccessManager(self)
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(3)

        self._setup_ui()
        self._create_menus()
        self.populate_game_selector()
        self.statusBar().showMessage("Bienvenido. Selecciona un juego o añádelo con el botón '+'.", 5000)

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        top_panel_layout = QHBoxLayout()
        top_panel_layout.addWidget(QLabel("<b>Juego Actual:</b>"))
        self.game_selector_combo = QComboBox()
        self.game_selector_combo.setMinimumWidth(250)
        self.game_selector_combo.currentIndexChanged.connect(self.on_game_selected)
        top_panel_layout.addWidget(self.game_selector_combo)
        
        self.add_game_button = QPushButton("+")
        self.add_game_button.setToolTip("Añadir nuevo juego")
        self.add_game_button.setFixedSize(30, 30)
        self.add_game_button.clicked.connect(self.open_add_game_dialog)
        top_panel_layout.addWidget(self.add_game_button)

        self.open_workshop_button = QPushButton("Abrir Workshop")
        self.open_workshop_button.setToolTip("Abrir la workshop del juego en una nueva ventana")
        self.open_workshop_button.clicked.connect(self.open_workshop_browser)
        top_panel_layout.addWidget(self.open_workshop_button)

        top_panel_layout.addStretch()
        main_layout.addLayout(top_panel_layout)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(5, 5, 5, 5)

        self.mod_title_label = QLabel("Selecciona un mod para ver sus detalles")
        self.mod_title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.mod_title_label.setWordWrap(True)
        preview_layout.addWidget(self.mod_title_label)

        self.mod_banner_label = QLabel()
        self.mod_banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mod_banner_label.setMinimumHeight(200)
        self.mod_banner_label.setStyleSheet("border: 1px solid #555; background-color: #2d2d2d;")
        preview_layout.addWidget(self.mod_banner_label)
        
        self.mod_desc_browser = QTextBrowser()
        self.mod_desc_browser.setReadOnly(True)
        preview_layout.addWidget(self.mod_desc_browser)
        
        preview_layout.addWidget(QLabel("<b>Dependencias (clic en las rojas para añadir):</b>"))
        self.mod_deps_list = QListWidget()
        self.mod_deps_list.setMaximumHeight(100)
        self.mod_deps_list.itemClicked.connect(self.on_dependency_clicked)
        preview_layout.addWidget(self.mod_deps_list)

        main_splitter.addWidget(preview_panel)

        mods_panel = QWidget()
        mods_layout = QVBoxLayout(mods_panel)
        mods_layout.setContentsMargins(5, 5, 5, 5)

        mods_layout.addWidget(QLabel("<b>Mods Instalados</b> (Clic derecho para opciones)"))
        self.installed_mods_list = QListWidget()
        self.installed_mods_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.installed_mods_list.customContextMenuRequested.connect(self.show_installed_mod_context_menu)
        self.installed_mods_list.currentItemChanged.connect(self.on_mod_selected)
        mods_layout.addWidget(self.installed_mods_list)
        
        mods_layout.addWidget(QLabel("<b>Mods Pendientes</b> (Marca los que quieres descargar)"))
        self.pending_mods_list = QListWidget()
        self.pending_mods_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pending_mods_list.customContextMenuRequested.connect(self.show_pending_mod_context_menu)
        self.pending_mods_list.currentItemChanged.connect(self.on_mod_selected)
        mods_layout.addWidget(self.pending_mods_list)
        
        action_layout = QHBoxLayout()
        self.download_button = QPushButton("Descargar Mods Marcados")
        self.download_button.clicked.connect(self.start_download_process)
        self.update_button = QPushButton("Buscar Actualizaciones")
        self.update_button.clicked.connect(self.check_for_updates)
        action_layout.addWidget(self.download_button)
        action_layout.addWidget(self.update_button)
        mods_layout.addLayout(action_layout)

        main_splitter.addWidget(mods_panel)
        main_splitter.setSizes([700, 700])
        self.setStatusBar(QStatusBar(self))

    def _create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Archivo")
        
        settings_action = QAction("Configuración...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def populate_game_selector(self):
        self.game_selector_combo.blockSignals(True)
        self.game_selector_combo.clear()
        managed_games = data_manager.list_managed_games()
        if not managed_games:
            self.game_selector_combo.addItem("No hay juegos gestionados")
            self.game_selector_combo.setEnabled(False)
            self.current_app_id = None
        else:
            self.game_selector_combo.setEnabled(True)
            for app_id in managed_games:
                info = data_manager.get_game_info(app_id)
                game_name = info.get('name', 'Nombre Desconocido')
                self.game_selector_combo.addItem(f"{game_name} [AppID: {app_id}]", userData=app_id)
        self.game_selector_combo.blockSignals(False)
        self.on_game_selected(self.game_selector_combo.currentIndex())
    
    @pyqtSlot(int)
    def on_game_selected(self, index):
        self.current_app_id = self.game_selector_combo.itemData(index)
        self.update_mod_lists()
        self.clear_preview_panel()

    def on_mod_selected(self, current_item, previous_item=None):
        if not current_item:
            self.clear_preview_panel()
            return

        workshop_id = current_item.data(Qt.ItemDataRole.UserRole)
        if not workshop_id: return

        self.clear_preview_panel()
        self.mod_title_label.setText(f"Cargando {workshop_id}...")

        cached_data = cache_manager.get_mod_cache(self.current_app_id, workshop_id)
        if cached_data:
            self.update_preview_panel(cached_data)
            return

        scraper = SteamWebScraper(workshop_id)
        scraper.signals.finished.connect(lambda data, app_id=self.current_app_id, wid=workshop_id: self.on_scraping_finished(data, app_id, wid))
        scraper.signals.error.connect(lambda e: self.mod_title_label.setText(f"Error al cargar: {e}"))
        self.thread_pool.start(scraper)

    def on_scraping_finished(self, data: dict, app_id: str, workshop_id: str):
        cache_manager.save_mod_cache(app_id, workshop_id, data)
        self.update_preview_panel(data)

    def update_mod_lists(self):
        self.installed_mods_list.clear()
        self.pending_mods_list.clear()
        if not self.current_app_id: return

        all_mods = data_manager.get_mods_for_game(self.current_app_id)
        for mod in sorted(all_mods, key=lambda x: x.get('name', '').lower()):
            item_text = f"{mod.get('name', 'N/A')} (ID: {mod.get('workshop_id', 'N/A')})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, mod.get('workshop_id'))
            
            if mod.get('status') == 'installed':
                self.installed_mods_list.addItem(item)
            elif mod.get('status') == 'pending':
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                self.pending_mods_list.addItem(item)
    
    def clear_preview_panel(self):
        self.mod_title_label.setText("Selecciona un mod para ver sus detalles")
        self.mod_banner_label.clear()
        self.mod_banner_label.setText("")
        self.mod_desc_browser.clear()
        self.mod_deps_list.clear()
    
    @pyqtSlot(dict)
    def update_preview_panel(self, data: dict):
        self.mod_title_label.setText(data.get('title', 'Título no disponible'))
        self.mod_desc_browser.setHtml(data.get('description', '').replace('\n', '<br>'))
        
        self.mod_deps_list.clear()
        dependencies = data.get('dependencies', [])
        
        all_game_mods = data_manager.get_mods_for_game(self.current_app_id)
        installed_ids = {mod['workshop_id'] for mod in all_game_mods if mod.get('status') == 'installed'}
        pending_ids = {mod['workshop_id'] for mod in all_game_mods if mod.get('status') == 'pending'}

        if not dependencies:
            self.mod_deps_list.addItem("Ninguna")
        else:
            for dep in dependencies:
                dep_id = dep['id']
                item_text = f"{dep['name']} (ID: {dep_id})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, dep)

                if dep_id in installed_ids:
                    item.setForeground(QColor("lightgreen"))
                elif dep_id in pending_ids:
                    item.setForeground(QColor("yellow"))
                else:
                    item.setForeground(QColor("orangered"))
                
                self.mod_deps_list.addItem(item)
        
        image_url = data.get('image_url')
        if image_url:
            req = QNetworkRequest(QUrl(image_url))
            reply = self.network_manager.get(req)
            reply.finished.connect(lambda rep=reply: self.set_banner_image(rep))
        else:
            self.mod_banner_label.setText("Imagen no disponible")

    def set_banner_image(self, reply):
        if reply.error() == QNetworkRequest.NetworkError.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.mod_banner_label.setPixmap(pixmap.scaled(
                self.mod_banner_label.width(),
                self.mod_banner_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.mod_banner_label.setText("Error al cargar imagen")
        reply.deleteLater()

    @pyqtSlot()
    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    @pyqtSlot()
    def open_add_game_dialog(self):
        dialog = AddGameDialog(self)
        if dialog.exec():
            game_info = dialog.game_info
            if game_info:
                app_id = game_info['app_id']
                if app_id in data_manager.list_managed_games():
                    QMessageBox.warning(self, "Juego ya existente", f"El juego con AppID {app_id} ya está siendo gestionado.")
                    return
                data_manager.save_game_info(app_id, game_info)
                data_manager.save_mods_for_game(app_id, []) 
                self.populate_game_selector()
                self.statusBar().showMessage(f"Juego '{game_info['name']}' añadido.", 3000)

    @pyqtSlot(str, str, str)
    def handle_add_mod_from_url(self, app_id: str, workshop_id: str, mod_name: str):
        """
        Maneja la señal emitida por el navegador cuando se intercepta una URL personalizada.
        """
        if self.current_app_id != app_id:
            QMessageBox.information(self, "Juego Diferente", f"El mod es para un juego diferente ({app_id}). Cambia al juego correcto para gestionarlo.")
            return

        if data_manager.add_mod_to_game(app_id, workshop_id, mod_name):
            self.statusBar().showMessage(f"Mod '{mod_name}' añadido a pendientes (desde navegador).", 3000)
            self.update_mod_lists() # Actualizar la UI
        else:
            self.statusBar().showMessage(f"Mod '{mod_name}' (ID: {workshop_id}) ya está en la lista.", 3000)


    @pyqtSlot()
    def open_workshop_browser(self):
        if not self.current_app_id:
            QMessageBox.warning(self, "Sin Juego", "Por favor, selecciona un juego primero.")
            return
        
        # Recopilar los IDs de todos los mods gestionados para este juego
        all_managed_mods = data_manager.get_mods_for_game(self.current_app_id)
        managed_mod_ids = [mod['workshop_id'] for mod in all_managed_mods]
        
        workshop_url = f"https://steamcommunity.com/app/{self.current_app_id}/workshop/"
        
        # Pasar la lista de IDs al constructor de la BrowserWindow
        self.browser_window = BrowserWindow(workshop_url, managed_mod_ids, self)
        
        self.browser_window.confirm_mods_signal.connect(self.handle_confirmed_mods)
        self.browser_window.download_mods_signal.connect(self.handle_direct_download_request)
        
        self.browser_window.show()

    @pyqtSlot(list)
    def handle_direct_download_request(self, mods_to_add: list):
        """Añade los mods y comienza inmediatamente el proceso de descarga."""
        self.handle_confirmed_mods(mods_to_add) # Primero los añade
        
        # Selecciona TODOS los mods pendientes para el proceso de descarga, no solo los nuevos
        all_pending_mods = []
        for i in range(self.pending_mods_list.count()):
            item = self.pending_mods_list.item(i)
            workshop_id = item.data(Qt.ItemDataRole.UserRole)
            name = item.text().split(" (ID:")[0]
            all_pending_mods.append({'workshop_id': workshop_id, 'name': name})
            
        if all_pending_mods:
            # Reutilizamos el mismo flujo de descarga que ya teníamos
            final_download_list = resolve_dependencies(self.current_app_id, all_pending_mods, self)
            if final_download_list is not None:
                self.execute_steamcmd(final_download_list)
    
    @pyqtSlot(list)
    def handle_confirmed_mods(self, mods_to_add: list):
        """Recibe la lista de mods del panel lateral y los añade a pendientes."""
        added_count = 0
        for mod_data in mods_to_add:
            if data_manager.add_mod_to_game(mod_data['appId'], mod_data['workshopId'], mod_data['modName']):
                added_count += 1
        
        if added_count > 0:
            self.statusBar().showMessage(f"{added_count} mods añadidos a la lista de pendientes.", 4000)
            self.update_mod_lists()

    @pyqtSlot()
    def start_download_process(self):
        if not self.current_app_id:
            QMessageBox.warning(self, "Error", "Selecciona un juego primero.")
            return

        mods_to_download = []
        for i in range(self.pending_mods_list.count()):
            item = self.pending_mods_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                workshop_id = item.data(Qt.ItemDataRole.UserRole)
                name = item.text().split(" (ID:")[0]
                mods_to_download.append({'workshop_id': workshop_id, 'name': name})
        
        if not mods_to_download:
            QMessageBox.information(self, "Información", "No hay mods marcados para descargar.")
            return

        final_download_list = resolve_dependencies(self.current_app_id, mods_to_download, self)

        if final_download_list is not None:
            if not final_download_list:
                QMessageBox.information(self, "Nada que descargar", "La lista final de descarga está vacía.")
                return
            self.execute_steamcmd(final_download_list)

    def execute_steamcmd(self, download_list: list[dict]):
        game_path = data_manager.get_game_path(self.current_app_id)
        script_path = game_path / "download_script.txt"
        try:
            with open(script_path, 'w') as f:
                f.write("@ShutdownOnFailedCommand 1\n")
                f.write("@NoPromptForPassword 1\n")
                f.write("login anonymous\n")
                for mod in download_list:
                    f.write(f"workshop_download_item {self.current_app_id} {mod['workshop_id']}\n")
                f.write("quit\n")
        except IOError as e:
            QMessageBox.critical(self, "Error", f"No se pudo escribir el script de descarga: {e}")
            return
        
        self.console_dialog = ConsoleDialog(self)
        self.console_dialog.show()

        steamcmd_path = config_manager.get("Paths", "steamcmd_path")
        self.steam_cmd_worker = SteamCMDWorker(steamcmd_path, str(script_path))
        self.steam_cmd_worker.signals.output.connect(self.console_dialog.append_log)
        self.steam_cmd_worker.signals.finished.connect(lambda log: self.on_steamcmd_finished(log, download_list))
        self.steam_cmd_worker.signals.error.connect(lambda err: self.console_dialog.append_log(f"ERROR CRÍTICO: {err}"))
        self.console_dialog.cancel_button.clicked.connect(self.steam_cmd_worker.cancel)
        
        self.thread_pool.start(self.steam_cmd_worker)

    def on_steamcmd_finished(self, log: str, original_download_list: list[dict]):
        self.console_dialog.cancel_button.setEnabled(False)
        self.console_dialog.setWindowTitle("Salida de SteamCMD (Completado)")

        all_game_mods = data_manager.get_mods_for_game(self.current_app_id)
        final_install_dir = Path(data_manager.get_game_info(self.current_app_id).get("mod_install_path", ""))
        
        moved_ids, failed_ids = [], []
        
        for mod_to_check in original_download_list:
            mod_id = mod_to_check['workshop_id']
            # --- LÓGICA DE PARSEO CORREGIDA Y ROBUSTA ---
            # Usamos re.escape para manejar cualquier caracter especial en el mod_id, y re.IGNORECASE para robustez
            success_pattern = re.compile(r"Success. Downloaded item \"{}\" to \"(.*?)\"".format(re.escape(mod_id)), re.IGNORECASE)
            success_match = success_pattern.search(log)

            if success_match:
                # Extraer la ruta y quitarle las comillas y espacios extra
                downloaded_path_str = success_match.group(1).strip()
                downloaded_path = Path(downloaded_path_str)

                if not downloaded_path.exists():
                    self.console_dialog.append_log(f"FALLO (Post-descarga): La carpeta del mod {mod_id} no existe en la ruta reportada: {downloaded_path}")
                    failed_ids.append(mod_id)
                    continue
                
                # El destino final es la carpeta de mods del juego. El mod se moverá *dentro* de ella.
                final_mod_path = final_install_dir / mod_id
                if final_mod_path.exists():
                    shutil.rmtree(final_mod_path) # Eliminar versión antigua
                
                try:
                    # Mover la carpeta del mod descargado (ej: .../3532474381) a la carpeta de mods final.
                    shutil.move(str(downloaded_path), str(final_install_dir))
                    moved_ids.append(mod_id)
                except Exception as e:
                    self.console_dialog.append_log(f"ERROR al mover mod {mod_id}: {e}")
                    failed_ids.append(mod_id)
            else:
                failed_ids.append(mod_id)
                self.console_dialog.append_log(f"FALLO (SteamCMD): Mod {mod_id} no se descargó (no se encontró 'Success' en el log).")

        # Actualizar base de datos
        for mod in all_game_mods:
            if mod['workshop_id'] in moved_ids:
                mod['status'] = 'installed'
                mod['local_path'] = str(final_install_dir / mod['workshop_id'])
        data_manager.save_mods_for_game(self.current_app_id, all_game_mods)
        self.update_mod_lists()

        # Gestionar reintentos
        if failed_ids:
            failed_mods_info = [mod for mod in original_download_list if mod['workshop_id'] in failed_ids]
            reply = QMessageBox.question(self, "Descargas Fallidas", f"{len(failed_mods_info)} mods fallaron. ¿Reintentar?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.console_dialog.close()
                self.execute_steamcmd(failed_mods_info)
                return

        QMessageBox.information(self, "Proceso Terminado", f"Proceso de descarga finalizado.\nÉxitos: {len(moved_ids)}\nFallos: {len(failed_ids)}")

    @pyqtSlot(QListWidgetItem)
    def on_dependency_clicked(self, item: QListWidgetItem):
        if item.foreground().color() != QColor("orangered"):
            return

        dep_info = item.data(Qt.ItemDataRole.UserRole)
        workshop_id = dep_info['id']
        name = dep_info['name']
        
        if data_manager.add_mod_to_game(self.current_app_id, workshop_id, name):
            QMessageBox.information(self, "Mod Añadido", f"'{name}' ha sido añadido a la lista de pendientes.")
            item.setForeground(QColor("yellow")) # Cambiar color al instante
            self.update_mod_lists() # Refrescar la lista principal
        else:
            QMessageBox.information(self, "Mod Existente", f"'{name}' ya está en la lista de gestión.")

    @pyqtSlot(QPoint)
    def show_pending_mod_context_menu(self, pos: QPoint):
        item = self.pending_mods_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            remove_action = QAction("Quitar de Pendientes", self)
            workshop_id = item.data(Qt.ItemDataRole.UserRole)
            remove_action.triggered.connect(lambda: self.remove_from_pending(workshop_id))
            menu.addAction(remove_action)
            menu.exec(self.pending_mods_list.mapToGlobal(pos))
            
    def remove_from_pending(self, workshop_id: str):
        all_mods = data_manager.get_mods_for_game(self.current_app_id)
        mod_to_remove = next((mod for mod in all_mods if mod['workshop_id'] == workshop_id and mod['status'] == 'pending'), None)
        if mod_to_remove:
            all_mods.remove(mod_to_remove)
            data_manager.save_mods_for_game(self.current_app_id, all_mods)
            self.update_mod_lists()

    @pyqtSlot(QPoint)
    def show_installed_mod_context_menu(self, pos: QPoint):
        item = self.installed_mods_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            workshop_id = item.data(Qt.ItemDataRole.UserRole)
            if workshop_id:
                remove_action = QAction("Eliminar Mod (Local y Gestión)", self)
                remove_action.triggered.connect(lambda: self.remove_mod(workshop_id))
                menu.addAction(remove_action)
            menu.exec(self.installed_mods_list.mapToGlobal(pos))

    def remove_mod(self, workshop_id: str):
        reply = QMessageBox.question(self, "Confirmar Eliminación", f"¿Seguro que quieres eliminar el mod {workshop_id}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        all_mods = data_manager.get_mods_for_game(self.current_app_id)
        mod_to_remove = next((mod for mod in all_mods if mod['workshop_id'] == workshop_id), None)
        if mod_to_remove:
            if mod_to_remove.get('status') == 'installed':
                final_mod_path = Path(data_manager.get_game_info(self.current_app_id).get('mod_install_path', '')) / workshop_id
                if final_mod_path.exists():
                    try:
                        shutil.rmtree(final_mod_path)
                    except Exception as e:
                        QMessageBox.critical(self, "Error al Eliminar", f"No se pudo eliminar la carpeta: {e}")
                        return
            
            all_mods.remove(mod_to_remove)
            data_manager.save_mods_for_game(self.current_app_id, all_mods)
            self.update_mod_lists()
            self.clear_preview_panel()
            self.statusBar().showMessage(f"Mod '{mod_to_remove.get('name', workshop_id)}' eliminado.", 3000)

    @pyqtSlot()
    def check_for_updates(self):
        # La lógica de check_for_updates se mantiene igual que en la versión anterior.
        pass

    def show_about_dialog(self):
        QMessageBox.about(self, "Acerca de Steam Workshop Mod Manager", "<b>Steam Workshop Mod Manager v1.4</b><br>Desarrollado con PyQt6.")