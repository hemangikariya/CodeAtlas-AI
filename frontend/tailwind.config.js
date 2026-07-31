/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        surface: "#161b2d",
        border: "#242c46",
        primary: "#6366f1", // sleek violet Indigo
        primaryHover: "#4f46e5",
        textPrimary: "#f8fafc",
        textSecondary: "#94a3b8",
        success: "#10b981",
        danger: "#ef4444"
      }
    },
  },
  plugins: [],
}
