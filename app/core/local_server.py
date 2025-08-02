import http.server
import socketserver
import json
from PyQt6.QtCore import QObject, pyqtSignal, QThread

SERVER_PORT = 27060

class LocalServerSignals(QObject):
    mod_received = pyqtSignal(dict)
    mod_removed = pyqtSignal(dict)

class HttpRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        # Pasar las referencias a los datos del servidor al manejador
        self.signals = server.signals
        self.staged_mods = server.staged_mods
        self.managed_mods = server.managed_mods
        super().__init__(request, client_address, server)

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Maneja la petición de estado inicial del script JS."""
        if self.path == '/status':
            try:
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                payload = {
                    'staged': list(self.staged_mods.keys()),
                    'managed': self.managed_mods
                }
                self.wfile.write(json.dumps(payload).encode('utf-8'))
            except Exception as e:
                print(f"Error en GET /status: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        # ... (La lógica de do_POST se mantiene idéntica a la versión anterior)
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            mod_data = json.loads(post_data.decode('utf-8'))
            if self.path == '/add': self.signals.mod_received.emit(mod_data)
            elif self.path == '/remove': self.signals.mod_removed.emit(mod_data)
            else: self.send_response(404); self.end_headers(); return
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
        except Exception as e:
            print(f"Error en POST: {e}")
            self.send_response(500)
            self._send_cors_headers()
            self.end_headers()

class ServerThread(QThread):
    def __init__(self, signals, staged_mods, managed_mods, parent=None):
        super().__init__(parent)
        self.signals = signals
        self.staged_mods = staged_mods # Referencia al dict de mods en sesión
        self.managed_mods = managed_mods # Lista de IDs de mods ya gestionados
        self.httpd = None

    def run(self):
        def handler_factory(*args, **kwargs):
            return HttpRequestHandler(*args, **kwargs)
        
        socketserver.TCPServer.allow_reuse_address = True
        self.httpd = socketserver.TCPServer(("", SERVER_PORT), handler_factory)
        # Pasar las referencias de datos al servidor para que el manejador pueda acceder a ellas
        self.httpd.signals = self.signals
        self.httpd.staged_mods = self.staged_mods
        self.httpd.managed_mods = self.managed_mods
        
        print(f"INFO: Servidor local iniciado en el puerto {SERVER_PORT}")
        self.httpd.serve_forever()

    def stop(self):
        if self.httpd:
            print("INFO: Deteniendo el servidor local...")
            self.httpd.shutdown()
            self.httpd.server_close()