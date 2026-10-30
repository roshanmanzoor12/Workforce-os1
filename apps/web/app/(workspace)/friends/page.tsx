import { Suspense } from "react";
import FriendsContent from "./friends-content";

export default function FriendsPage() {
  return (
    <Suspense fallback={
      <main style={{ padding: 24 }}>
        Loading friends...
      </main>
    }>
      <FriendsContent />
    </Suspense>
  );
}