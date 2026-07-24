/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        headroom: {
          bg: '#000000',
          card: '#0a0a0a',
          cardHover: '#121212',
          sidebar: '#0c0c0c',
          border: '#1f1f1f',
          borderHover: '#2e2e2e',
          text: '#ffffff',
          muted: '#888888',
          subtle: '#555555'
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
