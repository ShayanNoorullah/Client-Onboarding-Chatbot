/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ati: {
          navy: "#1a2b4a",
          gold: "#c9a227",
          light: "#eef1f6",
        },
      },
    },
  },
  plugins: [],
};
