export const AppTheme = {
  DarkGreen: "dark_green",
  Light: "light",
} as const;

export type AppTheme = (typeof AppTheme)[keyof typeof AppTheme];

export const ThemeBackgrounds: Record<AppTheme, string> = {
  [AppTheme.DarkGreen]:
    "bg-[radial-gradient(circle_at_center,#163328_0%,#020403_100%)]",
  [AppTheme.Light]: "bg-background",
};

export const DEFAULT_THEME = AppTheme.DarkGreen;
