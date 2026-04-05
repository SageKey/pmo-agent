import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "1rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        navy: {
          50: "#f3f6fb",
          100: "#e3ebf5",
          200: "#c2d2e6",
          300: "#94b0d1",
          400: "#6489b7",
          500: "#436c9e",
          600: "#345684",
          700: "#2b466b",
          800: "#263c59",
          900: "#1a2b44",
          950: "#0d1627",
        },
        status: {
          green: "#22c55e",
          yellow: "#eab308",
          red: "#ef4444",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.06)",
        elev: "0 4px 12px rgba(16,24,40,0.08), 0 2px 4px rgba(16,24,40,0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
