import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hissövervakning",
  description: "Interaktiv jämförelse av hissarnas styrprofil och mekaniska vibrationssignaturer.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="sv">
      <body className="antialiased">{children}</body>
    </html>
  );
}
