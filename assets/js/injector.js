// assets/js/injector.js - Versión 15.0 - Arquitectura "Server First" y Sincronización
(function() {
    'use strict';
    
    if (typeof MOD_MANAGER_PORT === 'undefined') { return; }
    
    console.log(`ModManager Injector v15.0: Iniciado. Conectando al puerto ${MOD_MANAGER_PORT}.`);
    const API_URL = `http://127.0.0.1:${MOD_MANAGER_PORT}`;

    // --- 1. Inyección de Estilos CSS (sin cambios) ---
    const styles = `
        .mod-manager-anchor { position: relative !important; display: block !important; }
        .mod-manager-btn {
            position: absolute; top: 5px; right: 5px; width: 32px; height: 32px;
            border-radius: 6px; display: flex; align-items: center; justify-content: center;
            color: white !important; font-size: 24px; font-weight: bold; line-height: 1;
            cursor: pointer; z-index: 1001; transition: all 0.2s ease;
            border: 1px solid rgba(0,0,0,0.4); box-shadow: 0 2px 5px rgba(0,0,0,0.4);
        }
        .mod-manager-btn:hover { transform: scale(1.1); }
        .mod-manager-btn.add { background-color: #28a745; }
        .mod-manager-btn.remove { background-color: #007bff; font-size: 22px; }
        .mod-manager-btn.managed { background-color: #6c757d; cursor: not-allowed; font-size: 22px; }
        #mod-manager-floating-btn {
            position: fixed; bottom: 20px; right: 20px; width: 56px; height: 56px;
            border-radius: 50%; font-size: 32px;
        }
        #mod-manager-floating-btn.remove { font-size: 28px; }
    `;
    const styleSheet = document.createElement("style");
    styleSheet.innerText = styles;
    document.head.appendChild(styleSheet);

    // --- 2. Gestión de Estado ---
    let stagedMods = new Set();
    let managedMods = new Set();
    const currentAppId = getCurrentAppId();
    if (!currentAppId) return;

    // --- 3. Lógica Principal de Inicialización ---
    // NO HACEMOS NADA HASTA QUE EL SERVIDOR RESPONDA.
    fetch(`${API_URL}/status`)
        .then(response => {
            if (!response.ok) throw new Error(`El servidor respondió con el estado: ${response.status}`);
            return response.json();
        })
        .then(data => {
            stagedMods = new Set(data.staged || []);
            managedMods = new Set(data.managed || []);
            console.log("ModManager: Estado inicial recibido. Iniciando inyección de botones.", {staged: data.staged, managed: data.managed});
            
            // Ahora que tenemos el estado, podemos empezar a trabajar.
            if (window.location.href.includes('/sharedfiles/filedetails/')) {
                processDetailPage();
            } else {
                startObserver();
            }
        })
        .catch(err => console.error("ModManager: No se pudo obtener el estado inicial del servidor. Los botones no funcionarán correctamente.", err));

    // --- 4. Funciones de Botones y API ---
    async function handleAddClick(workshopId, modName) {
        stagedMods.add(workshopId);
        syncAllButtonsForId(workshopId, modName);
        try {
            await fetch(`${API_URL}/add`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ appId: currentAppId, workshopId, modName })
            });
        } catch (error) { console.error('ModManager: Error al añadir mod:', error); }
    }

    async function handleRemoveClick(workshopId, modName) {
        stagedMods.delete(workshopId);
        syncAllButtonsForId(workshopId, modName);
        try {
            await fetch(`${API_URL}/remove`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ appId: currentAppId, workshopId, modName })
            });
        } catch (error) { console.error('ModManager: Error al quitar mod:', error); }
    }

    function syncAllButtonsForId(workshopId, modName) {
        const buttons = document.querySelectorAll(`[data-workshop-id="${workshopId}"]`);
        buttons.forEach(button => updateButtonState(button, workshopId, modName));
    }

    function updateButtonState(button, workshopId, modName) {
        button.dataset.workshopId = workshopId;
        button.dataset.modName = modName;
        button.className = 'mod-manager-btn'; // Reset
        if (managedMods.has(workshopId)) {
            button.innerHTML = '*';
            button.classList.add('managed');
            button.title = 'Este mod ya está gestionado en la aplicación';
            button.onclick = (e) => { e.preventDefault(); e.stopPropagation(); };
        } else if (stagedMods.has(workshopId)) {
            button.innerHTML = '✓';
            button.classList.add('remove');
            button.title = 'Quitar de la lista de sesión';
            button.onclick = (e) => { e.preventDefault(); e.stopPropagation(); handleRemoveClick(workshopId, modName); };
        } else {
            button.innerHTML = '+';
            button.classList.add('add');
            button.title = 'Añadir a la lista de sesión';
            button.onclick = (e) => { e.preventDefault(); e.stopPropagation(); handleAddClick(workshopId, modName); };
        }
        if (button.id === 'mod-manager-floating-btn') { button.className += ' mod-manager-floating-btn'; }
    }

    // --- 5. Lógica de Inyección y Observador ---
    function processModLink(linkElement) {
        if (linkElement.dataset.modManagerProcessed) return;
        linkElement.dataset.modManagerProcessed = 'true';
        try {
            const workshopId = new URL(linkElement.href).searchParams.get('id');
            if (!workshopId) return;
            const titleElement = linkElement.querySelector('.workshopItemTitle, .workshop_item_title');
            const modName = (titleElement ? titleElement.textContent.trim() : linkElement.textContent.trim()) || `Mod ${workshopId}`;
            linkElement.classList.add('mod-manager-anchor');
            const button = document.createElement('div');
            // Crear el botón con el estado correcto desde el principio
            updateButtonState(button, workshopId, modName);
            linkElement.appendChild(button);
        } catch (e) { /* Ignorar errores en elementos extraños */ }
    }
    
    function startObserver() {
        const masterSelector = 'a[href*="/sharedfiles/filedetails/?id="]:not(.item_link)';
        function applyProcessing(targetNode) {
            targetNode.querySelectorAll(masterSelector).forEach(link => processModLink(link));
        }
        applyProcessing(document.body);
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        if (node.matches && node.matches(masterSelector)) {
                            processModLink(node);
                        }
                        applyProcessing(node);
                    }
                });
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    function processDetailPage() {
        const workshopId = new URL(window.location.href).searchParams.get('id');
        const modName = document.title.replace("Steam Workshop::", "").trim();
        if (!workshopId) return;

        // Esta lógica es simple y fiable.
        // Como se ejecuta después de tener el estado, siempre creará el botón correcto.
        if (document.getElementById('mod-manager-floating-btn')) return;
        const button = document.createElement('div');
        button.id = 'mod-manager-floating-btn';
        updateButtonState(button, workshopId, modName);
        document.body.appendChild(button);
    }
    
    function getCurrentAppId() {
        const urlMatch = window.location.href.match(/\/app\/(\d+)\/|appid=(\d+)/);
        if (urlMatch) return urlMatch[1] || urlMatch[2];
        return null;
    }
})();