import React, { createContext, useState, useEffect, useCallback } from 'react';

/**
 * ThemeContext — Dual-theme architecture for PhishGuard/ShadowWatch
 *
 * ISOLATION GUARANTEE:
 *   Dark mode  → html (no attribute)           → zero light styles apply
 *   Light mode → html[data-theme="light"]      → scoped overrides only
 *
 * This context ONLY manages which attribute is on <html>.
 * It never touches any existing dark-mode styles or components.
 */

export const ThemeContext = createContext({
  theme: 'dark',
  toggleTheme: () => {},
  isLight: false,
});

const STORAGE_KEY = 'shadowwatch-theme';
const LIGHT_ATTR  = 'data-theme';
const LIGHT_VAL   = 'light';

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Read persisted preference; default to dark
    try {
      return localStorage.getItem(STORAGE_KEY) === LIGHT_VAL ? LIGHT_VAL : 'dark';
    } catch {
      return 'dark';
    }
  });

  // Sync data-theme attribute on <html> whenever theme changes
  useEffect(() => {
    const root = document.documentElement;
    if (theme === LIGHT_VAL) {
      root.setAttribute(LIGHT_ATTR, LIGHT_VAL);
    } else {
      root.removeAttribute(LIGHT_ATTR);
    }
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch { /* ignore storage errors */ }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => (prev === LIGHT_VAL ? 'dark' : LIGHT_VAL));
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, isLight: theme === LIGHT_VAL }}>
      {children}
    </ThemeContext.Provider>
  );
};
