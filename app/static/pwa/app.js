// app.js

// Espera a que el DOM esté completamente cargado para empezar.
window.addEventListener('DOMContentLoaded', () => {

    // --- REGISTRO DEL SERVICE WORKER ---
    // Esto es fundamental para que la PWA funcione offline.
    if ('serviceWorker' in navigator) {
        // La ruta debe coincidir con su ubicación en el servidor
        navigator.serviceWorker.register('/static/pwa/service-worker.js') 
            .then(registration => console.log('Service Worker registrado con éxito:', registration))
            .catch(error => console.log('Error al registrar el Service Worker:', error));
    }

    // --- REFERENCIAS A ELEMENTOS DEL DOM ---
    // Obtenemos todos los elementos interactivos de la página.
    const pantallaInicio = document.getElementById('pantallaInicio');
    const pantallaCamara = document.getElementById('pantallaCamara');
    const pantallaRevision = document.getElementById('pantallaRevision');
    
    const btnIniciar = document.getElementById('btnIniciar');
    const btnCapturar = document.getElementById('btnCapturar');
    const btnDescartar = document.getElementById('btnDescartar');
    const btnEnviar = document.getElementById('btnEnviar');

    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const estado = document.getElementById('estado');
    const spinner = document.getElementById('spinner');
    const inputTelefono = document.getElementById('telefono');
    const divDatosReporte = document.getElementById('datosReporte');
    
    // --- VARIABLES DE ESTADO ---
    // Aquí guardaremos los datos que recolectamos.
    let stream;
    let datosRecolectados = {
        latitud: null,
        longitud: null,
        fechaHora: null,
        telefono: null,
        fotoBlob: null,
        clima: null
    };

    // --- FUNCIONES AUXILIARES ---
    const mostrarSpinner = (mostrar) => {
        spinner.classList.toggle('hidden', !mostrar);
    };

    const cambiarPantalla = (pantallaVisible) => {
        pantallaInicio.classList.add('hidden');
        pantallaCamara.classList.add('hidden');
        pantallaRevision.classList.add('hidden');
        pantallaVisible.classList.remove('hidden');
    };

    // --- LÓGICA PRINCIPAL ---

    // 1. Iniciar el proceso de captura
    btnIniciar.addEventListener('click', async () => {
        mostrarSpinner(true);
        estado.textContent = 'Solicitando permisos...';

        // Guardamos el número de teléfono
        datosRecolectados.telefono = inputTelefono.value || 'No proporcionado';

        try {
            // A. Obtener la geolocalización
            estado.textContent = 'Obteniendo ubicación...';
            const posicion = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                });
            });
            datosRecolectados.latitud = posicion.coords.latitude.toFixed(6);
            datosRecolectados.longitud = posicion.coords.longitude.toFixed(6);
            
            // B. Obtener acceso a la cámara
            estado.textContent = 'Iniciando cámara...';
            stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' } // 'environment' prefiere la cámara trasera
            });
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                mostrarSpinner(false);
                cambiarPantalla(pantallaCamara);
            };

        } catch (error) {
            mostrarSpinner(false);
            console.error("Error al iniciar:", error);
            if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
                estado.textContent = 'Error: No se encontró una cámara trasera.';
            } else if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
                estado.textContent = 'Error: No diste permiso para acceder a la cámara o ubicación.';
            } else if (error.code === 1) { // Error de geolocalización
                 estado.textContent = 'Error: No diste permiso para acceder a la ubicación.';
            } else {
                estado.textContent = 'Ocurrió un error inesperado. Inténtalo de nuevo.';
            }
        }
    });

    // 2. Tomar la foto y estampar los datos
    btnCapturar.addEventListener('click', () => {
        // Ajustar el tamaño del canvas al del video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const context = canvas.getContext('2d');
        // Dibuja el frame actual del video en el canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Detener la cámara
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;

        // Preparar los datos para estampar en la foto
        datosRecolectados.fechaHora = new Date();
        const fechaFormateada = datosRecolectados.fechaHora.toLocaleDateString('es-ES');
        const horaFormateada = datosRecolectados.fechaHora.toLocaleTimeString('es-ES');
        const textoCoordenadas = `Lat: ${datosRecolectados.latitud}, Lon: ${datosRecolectados.longitud}`;
        const textoFechaHora = `${fechaFormateada} - ${horaFormateada}`;

        // Estilo del texto "estampado"
        const fontSize = Math.floor(canvas.width / 30); // Tamaño de fuente responsivo
        context.font = `bold ${fontSize}px Arial`;
        context.fillStyle = 'rgba(0, 0, 0, 0.5)';
        // Dibuja un fondo semitransparente para legibilidad
        context.fillRect(10, canvas.height - (fontSize * 2.5) - 20, context.measureText(textoCoordenadas).width + 20, (fontSize * 2.5) + 10);
        
        context.fillStyle = 'white';
        context.fillText(textoCoordenadas, 20, canvas.height - fontSize - 15);
        context.fillText(textoFechaHora, 20, canvas.height - 15);

        // Guardar la imagen del canvas como un Blob
        canvas.toBlob(blob => {
            datosRecolectados.fotoBlob = blob;
        }, 'image/jpeg', 0.9); // Calidad del 90%

        cambiarPantalla(pantallaRevision);
        mostrarDatosEnRevision();
    });

    // Función para mostrar los datos en la pantalla de revisión
    const mostrarDatosEnRevision = () => {
        divDatosReporte.innerHTML = `
            <p><strong>Teléfono:</strong> ${datosRecolectados.telefono}</p>
            <p><strong>Ubicación:</strong> ${datosRecolectados.latitud}, ${datosRecolectados.longitud}</p>
            <p><strong>Fecha y Hora:</strong> ${datosRecolectados.fechaHora.toLocaleString('es-ES')}</p>
            <p><strong>Clima:</strong> <span id="climaInfo">Pendiente de consulta...</span></p>
        `;
    };

    // 3. Descartar la foto y volver al inicio
    btnDescartar.addEventListener('click', () => {
        // Limpiar los datos para un nuevo reporte
        datosRecolectados = { latitud: null, longitud: null, fechaHora: null, telefono: null, fotoBlob: null, clima: null };
        estado.textContent = '';
        inputTelefono.value = '';
        cambiarPantalla(pantallaInicio);
    });

    // 4. Consultar el clima y preparar el envío final
    btnEnviar.addEventListener('click', async () => {
        mostrarSpinner(true);
        btnEnviar.disabled = true;
        btnDescartar.disabled = true;
        const climaInfoSpan = document.getElementById('climaInfo');
        climaInfoSpan.textContent = "Consultando API del clima...";

        try {
            // A. Consultar la API del clima (usando Open-Meteo, que no requiere API key)
            const urlClima = `https://api.open-meteo.com/v1/forecast?latitude=${datosRecolectados.latitud}&longitude=${datosRecolectados.longitud}¤t_weather=true`;
            const respuestaClima = await fetch(urlClima);
            if (!respuestaClima.ok) throw new Error('No se pudo obtener el clima.');
            
            const datosClima = await respuestaClima.json();
            datosRecolectados.clima = `Temp: ${datosClima.current_weather.temperature}°C, Viento: ${datosClima.current_weather.windspeed} km/h`;
            climaInfoSpan.textContent = datosRecolectados.clima;
            
            // B. Enviar todos los datos al backend
            await enviarReporteFinal();

        } catch (error) {
            console.error("Error al consultar clima o enviar:", error);
            climaInfoSpan.textContent = `Error al consultar clima. (${error.message})`;
            alert("No se pudo consultar el clima, pero puedes intentar enviar el reporte de todos modos.");
            // Aun con error de clima, podríamos permitir enviar
            await enviarReporteFinal();
        } finally {
            mostrarSpinner(false);
            btnEnviar.disabled = false;
            btnDescartar.disabled = false;
        }
    });

    // Función que realmente envía los datos al servidor
    const enviarReporteFinal = async () => {
        mostrarSpinner(true);
        estado.textContent = 'Enviando reporte al servidor...';

        // Usamos FormData para enviar archivos (la foto) y datos de texto juntos.
        // Es el método estándar y más robusto para esto.
        const formData = new FormData();
        formData.append('foto', datosRecolectados.fotoBlob, 'captura.jpg');
        formData.append('latitud', datosRecolectados.latitud);
        formData.append('longitud', datosRecolectados.longitud);
        formData.append('fechaHora', datosRecolectados.fechaHora.toISOString());
        formData.append('telefono', datosRecolectados.telefono);
        formData.append('clima', datosRecolectados.clima || 'No disponible');

        try {
            // ¡¡IMPORTANTE!! Reemplaza esta URL con la de tu endpoint en Railway.
            const urlBackend = '/api/guardar-reporte'; 

            const respuestaServidor = await fetch(urlBackend, {
                method: 'POST',
                body: formData 
                // No necesitas 'Content-Type', FormData lo establece automáticamente.
            });

            if (!respuestaServidor.ok) {
                // Si el servidor responde con un error (ej. 400, 500)
                const errorTexto = await respuestaServidor.text();
                throw new Error(`El servidor respondió con un error: ${errorTexto}`);
            }

            const resultado = await respuestaServidor.json();
            console.log('Respuesta del servidor:', resultado);
            alert('¡Reporte enviado con éxito!');
            
            // Limpiar y volver al inicio
            btnDescartar.click();

        } catch (error) {
            console.error('Error al enviar el reporte:', error);
            alert(`Ocurrió un error al enviar el reporte. Por favor, inténtalo de nuevo.\n\nDetalle: ${error.message}`);
        } finally {
            mostrarSpinner(false);
        }
    };
});