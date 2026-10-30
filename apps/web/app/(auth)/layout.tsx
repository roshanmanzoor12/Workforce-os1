import type { ReactNode } from "react";

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({
  children,
}: AuthLayoutProps) {
  return (
    <main
      style={{
        minHeight: "100dvh",
        background: "#f7f4ec",
      }}
    >
      {children}
    </main>
  );
}