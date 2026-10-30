import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  applicationName: "Workforce OS",

  title: {
    default: "Workforce OS",
    template: "%s | Workforce OS",
  },

  description:
    "Workforce management, employee monitoring, device presence, attendance, productivity, and workforce operations platform.",

  robots: {
    index: false,
    follow: false,
  },

  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  colorScheme: "light",
  themeColor: "#faf8f3",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({
  children,
}: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <div id="workforce-os-root">
          {children}
        </div>
      </body>
    </html>
  );
}