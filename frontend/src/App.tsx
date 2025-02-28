import React, { useMemo } from "react";
import { createTheme, ThemeProvider, CssBaseline } from "@mui/material";
import useMediaQuery from "@mui/material/useMediaQuery";
// Your custom code imports:
import RegistrationForm from "./RegistrationForm";

function App() {
  // This hook checks if user prefers dark mode at the OS/browser level
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");

  // Memoize the theme object to avoid re-creation on every render
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? "dark" : "light",
        },
      }),
    [prefersDarkMode]
  );

  return (
    <ThemeProvider theme={theme}>
      {/* CssBaseline sets up basic styles, including background and text for dark/light mode */}
      <CssBaseline />
      <RegistrationForm />
    </ThemeProvider>
  );
}

export default App;
