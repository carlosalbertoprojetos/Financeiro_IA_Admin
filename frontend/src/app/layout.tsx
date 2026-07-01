import type { Metadata } from "next";

import { AuthProvider } from "@/shared/auth/AuthProvider";
import { ThemeProvider } from "@/shared/theme/ThemeProvider";

import "./globals.css";

export const metadata: Metadata = {
  title: "TIP — Trello Intelligence Platform",
  description: "Plataforma de inteligência operacional Trello",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
