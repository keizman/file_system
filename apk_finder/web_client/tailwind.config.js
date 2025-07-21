/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3B82F6',
          hover: '#2563EB'
        },
        secondary: {
          DEFAULT: '#8B5CF6',
          hover: '#7C3AED'
        },
        surface: '#F8FAFC',
        'surface-hover': '#F1F5F9'
      }
    },
  },
  plugins: [],
}