document.addEventListener('DOMContentLoaded', () => {
    
    // Función universal para cerrar cualquier modal abierto
    const closeModal = () => {
        const openModal = document.querySelector('.modal-container.is-open');
        if (openModal) {
            openModal.classList.remove('is-open');
        }
        document.body.classList.remove('modal-is-open');
    };

    // Función para vincular eventos de cierre (ahora reutilizable)
    const bindModalCloseEvents = (context = document) => {
        context.querySelectorAll('[data-modal-close]').forEach(trigger => {
            // Removemos listeners existentes para evitar duplicados al recargar contenido
            trigger.removeEventListener('click', closeModal); 
            // Añadimos el listener
            trigger.addEventListener('click', closeModal);
        });
    };

    // Exponemos la función globalmente para que otros scripts puedan usarla
    window.bindModalCloseEvents = bindModalCloseEvents;

    // --- Vinculación de Eventos de Apertura (sin cambios) ---
    document.querySelectorAll('[data-modal-open]').forEach(trigger => {
        trigger.addEventListener('click', () => {
            const modalId = trigger.dataset.modalOpen;
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('is-open');
                document.body.classList.add('modal-is-open');
            }
        });
    });

    // --- Vinculación Inicial de Eventos de Cierre ---
    bindModalCloseEvents(); 

    // 3. Cerrar el modal con la tecla "Escape"
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeModal();
        }
    });
});