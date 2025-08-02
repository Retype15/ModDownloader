import requests
from bs4 import BeautifulSoup
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

class ScraperSignals(QObject):
    """Señales para el scraper, para comunicación entre hilos."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

class SteamWebScraper(QRunnable):
    """
    Scraper que se ejecuta en un hilo para obtener detalles de la página de un mod
    de la Workshop de Steam sin congelar la UI.
    """
    def __init__(self, workshop_id: str):
        super().__init__()
        self.workshop_id = workshop_id
        self.signals = ScraperSignals()

    def run(self):
        try:
            url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={self.workshop_id}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Extraer datos
            title = soup.find('div', class_='workshopItemTitle').text.strip()
            description_div = soup.find('div', class_='workshopItemDescription')
            description = description_div.get_text(separator='\n', strip=True) if description_div else "No se encontró descripción."
            
            # El banner principal
            image_url = ""
            preview_image = soup.find('img', id='mainContentsContainer')
            if preview_image:
                image_url = preview_image['src']

            # Extraer dependencias
            dependencies = []
            required_items_section = soup.find('div', id='RequiredItems')
            if required_items_section:
                dependency_links = required_items_section.find_all('a')
                for link in dependency_links:
                    dep_name = link.find('div', class_='requiredItem').text.strip()
                    dep_url = link['href']
                    dep_id = dep_url.split('id=')[-1]
                    dependencies.append({'name': dep_name, 'id': dep_id})
            
            result = {
                'title': title,
                'description': description,
                'image_url': image_url,
                'dependencies': dependencies
            }
            self.signals.finished.emit(result)

        except requests.RequestException as e:
            self.signals.error.emit(f"Error de red: {e}")
        except Exception as e:
            self.signals.error.emit(f"Error de parsing: {e}")