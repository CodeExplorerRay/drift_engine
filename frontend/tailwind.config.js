/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        "quiet-card": "0 18px 48px rgba(15, 23, 42, 0.06)"
      },
      fontFamily: {
        sans: ["Aptos", "Segoe UI Variable Text", "Segoe UI", "sans-serif"],
        mono: ["Cascadia Mono", "Consolas", "monospace"]
      }
    }
  },
  plugins: []
};
