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
});