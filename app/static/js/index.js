// app/static/js/index.js
console.log("index.js loaded - For RUCFACIL home page specific scripts.");

document.addEventListener('DOMContentLoaded', function () {
    // Aquí puedes poner JavaScript que sea MUY específico de la página index.html
    // Por ejemplo, si tienes un carrusel solo en la home, o animaciones muy particulares.

    // La lógica de los modales de "Paso 1, 2, 3" y el audio de "Escucha"
    // que están en index.html podrían ir aquí si no están ya en main.js.

    // Ejemplo: Si el botón "listen-hero-explanation" está en index.html
    const heroListenButton = document.getElementById('listen-hero-explanation');
    if (heroListenButton) {
        heroListenButton.addEventListener('click', () => {
            alert('Audio para la explicación del Hero pendiente.');
            // Aquí iría la lógica para reproducir el audio específico del Hero.
        });
    }

    // Los Lottie players también se inicializarían aquí si son específicos de la home.
    // Ejemplo (si usas el web component lottie-player y lazy loading en main.js no los cubre):
    // document.querySelectorAll('.lazy-lottie-home').forEach(player => {
    //     if (player.dataset.src && !player.hasAttribute('loaded')) {
    //        // player.load(player.dataset.src); // O tu método de carga
    //        // player.setAttribute('loaded', 'true');
    //     }
    // });



    // --- LÓGICA PARA EL PANEL DE VIDEOS SECUENCIALES ---
    const videoGrid = document.getElementById('video-story-grid');
    if (videoGrid) {
        // Elementos del DOM
        const videos = Array.from(videoGrid.querySelectorAll('.story-video'));
        const wrappers = Array.from(videoGrid.querySelectorAll('.video-wrapper'));
        const audioBtn = document.getElementById('toggle-audio-btn');
        const iconSoundOn = document.getElementById('icon-sound-on');
        const iconSoundOff = document.getElementById('icon-sound-off');

        // Estado
        let currentVideoIndex = 0;
        let hasPlayedOnce = false;
        let isSequenceMuted = true; // El estado de audio para toda la secuencia

        if (videos.length > 0 && audioBtn) {
            
            // Función para reproducir el siguiente video
            const playNextVideo = () => {
                if (hasPlayedOnce) return;
                
                if (currentVideoIndex >= videos.length) {
                    hasPlayedOnce = true;
                    console.log("Secuencia de video completada.");
                    audioBtn.style.display = 'none'; // Oculta el botón al final
                    return;
                }

                wrappers.forEach(w => w.classList.remove('is-playing'));

                const currentVideo = videos[currentVideoIndex];
                const currentWrapper = wrappers[currentVideoIndex];
                
                // Aplicar el estado de silencio actual al video ANTES de reproducirlo
                currentVideo.muted = isSequenceMuted;

                currentWrapper.classList.add('is-playing');
                currentVideo.currentTime = 0;
                
                const playPromise = currentVideo.play();
                if (playPromise !== undefined) {
                    playPromise.catch(error => {
                        console.error("Error al reproducir video:", error);
                        hasPlayedOnce = true;
                    });
                }
                
                currentVideoIndex++;
            };

            // Evento para cambiar de video al terminar el actual
            videos.forEach(video => {
                video.addEventListener('ended', playNextVideo);
            });

            // Evento para el botón de audio
            audioBtn.addEventListener('click', () => {
                // Invertir el estado de silencio
                isSequenceMuted = !isSequenceMuted;

                // Aplicar el nuevo estado a TODOS los videos
                videos.forEach(video => {
                    video.muted = isSequenceMuted;
                });

                // Actualizar los iconos
                if (isSequenceMuted) {
                    iconSoundOn.classList.add('hidden');
                    iconSoundOff.classList.remove('hidden');
                } else {
                    iconSoundOn.classList.remove('hidden');
                    iconSoundOff.classList.add('hidden');
                }
            });
            
            // Iniciar la secuencia
            setTimeout(playNextVideo, 500);
        }
    }
});