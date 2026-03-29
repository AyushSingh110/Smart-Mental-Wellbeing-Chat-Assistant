/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#09111f",
        panel: "#111c31",
        panelSoft: "#17233b",
        panelMute: "#1f2e48",
        edge: "rgba(148, 163, 184, 0.16)",
        brand: {
          300: "#6ce3cf",
          400: "#45d5cf",
          500: "#2cb8c7",
          600: "#1b9db6"
        },
        coral: "#ff7b70",
        gold: "#ffc96b",
        lime: "#7be495"
      },
      boxShadow: {
        halo: "0 20px 60px rgba(11, 26, 43, 0.35)"
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Manrope", "sans-serif"]
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at top, rgba(69, 213, 207, 0.14), transparent 34%), linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0))"
      }
    }
  },
  plugins: []
};
