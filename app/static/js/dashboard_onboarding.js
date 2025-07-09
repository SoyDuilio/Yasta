// app/static/js/dashboard_onboarding.js
// VERSIÓN COMPLETA Y FINAL PARA RESTAURAR /onboarding

document.addEventListener('DOMContentLoaded', function () {
    console.log("[Onboarding] DOM cargado. Script de Onboarding iniciado.");

    const freemiumForm = document.getElementById('freemium-form');
    if (!freemiumForm) {
        console.log("[Onboarding] No se encontró el formulario 'freemium-form'. El script no continuará.");
        return;
    }
    
    console.log("[Onboarding] Formulario 'freemium-form' encontrado. Asignando listeners...");

    // --- Selectores ---
    const rucInput = document.getElementById('client_ruc_modal');
    const rucDetailsContainer = document.getElementById('ruc-details');
    const businessNameInput = document.getElementById('business_name');
    const businessAddressInput = document.getElementById('business_address');
    const rucSpinner = document.getElementById('ruc-spinner');
    const nextPeriodsContainer = document.getElementById('next-periods-container');
    const submitButton = document.getElementById('freemium-submit-btn');

    // --- Funciones Helper ---
    const showToast = (message, isError = false) => {
        const toast = document.getElementById('custom-toast');
        if (!toast) return;
        const toastMessage = toast.querySelector('#toast-message');
        const toastIcon = toast.querySelector('#toast-icon');
        if (!toastMessage || !toastIcon) return;
        
        toastMessage.textContent = message;
        toast.className = 'custom-toast';
        if (isError) {
            toast.classList.add('error');
            toastIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;
        } else {
            toastIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;
        }
        
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 5000);
    };

    const fetchWithTimeout = (url, options, timeout = 8000) => {
        return Promise.race([
            fetch(url, options),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), timeout))
        ]);
    };

    const handleRucValidation = async () => {
        const ruc = rucInput.value.trim();
        if (ruc.length !== 11 || !/^(10|20)\d{9}$/.test(ruc)) {
            rucDetailsContainer.classList.remove('visible');
            return;
        }

        rucSpinner.classList.remove('hidden');
        try {
            const infoResponse = await fetchWithTimeout(`/api/v1/utils/sunat-info/${ruc}`);
            if (!infoResponse.ok) {
                const errorData = await infoResponse.json();
                throw new Error(errorData.detail || 'No se pudo validar el RUC.');
            }
            const infoData = await infoResponse.json();
            
            businessNameInput.value = infoData.razonSocial;
            businessAddressInput.value = infoData.direccion;
            rucDetailsContainer.classList.add('visible');

            if(nextPeriodsContainer) {
                const periodsResponse = await fetchWithTimeout(`/api/v1/utils/next-freemium-periods/${ruc}`);
                if (periodsResponse.ok) {
                    const periodsData = await periodsResponse.json();
                    if (periodsData.periods) {
                        nextPeriodsContainer.innerHTML = '';
                        periodsData.periods.forEach(period => {
                            const periodElement = document.createElement('div');
                            periodElement.className = 'calendar-item';
                            periodElement.innerHTML = `<span>${period.name}</span><span class="due-text">${period.due_text}</span>`;
                            nextPeriodsContainer.appendChild(periodElement);
                        });
                    }
                }
            }
        } catch (error) {
            rucDetailsContainer.classList.remove('visible');
            showToast(`Error: ${error.message}`, true);
        } finally {
            rucSpinner.classList.add('hidden');
        }
    };

    const handleFormSubmit = (event) => {
        event.preventDefault();
        
        const pass1 = document.getElementById('sol_password_modal').value;
        const pass2 = document.getElementById('sol_password_confirm_modal').value;

        if (pass1 !== pass2) {
            showToast('Las Claves SOL no coinciden. Por favor, verifícalas.', true);
            return;
        }

        const spinner = submitButton.querySelector('.submit-spinner');
        submitButton.disabled = true;
        if(spinner) spinner.classList.remove('hidden');

        freemiumForm.submit();
    };

    // --- Asignación de Eventos ---
    rucInput.addEventListener('blur', handleRucValidation);
    freemiumForm.addEventListener('submit', handleFormSubmit);

    // --- Lógica de Modales ---
    const openModalButton = document.querySelector('[data-modal-target="freemium-register-modal"]');
    const modal = document.getElementById('freemium-register-modal');
    if (openModalButton && modal) {
        const closeModalButton = modal.querySelector('.modal-close-btn');
        const overlay = modal.querySelector('.modal-overlay');
        
        const openModal = () => {
            modal.classList.add('is-active');
            document.body.style.overflow = 'hidden';
        };

        const closeModal = () => {
            modal.classList.remove('is-active');
            document.body.style.overflow = '';
        };
        
        openModalButton.addEventListener('click', openModal);
        if (closeModalButton) closeModalButton.addEventListener('click', closeModal);
        if (overlay) overlay.addEventListener('click', closeModal);
    }

    // --- Gráficos de Ejemplo ---
    if (typeof Chart !== 'undefined') {
        const lineChartElement = document.getElementById('lineChart');
        const pieChartElement = document.getElementById('pieChart');
        if (lineChartElement) { new Chart(lineChartElement, { type: 'line', data: { labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'], datasets: [{ label: 'Impuestos', data: [650, 590, 800, 810, 560, 1250], borderColor: '#818cf8', tension: 0.4 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: '#9ca3af' } }, x: { grid: { display: false }, ticks: { color: '#9ca3af' } } } } }); }
        if (pieChartElement) { new Chart(pieChartElement, { type: 'doughnut', data: { labels: ['Planillas', 'Servicios', 'Compras', 'Otros'], datasets: [{ data: [300, 150, 200, 50], backgroundColor: ['#c084fc', '#f87171', '#fbbf24', '#60a5fa'], borderColor: '#1f2937', borderWidth: 4 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#d1d5db', padding: 10 } } } } }); }
    }
});