import json
import time
from pathlib import Path
from app.core.config_manager import config_manager

class DataManager:
    """Gestiona todos los datos específicos de los juegos (infos, mods)."""
    def __init__(self):
        self.gamedata_path = Path(config_manager.get("Paths", "gamedata_path", fallback="gamedata"))
        self.gamedata_path.mkdir(exist_ok=True)

    def get_game_path(self, app_id: str) -> Path:
        """Devuelve la ruta base para un juego específico."""
        return self.gamedata_path / str(app_id)

    def list_managed_games(self) -> list[str]:
        """Devuelve una lista de AppIDs de todos los juegos gestionados."""
        games = []
        for p in self.gamedata_path.iterdir():
            if p.is_dir() and (p / "game_info.json").exists():
                games.append(p.name)
        return sorted(games)

    def get_game_info(self, app_id: str) -> dict:
        """Lee el archivo game_info.json de un juego."""
        info_file = self.get_game_path(app_id) / "game_info.json"
        if not info_file.exists():
            return {}
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def save_game_info(self, app_id: str, data: dict):
        """Guarda datos en el game_info.json de un juego."""
        game_path = self.get_game_path(app_id)
        game_path.mkdir(exist_ok=True)
        (game_path / "staging").mkdir(exist_ok=True)
        with open(game_path / "game_info.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def get_mods_for_game(self, app_id: str) -> list[dict]:
        """Lee el archivo mods.json de un juego."""
        mods_file = self.get_game_path(app_id) / "mods.json"
        if not mods_file.exists():
            return []
        try:
            with open(mods_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, TypeError):
            return []

    def save_mods_for_game(self, app_id: str, mods_data: list[dict]):
        """Guarda la lista de mods en el mods.json de un juego."""
        game_path = self.get_game_path(app_id)
        game_path.mkdir(exist_ok=True)
        with open(game_path / "mods.json", 'w', encoding='utf-8') as f:
            json.dump(mods_data, f, indent=4)

    def add_mod_to_game(self, app_id: str, workshop_id: str, mod_name: str) -> bool:
        """Añade un nuevo mod al estado 'pending' si no existe ya."""
        mods = self.get_mods_for_game(app_id)
        
        if any(mod.get('workshop_id') == workshop_id for mod in mods):
            return False

        new_mod = {
            "workshop_id": workshop_id,
            "name": mod_name.strip(),
            "status": "pending",
            "time_updated": int(time.time()),
            "local_path": ""
        }
        mods.append(new_mod)
        self.save_mods_for_game(app_id, mods)
        return True

data_manager = DataManager()