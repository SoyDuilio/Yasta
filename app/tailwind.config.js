// C:/RUCFACIL/tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Habilita el modo oscuro basado en la clase 'dark' en el tag <html>
  content: [
    "./app/templates/**/*.html",   // Observa todos los archivos HTML en tus plantillas
    "./app/static/js/**/*.js",    // Observa archivos JS si generas clases de Tailwind allí
    "./app/**/*.py"               // Observa archivos Python si generas clases allí (ej. para HTMX)
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          '50': '#f0f9ff', '100': '#e0f2fe', '200': '#bae6fd',
          '300': '#7dd3fc', '400': '#38bdf8', '500': '#0ea5e9',
          '600': '#0284c7', '700': '#0369a1', '800': '#075985',
          '900': '#0c4a6e',
        },
        secondary: {
          '500': '#8b5cf6', '600': '#7c3aed',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', '"Noto Sans"', 'sans-serif', '"Apple Color Emoji"', '"Segoe UI Emoji"', '"Segoe UI Symbol"', '"Noto Color Emoji"'],
      },
    },
  },
  plugins: [
    // require('@tailwindcss/forms'), // Ejemplo
  ],
}