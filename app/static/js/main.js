// =========================================================================
// === ARCHIVO main.js COMPLETO Y CORREGIDO - VERSIÓN FINAL ===
// =========================================================================

document.addEventListener('DOMContentLoaded', function () {
    
    // --- Cacheo de Elementos Comunes ---
    const htmlElement = document.documentElement;

    // --- Theme Toggle (Modo Oscuro/Claro) ---
    const themeToggleButtons = document.querySelectorAll('.theme-toggle-button');
    const logoLight = document.getElementById('logo-light');
    const logoDark = document.getElementById('logo-dark');
    const sunIcons = document.querySelectorAll('#theme-icon-sun-mobile');
    const moonIcons = document.querySelectorAll('#theme-icon-moon-mobile');
    const themeTextFooter = document.getElementById('theme-text-footer');

    const updateVisualsForTheme = (isDark) => {
        if (isDark) {
            htmlElement.classList.add('dark');
            if (logoLight) logoLight.classList.add('hidden');
            if (logoDark) logoDark.classList.remove('hidden');
            sunIcons.forEach(icon => icon.classList.add('hidden'));
            moonIcons.forEach(icon => icon.classList.remove('hidden'));
            if (themeTextFooter) themeTextFooter.textContent = 'Cambiar a Modo Claro';
        } else {
            htmlElement.classList.remove('dark');
            if (logoLight) logoLight.classList.remove('hidden');
            if (logoDark) logoDark.classList.add('hidden');
            sunIcons.forEach(icon => icon.classList.remove('hidden'));
            moonIcons.forEach(icon => icon.classList.add('hidden'));
            if (themeTextFooter) themeTextFooter.textContent = 'Cambiar a Modo Oscuro';
        }
    };

    let preferredTheme = localStorage.getItem('theme');
    if (!preferredTheme) {
        preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    updateVisualsForTheme(preferredTheme === 'dark');

    themeToggleButtons.forEach(button => {
        button.addEventListener('click', () => {
            const newTheme = htmlElement.classList.contains('dark') ? 'light' : 'dark';
            updateVisualsForTheme(newTheme === 'dark');
            localStorage.setItem('theme', newTheme);
        });
    });

    // --- Menú Móvil ---
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            const isHidden = mobileMenu.classList.toggle('hidden');
            mobileMenuButton.setAttribute('aria-expanded', String(!isHidden));
        });
    }

    // ========================================================================
    // === INICIO DE LA SECCIÓN CORREGIDA PARA EL MENÚ DE USUARIO (HTMX) ===
    // ========================================================================
    
    // Se usa delegación de eventos en 'body' para que funcione incluso
    // si HTMX reemplaza el contenido del header.
    document.body.addEventListener('click', function(event) {
        const target = event.target;
        
        // El método .closest() busca el elemento clickeado o su padre más cercano que coincida.
        // Es la clave para que esto funcione.
        const userMenuButton = target.closest('#user-menu-button');
        const userDropdown = document.getElementById('user-dropdown');

        // Si el menú no existe en la página, no hacemos nada.
        if (!userDropdown) return;

        // CASO 1: Se hizo clic EN o DENTRO del botón principal para abrir/cerrar.
        if (userMenuButton) {
            userDropdown.classList.toggle('hidden');
            const arrow = userMenuButton.querySelector('.dropdown-arrow');
            if (arrow) {
                arrow.classList.toggle('rotate-180', !userDropdown.classList.contains('hidden'));
            }
            return; // Salimos para no ejecutar el resto de la lógica.
        }

        // CASO 2: Se hizo clic DENTRO del menú desplegable que ya está abierto.
        if (target.closest('#user-dropdown')) {
            // No hacemos nada. Dejamos que el navegador maneje el clic.
            // Si es un enlace <a>, el navegador lo seguirá.
            // El menú se "cerrará" solo porque la página cambiará.
            return;
        }

        // CASO 3: El clic fue en cualquier otra parte de la página (fuera del botón y del menú).
        // Si el menú está abierto, lo cerramos.
        if (!userDropdown.classList.contains('hidden')) {
            userDropdown.classList.add('hidden');
            const mainButton = document.getElementById('user-menu-button'); // Buscamos el botón de nuevo
            if (mainButton) {
                const arrow = mainButton.querySelector('.dropdown-arrow');
                if (arrow) {
                    arrow.classList.remove('rotate-180');
                }
            }
        }
    });

    // ======================================================================
    // === FIN DE LA SECCIÓN CORREGIDA ===
    // ======================================================================
    
    // --- Lógica de Modales (Mejorada y Unificada) ---
    const openModalButtons = document.querySelectorAll('[data-modal-target]');
    const closeModalButtons = document.querySelectorAll('[data-modal-close]');
    const authModal = document.getElementById('auth-modal');

    const openModal = (modal) => {
        if (!modal) return;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        if (modal.id === 'auth-modal') {
            const initialView = modal.querySelector('#auth-initial-view');
            const otherViews = modal.querySelectorAll('#auth-login-view, #auth-register-view');
            if (initialView) initialView.classList.remove('hidden');
            otherViews.forEach(view => view.classList.add('hidden'));
        }
    };

    const closeModal = (modal) => {
        if (!modal) return;
        modal.classList.remove('active');
        document.body.style.overflow = '';
    };

    openModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modalId = button.dataset.modalTarget;
            const targetModal = document.getElementById(modalId);
            openModal(targetModal);
        });
    });

    closeModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal');
            closeModal(modal);
        });
    });

    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal(modal);
            }
        });
    });

    // --- Lógica del INTERIOR del Modal de Autenticación ---
    if (authModal) {
        const viewTriggers = authModal.querySelectorAll('[data-auth-view-target]');
        
        const showAuthView = (targetId) => {
            const views = authModal.querySelectorAll('#auth-initial-view, #auth-login-view, #auth-register-view');
            views.forEach(view => {
                view.classList.toggle('hidden', view.id !== targetId);
            });
        };

        viewTriggers.forEach(trigger => {
            trigger.addEventListener('click', () => {
                const targetId = trigger.dataset.authViewTarget;
                showAuthView(targetId);
            });
        });
        
        const backButtons = authModal.querySelectorAll('[data-auth-view-target="auth-initial-view"]');
        backButtons.forEach(button => {
            button.addEventListener('click', () => showAuthView('auth-initial-view'));
        });
    }

    // --- Lógica para abrir modal desde URL Hash ---
    const handleUrlHash = () => {
        const hash = window.location.hash;
        if (hash === '#auth-login' || hash === '#auth-register' || hash === '#auth-google-error' || hash === '#auth-login-error' || hash === '#auth-register-error-email') {
            if (authModal) {
                openModal(authModal);
                
                const initialView = document.getElementById('auth-initial-view');
                const loginView = document.getElementById('auth-login-view');
                const registerView = document.getElementById('auth-register-view');

                initialView.classList.add('hidden');
                if (hash === '#auth-login' || hash === '#auth-login-error') {
                    loginView.classList.remove('hidden');
                    registerView.classList.add('hidden');
                } else {
                    registerView.classList.remove('hidden');
                    loginView.classList.add('hidden');
                }

                setTimeout(() => {
                    history.replaceState(null, null, ' ');
                }, 100);
            }
        }
    };
    handleUrlHash();

    // --- Lazy Loading de Secciones ---
    const lazySections = document.querySelectorAll('.lazy-section');
    if ("IntersectionObserver" in window) {
        const sectionObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { rootMargin: "0px 0px -100px 0px" });

        lazySections.forEach(section => sectionObserver.observe(section));
    } else {
        lazySections.forEach(section => section.classList.add('visible'));
    }
    
    // --- Año Actual en el Footer ---
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // --- Botones "Escuchar" ---
    const listenButtons = document.querySelectorAll('.btn-listen-modal, #listen-hero-explanation');
    listenButtons.forEach(button => {
        button.addEventListener('click', () => {
            alert('Funcionalidad de audio pendiente de implementación.');
        });
    });
});