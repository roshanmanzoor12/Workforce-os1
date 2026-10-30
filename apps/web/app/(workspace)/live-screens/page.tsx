import { redirect } from "next/navigation";

export default function LegacyLiveScreenPage() {
  redirect("/monitoring/live-screen");
}