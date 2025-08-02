#app/core/config_manager.py
import configparser
from pathlib import Path

CONFIG_FILE = Path("config.ini")
DEFAULT_CONFIG = {
    "Paths": {
        "steamcmd_path": "",
        "gamedata_path": "gamedata",
    },
    "API": {
        "steam_api_key": ""
    }
}

class ConfigManager:
    """Gestiona el archivo de configuración global (config.ini)."""
    def __init__(self):
        self.config = configparser.ConfigParser()
        if not CONFIG_FILE.exists():
            self.create_default_config()
        self.config.read(CONFIG_FILE)

    def create_default_config(self):
        """Crea un archivo de configuración con valores por defecto."""
        self.config.read_dict(DEFAULT_CONFIG)
        with open(CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

    def get(self, section, option, fallback=None):
        """Obtiene un valor de la configuración."""
        return self.config.get(section, option, fallback=fallback)

    def set(self, section, option, value):
        """Establece un valor en la configuración."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def save(self):
        """Guarda los cambios en el archivo config.ini."""
        with open(CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

# Instancia única para ser usada en toda la aplicación
config_manager = ConfigManager()