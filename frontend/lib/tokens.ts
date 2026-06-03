// Single source of truth for the shared slate/blue/severity color palette.
// All inline styles should reference these instead of raw hex literals.

export const colors = {
  // Surfaces
  bgBase:    "#0f172a",  // slate-950 — page background
  bgPanel:   "#1e293b",  // slate-800 — card / panel background
  bgClicked: "#1a2744",  // interaction highlight

  // Borders
  border: "#334155",  // slate-700

  // Text
  textPrimary:   "#f1f5f9",  // slate-100
  textSecondary: "#e2e8f0",  // slate-200
  textMuted:     "#94a3b8",  // slate-400
  textFaint:     "#64748b",  // slate-500
  textDimmer:    "#475569",  // slate-600
  textDimmest:   "#334155",  // slate-700 (border shade, used for very dim text)

  // Blue accent
  blue:      "#3b82f6",  // blue-500
  blueDark:  "#1e3a5f",  // blue-950 background
  blueLight: "#7dd3fc",  // sky-300

  // Severity — high (red)
  highBg:     "#7f1d1d",
  highBorder: "#ef4444",
  highText:   "#fca5a5",

  // Severity — medium (amber)
  medBg:     "#451a03",
  medBorder: "#f59e0b",
  medText:   "#fcd34d",

  // Severity — low (green)
  lowBg:     "#14532d",
  lowBorder: "#22c55e",
  lowText:   "#86efac",

  // Bus stops
  busPin:   "#0ea5e9",  // sky-500
  busBg:    "#0c4a6e",  // sky-950

  // Alert banner
  bannerAiBg:     "#7c2d12",
  bannerAiText:   "#fed7aa",
  bannerFeedBg:   "#431407",
  bannerFeedText: "#fde68a",
} as const;

export const severity = {
  high:   { bg: colors.highBg,  border: colors.highBorder,  text: colors.highText,  pin: colors.highBorder },
  medium: { bg: colors.medBg,   border: colors.medBorder,   text: colors.medText,   pin: colors.medBorder  },
  low:    { bg: colors.lowBg,   border: colors.lowBorder,   text: colors.lowText,   pin: colors.lowBorder  },
} as const;
