export const AppTheme = {
  DarkGreen: "dark_green",
  Light: "light",
} as const;

export type AppTheme = (typeof AppTheme)[keyof typeof AppTheme];

export const ThemeBackgrounds: Record<AppTheme, string> = {
  [AppTheme.DarkGreen]:
    "bg-[#020804] text-white selection:bg-emerald-500/30 selection:text-white",
  [AppTheme.Light]: "bg-background",
};

export const DEFAULT_THEME = AppTheme.DarkGreen;
