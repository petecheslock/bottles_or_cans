/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./templates/**/*.{html,j2,jinja,jinja2}",
    "./static/**/*.js"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

