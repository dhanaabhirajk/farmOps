import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Custom colors for agricultural theme
        "farm-green": "#2D5A27",
        "farm-light": "#E8F5E9",
        "earth-brown": "#8D6E63",
        "earth-light": "#D7CCC8",
        "sky-blue": "#E1F5FE",
        "cream": "#F5F5F0",
        
        primary: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e", // Main green
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
        },
        secondary: {
          50: "#fefce8",
          100: "#fef9c3",
          200: "#fef08a",
          300: "#fde047",
          400: "#facc15",
          500: "#eab308", // Harvest gold
          600: "#ca8a04",
          700: "#a16207",
          800: "#854d0e",
          900: "#713f12",
        },
        soil: {
          light: "#d4a574",
          DEFAULT: "#8b6f47",
          dark: "#654321",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        serif: ["Cormorant Garamond", "ui-serif", "Georgia", "serif"],
        tamil: ["Noto Sans Tamil", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
