"use client";

import { useState, type CSSProperties, type ReactNode } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import styles from "./user-avatar.module.css";

export function avatarImageUrl(value?: string | null): string | null {
  if (!value) return null;
  if (value.startsWith("/api/v1/personal/avatars/")) {
    const base = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/backend").replace(/\/+$/, "");
    return `${base}${value.slice("/api/v1".length)}`;
  }
  return value;
}

export function UserAvatar({ userId, src, name, size, className = "", style,
  fallback, animated = true }: {
  userId?: string | null; src?: string | null; name?: string | null;
  size?: number | string; className?: string; style?: CSSProperties;
  fallback?: ReactNode; animated?: boolean;
}) {
  const { user } = useWorkspace();
  const own = Boolean(userId && userId === user?.id);
  const selected = own ? user?.avatar_url : src;
  const url = avatarImageUrl(selected);
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const title = own
    ? [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.username
    : name;
  const letters = (title || "User").trim().split(/\s+/).slice(0, 2)
    .map(part => part.charAt(0).toUpperCase()).join("");
  const preset = Boolean(selected?.includes("/personal/avatars/presets/"));
  return <span className={`${styles.avatar} ${className}`} aria-hidden="true"
    style={{ width: size ?? "100%", height: size ?? "100%", ...style }}>
    {url && failedUrl !== url
      ? <img key={url} className={animated && preset ? styles.animated : undefined}
          src={url} alt="" referrerPolicy="no-referrer" draggable={false}
          onError={() => setFailedUrl(url)} />
      : fallback ?? letters}
  </span>;
}
