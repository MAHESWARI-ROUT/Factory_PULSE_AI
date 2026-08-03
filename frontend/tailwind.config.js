/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#0A0F1A",
          900: "#0F1626",
          800: "#141D33",
          700: "#1C2740",
          600: "#2A3654",
        },
        signal: {
          cyan: "#3FD0E0",
          amber: "#F5A524",
          red: "#EF5A5A",
          green: "#3ED598",
        },
        ink: {
          100: "#EAEEF6",
          300: "#B7C0D6",
          500: "#7C88A3",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.6)",
      },
    },
  },
  plugins: [],
};
