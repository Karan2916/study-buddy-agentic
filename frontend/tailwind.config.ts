import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#192a26",
        muted: "#7d8983",
        canvas: "#f6f7f3",
        forest: "#1d5948",
        lime: "#d8f06b",
        line: "#e7ebe4",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Manrope", "Inter", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        card: "0 8px 30px rgba(27, 57, 46, .045)",
      },
      animation: {
        "fade-in": "fade-in .28s ease-out",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(5px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
