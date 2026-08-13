// src/app/App.tsx

import { QueryProvider } from "../providers/QueryProvider";
import { ThemeProvider } from "../providers/ThemeProvider";
import { AuthProvider } from "../providers/AuthProvider";
import { ToastProvider } from "../providers/ToastProvider";

import AppRouter from "./router";

export default function App() {
  return (
    <QueryProvider>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <AppRouter />
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryProvider>
  );
}