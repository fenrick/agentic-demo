export default {
  content: ["./frontend/index.html", "./frontend/src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Montserrat", "sans-serif"],
        serif: ["Domine", "serif"],
      },
      colors: {
        primary: "#000000",
        accent: "#00ffc6",
      },
      boxShadow: {
        card: "0 4px 8px rgba(0, 0, 0, 0.05)",
      },
    },
  },
  plugins: [],
};
