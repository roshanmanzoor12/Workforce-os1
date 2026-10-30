import type { Metadata } from "next";

import { LoginClient } from "./login-client";

export const metadata: Metadata = {
  title: "Sign In",
  description:
    "Sign in to your Workforce OS account.",
};

export default function LoginPage() {
  return <LoginClient />;
}