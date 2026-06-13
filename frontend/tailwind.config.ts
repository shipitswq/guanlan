import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: "#D4835A", "primary-hover": "#C47A4A",
        bg: { primary: "#FAF8F5", secondary: "#FFFFFF" },
        border: "#E5E2DD",
        text: { primary: "#2C2824", secondary: "#8B8278" },
        success: "#5A8F5A", danger: "#C46A5A", warning: "#C9A84C",
        highlight: "#F0ECE7",
      },
    },
  },
  plugins: [],
};
export default config;