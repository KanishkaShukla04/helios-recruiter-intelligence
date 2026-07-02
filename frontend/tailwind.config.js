/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      colors: {
        helios: {
          bg: "#050508",
          surface: "rgba(255,255,255,0.03)",
          border: "rgba(255,255,255,0.07)",
          violet: "#8b5cf6",
          indigo: "#6366f1",
          cyan: "#06b6d4",
          emerald: "#10b981",
        },
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out",
        "slide-up": "slide-up 0.4s ease-out",
        "shimmer": "shimmer 1.6s ease-in-out infinite",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          from: { transform: "translateX(-200%)" },
          to: { transform: "translateX(600%)" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(139,92,246,0.2)" },
          "50%": { boxShadow: "0 0 40px rgba(139,92,246,0.4)" },
        },
      },
    },
  },
  plugins: [],
};
