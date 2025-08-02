import json
from pathlib import Path
from app.core.data_manager import data_manager

class CacheManager:
    """
    Gestiona el almacenamiento y recuperación en caché de los detalles de los mods
    para evitar hacer scraping web repetidamente.
    """
    def get_cache_dir(self, app_id: str) -> Path:
        """Obtiene el directorio de caché para un juego específico."""
        cache_dir = data_manager.get_game_path(app_id) / "cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def get_mod_cache(self, app_id: str, workshop_id: str) -> dict | None:
        """Intenta recuperar los detalles de un mod desde el archivo de caché JSON."""
        cache_file = self.get_cache_dir(app_id) / f"{workshop_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def save_mod_cache(self, app_id: str, workshop_id: str, data: dict):
        """Guarda los detalles de un mod en un archivo de caché JSON."""
        cache_file = self.get_cache_dir(app_id) / f"{workshop_id}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

# Instancia única para ser usada en toda la aplicación
cache_manager = CacheManager()