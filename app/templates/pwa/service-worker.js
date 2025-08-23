// service-worker.js

const CACHE_NAME = 'reporte-rural-cache-v1';
// Lista de archivos para almacenar en caché.
const urlsToCache = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  '/iconos/icon-192x192.png',
  '/iconos/icon-512x512.png'
];

// Evento 'install': se dispara cuando el service worker se instala.
self.addEventListener('install', event => {
  // Esperamos hasta que la promesa de caches.open se resuelva.
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache abierto');
        // Agregamos todos los archivos de nuestra lista al cache.
        return cache.addAll(urlsToCache);
      })
  );
});

// Evento 'fetch': se dispara cada vez que la página solicita un recurso (imagen, script, etc.).
self.addEventListener('fetch', event => {
  event.respondWith(
    // Buscamos si el recurso solicitado ya está en el cache.
    caches.match(event.request)
      .then(response => {
        // Si encontramos el recurso en el cache, lo devolvemos.
        if (response) {
          return response;
        }
        // Si no está en el cache, lo pedimos a la red.
        return fetch(event.request);
      }
    )
  );
});