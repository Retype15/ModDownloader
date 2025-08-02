import requests
from app.core.config_manager import config_manager

class SteamAPIHandler:
    """Gestiona las llamadas a la API Web de Steam."""
    API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

    def __init__(self):
        self.api_key = config_manager.get("API", "steam_api_key")

    def get_mod_details(self, workshop_ids: list[str]) -> dict | None:
        """
        Obtiene detalles de una lista de mods de la Workshop.
        Devuelve un diccionario mapeando workshop_id -> mod_data.
        """
        if not self.api_key:
            print("Error: No se ha configurado la clave de API de Steam.")
            return None
        if not workshop_ids:
            return {}

        payload = {
            'itemcount': len(workshop_ids),
            **{f'publishedfileids[{i}]': wid for i, wid in enumerate(workshop_ids)}
        }
        
        try:
            response = requests.post(self.API_URL, data=payload)
            response.raise_for_status()
            data = response.json().get('response', {})
            
            if 'publishedfiledetails' in data:
                return {item['publishedfileid']: item for item in data['publishedfiledetails']}
            return {}
        except requests.RequestException as e:
            print(f"Error en la llamada a la API de Steam: {e}")
            return None

# Instancia única
steam_api_handler = SteamAPIHandler()