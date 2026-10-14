/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: "#0c0d12",
        graphite: "#0c0d12",
        anthracite: "#151720",
        cardborder: "#222533",
      },
    },
  },
  plugins: [],
}
