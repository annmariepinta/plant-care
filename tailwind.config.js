/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#C1121F",
        secondary: "#2A9D55",
        tertiary: "#767676",
        quaternary: "#1F3D2B",
        quinary: "#FFB703",
        overlayy: "rgba(25, 28, 31, 0.5)",
      },
      fontFamily: {
        futura: ["Futura"], // Add your custom font here
      },
    },
  },
  plugins: [],
};

