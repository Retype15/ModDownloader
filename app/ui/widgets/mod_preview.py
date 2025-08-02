from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser, QListWidget, QListWidgetItem
from PyQt6.QtCore import pyqtSlot, QUrl, Qt
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest

class ModPreviewWidget(QWidget):
    """Panel de previsualización que muestra los detalles de un mod."""
    dependency_add_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.network_manager = QNetworkAccessManager(self)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.mod_title_label = QLabel("Selecciona un mod para ver sus detalles")
        self.mod_title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.mod_title_label.setWordWrap(True)
        layout.addWidget(self.mod_title_label)

        self.mod_banner_label = QLabel()
        self.mod_banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mod_banner_label.setMinimumHeight(200)
        self.mod_banner_label.setStyleSheet("border: 1px solid #555; background-color: #2d2d2d;")
        layout.addWidget(self.mod_banner_label)
        
        self.mod_desc_browser = QTextBrowser()
        self.mod_desc_browser.setReadOnly(True)
        layout.addWidget(self.mod_desc_browser)
        
        layout.addWidget(QLabel("<b>Dependencias (clic en las rojas para añadir):</b>"))
        self.mod_deps_list = QListWidget()
        self.mod_deps_list.setMaximumHeight(100)
        self.mod_deps_list.itemClicked.connect(self._on_dependency_clicked)
        layout.addWidget(self.mod_deps_list)

    @pyqtSlot()
    def clear(self):
        self.mod_title_label.setText("Selecciona un mod para ver sus detalles")
        self.mod_banner_label.clear()
        self.mod_banner_label.setText("")
        self.mod_desc_browser.clear()
        self.mod_deps_list.clear()

    @pyqtSlot(dict, set, set)
    def update_content(self, mod_details: dict, installed_ids: set, pending_ids: set):
        self.mod_title_label.setText(mod_details.get('title', 'Título no disponible'))
        self.mod_desc_browser.setHtml(mod_details.get('description', '').replace('\n', '<br>'))
        
        self.mod_deps_list.clear()
        dependencies = mod_details.get('dependencies', [])
        if not dependencies:
            self.mod_deps_list.addItem("Ninguna")
        else:
            for dep in dependencies:
                item = QListWidgetItem(f"{dep['name']} (ID: {dep['id']})")
                item.setData(Qt.ItemDataRole.UserRole, dep)
                if dep['id'] in installed_ids: item.setForeground(QColor("lightgreen"))
                elif dep['id'] in pending_ids: item.setForeground(QColor("yellow"))
                else: item.setForeground(QColor("orangered"))
                self.mod_deps_list.addItem(item)
        
        image_url = mod_details.get('image_url')
        if image_url:
            req = QNetworkRequest(QUrl(image_url))
            reply = self.network_manager.get(req)
            reply.finished.connect(lambda rep=reply: self._set_banner_image(rep))
        else:
            self.mod_banner_label.setText("Imagen no disponible")

    def _set_banner_image(self, reply):
        if reply.error() == QNetworkRequest.NetworkError.NoError:
            pixmap = QPixmap()
            pixmap.loadFromData(reply.readAll())
            self.mod_banner_label.setPixmap(pixmap.scaled(self.mod_banner_label.width(), self.mod_banner_label.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.mod_banner_label.setText("Error al cargar imagen")
        reply.deleteLater()

    @pyqtSlot(QListWidgetItem)
    def _on_dependency_clicked(self, item: QListWidgetItem):
        if item.foreground().color() == QColor("orangered"):
            dep_info = item.data(Qt.ItemDataRole.UserRole)
            self.dependency_add_requested.emit(dep_info)
            item.setForeground(QColor("yellow")) # Feedback visual inmediato