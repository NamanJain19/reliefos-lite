/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface": "#051423",
        "surface-dim": "#051423",
        "surface-bright": "#2c3a4b",
        "surface-container-lowest": "#010f1e",
        "surface-container-low": "#0e1d2c",
        "surface-container": "#122130",
        "surface-container-high": "#1d2b3b",
        "surface-container-highest": "#283646",
        "surface-variant": "#283646",
        "surface-tint": "#4ddcc1",
        "on-surface": "#d5e4f9",
        "on-surface-variant": "#bbcac4",
        "inverse-surface": "#d5e4f9",
        "inverse-on-surface": "#233241",
        "outline": "#85948f",
        "outline-variant": "#3c4a46",
        "primary": "#4ddcc1",
        "on-primary": "#00382e",
        "primary-container": "#20bfa5",
        "on-primary-container": "#00483c",
        "inverse-primary": "#006b5b",
        "secondary": "#61d4ff",
        "on-secondary": "#003545",
        "secondary-container": "#01a0c9",
        "on-secondary-container": "#00313f",
        "tertiary": "#ffb3b1",
        "on-tertiary": "#650713",
        "tertiary-container": "#ff8786",
        "on-tertiary-container": "#7a1920",
        "error": "#ffb4ab",
        "on-error": "#690005",
        "error-container": "#93000a",
        "on-error-container": "#ffdad6",
        "background": "#051423",
        "on-background": "#d5e4f9",
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "sm": "0.125rem",
        "md": "0.375rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
      spacing: {
        "space-xs": "0.25rem",   // 4px: tight icon/text spacing
        "space-sm": "0.5rem",    // 8px: compact internal spacing
        "space-md": "0.75rem",   // 12px: standard component spacing
        "space-lg": "1rem",      // 16px: card padding and section gaps
        "space-xl": "1.25rem",   // 20px: major content spacing
        "space-2xl": "1.5rem",   // 24px: page section separation
        "space-3xl": "2rem",     // 32px: larger layout separation
        "gutter": "0.75rem",
        "gutter-lg": "1rem",
        "margin": "0.75rem",
        "margin-lg": "1.25rem",
      },
      fontSize: {
        "headline-lg": ["1.5rem", { lineHeight: "1.25", fontWeight: "600", letterSpacing: "-0.015em" }], // 24px Page Title
        "display-lg": ["1.5rem", { lineHeight: "1.25", fontWeight: "600", letterSpacing: "-0.015em" }],  // 24px
        "headline-md": ["1.125rem", { lineHeight: "1.35", fontWeight: "600", letterSpacing: "-0.01em" }], // 18px Section Heading
        "headline-sm": ["0.9375rem", { lineHeight: "1.4", fontWeight: "600" }],                             // 15px Card Heading
        "body-lg": ["0.875rem", { lineHeight: "1.5", fontWeight: "400" }],                                 // 14px
        "body-md": ["0.8125rem", { lineHeight: "1.5", fontWeight: "400" }],                                 // 13px Body text
        "body-sm": ["0.75rem", { lineHeight: "1.4", fontWeight: "400" }],                                   // 12px Secondary text
        "label-md": ["0.8125rem", { lineHeight: "1.3", fontWeight: "500" }],                                // 13px Form labels / nav
        "label-sm": ["0.6875rem", { lineHeight: "1.3", fontWeight: "500", letterSpacing: "0.02em" }],      // 11px Metadata / tags
        "label-xs": ["0.625rem", { lineHeight: "1.2", fontWeight: "600", letterSpacing: "0.04em" }],       // 10px Uppercase tags
        "kpi-lg": ["1.625rem", { lineHeight: "1.1", fontWeight: "700", letterSpacing: "-0.02em" }],       // 26px KPI Value
        "kpi-md": ["1.375rem", { lineHeight: "1.15", fontWeight: "700", letterSpacing: "-0.015em" }],     // 22px KPI Sub-value
      },
      fontFamily: {
        "display-lg": ["Inter", "sans-serif"],
        "headline-lg": ["Inter", "sans-serif"],
        "headline-md": ["Inter", "sans-serif"],
        "headline-sm": ["Inter", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "body-sm": ["Inter", "sans-serif"],
        "label-md": ["Inter", "sans-serif"],
        "label-sm": ["Inter", "sans-serif"],
        "mono-data": ["Inter", "monospace"],
      }
    },
  },
  plugins: [],
}
