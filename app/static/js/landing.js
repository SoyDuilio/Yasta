// --- FUNCIONES DEL MODAL ---
function openModal() {
    document.getElementById('modal-container').classList.add('is-open');
    document.body.classList.add('modal-open');
}

function closeModal() {
    document.getElementById('modal-container').classList.remove('is-open');
    document.body.classList.remove('modal-open');
}

// --- FUNCIÓN DE TRACKING ---
async function trackClick(eventName) {
    try {
        await fetch('/lanza/track-click', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event_name: eventName })
        });
        console.log(`Tracked: ${eventName}`);
    } catch (error) {
        console.error('Tracking failed:', error);
    }
}

// --- LÓGICA DE EVENTOS (LA CLAVE DE LA SOLUCIÓN) ---
document.addEventListener('DOMContentLoaded', () => {
    // Cerrar modal con la tecla Escape
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') { closeModal(); }
    });

    // Escuchar a HTMX: Después de que el contenido se cargue en el modal, ábrelo.
    htmx.on('#modal-content', 'htmx:afterSwap', function() {
        openModal();
    });
});