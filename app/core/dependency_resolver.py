#app/core/dependency_resolver.py
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QColor

from app.core.data_manager import data_manager
from app.core.cache_manager import cache_manager
from app.ui.dialogs.dependency_dialog import DependencyDialog

def resolve_dependencies(app_id: str, initial_mods: list[dict], parent_widget) -> list[dict] | None:
    """
    Función síncrona y recursiva para resolver todas las dependencias de una lista de mods.

    Args:
        app_id (str): El AppID del juego actual.
        initial_mods (list[dict]): La lista inicial de mods seleccionados por el usuario.
        parent_widget: El widget padre (MainWindow) para el diálogo de dependencias.

    Returns:
        list[dict] | None: La lista final y completa de mods a descargar, o None si el usuario cancela.
    """
    full_download_queue = {mod['workshop_id']: mod for mod in initial_mods}
    processed_ids = set()
    ids_to_check = list(full_download_queue.keys())

    # Obtener todos los mods ya instalados
    installed_mods_ids = {mod['workshop_id'] for mod in data_manager.get_mods_for_game(app_id) if mod.get('status') == 'installed'}

    while ids_to_check:
        workshop_id = ids_to_check.pop(0)
        if workshop_id in processed_ids:
            continue

        # --- LÓGICA MEJORADA ---
        # El conjunto de "mods seguros" incluye los ya instalados y los que YA ESTÁN en la cola de descarga actual.
        safe_mods_ids = installed_mods_ids.union(full_download_queue.keys())

        mod_details = cache_manager.get_mod_cache(app_id, workshop_id)
        if not mod_details:
            processed_ids.add(workshop_id)
            continue
        
        dependencies = mod_details.get('dependencies', [])
        if not dependencies:
            processed_ids.add(workshop_id)
            continue

        missing_deps_data = {}
        for dep in dependencies:
            dep_id = dep.get('id')
            # Una dependencia falta si NO está en el conjunto de mods seguros.
            if dep_id and dep_id not in safe_mods_ids:
                missing_deps_data[dep_id] = dep.get('name', f"Mod ID {dep_id}")

        if missing_deps_data:
            dialog = DependencyDialog(missing_deps_data, parent_widget)
            if dialog.exec():
                newly_added_deps = dialog.selected_deps
                if not newly_added_deps:
                    pass
                else:
                    for new_dep in newly_added_deps:
                        new_id = new_dep['workshop_id']
                        if new_id not in full_download_queue:
                            full_download_queue[new_id] = new_dep
                            ids_to_check.append(new_id)
                            # Añadir a la base de datos como pendiente si no estaba ya
                            data_manager.add_mod_to_game(app_id, new_id, new_dep['name'])
                    
                    parent_widget.update_mod_lists()
            else:
                QMessageBox.information(parent_widget, "Cancelado", "Proceso de descarga cancelado durante la resolución de dependencias.")
                return None

        processed_ids.add(workshop_id)
    
    return list(full_download_queue.values())