/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // ── Background layers
        ink:       "#0c1220",
        panel:     "#111c2e",
        panelSoft: "#172032",
        panelMute: "#1d2940",

        // ── Borders
        edge: "rgba(55, 75, 105, 0.55)",

        // ── Clinical accent colours (muted, not neon)
        accent: {
          DEFAULT: "#4a84d6",
          50:  "#eef4fd",
          100: "#d6e6f9",
          200: "#aacbf3",
          300: "#74a8ea",
          400: "#4a84d6",
          500: "#3168b8",
          600: "#244f96",
        },

        // ── Semantic colours
        success: "#3d8a5c",   // good MHI, stable
        caution: "#b5822a",   // moderate / warning
        danger:  "#c04040",   // crisis / critical
        purple:  "#6a5acd",   // CBT / therapeutic

        // ── Text
        textPrimary:   "#c8d8ea",
        textSecondary: "#7a92a8",
        textMuted:     "#4a6278",
      },

      boxShadow: {
        card:  "0 1px 4px rgba(0,0,0,0.35), 0 0 0 1px rgba(55,75,105,0.35)",
        float: "0 8px 24px rgba(0,0,0,0.45)",
        modal: "0 20px 60px rgba(0,0,0,0.6)",
      },

      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body:    ["Manrope", "sans-serif"],
      },

      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          "0%":   { opacity: "0", transform: "translateX(-6px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        spinSlow: {
          "0%":   { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },

      animation: {
        fadeIn:   "fadeIn 0.22s ease forwards",
        slideIn:  "slideIn 0.22s ease forwards",
        spinSlow: "spinSlow 1.2s linear infinite",
      },
    },
  },
  plugins: [],
};
