/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dash dark theme colors
        background: '#1a1a1a',
        foreground: '#ffffff',
        primary: '#00D9FF', // Cyan accent
        secondary: '#2a2a2a',
        muted: '#3a3a3a',
        accent: '#00D9FF',
        border: '#3a3a3a',
        input: '#2a2a2a',
        ring: '#00D9FF',
      },
      fontFamily: {
        mono: ['Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
