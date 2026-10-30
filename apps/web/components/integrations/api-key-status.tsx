"use client";

import { StatusBadge } from "@/components/ui/status-badge";

import type { APIKeyPublic } from "@/types/api-keys";

function getStatus(
  key: APIKeyPublic,
): "success" | "warning" | "neutral" {
  if (key.revoked_at) {
    return "neutral";
  }

  if (
    key.expires_at &&
    new Date(key.expires_at).getTime() <=
      Date.now()
  ) {
    return "neutral";
  }

  return "success";
}

function getLabel(
  key: APIKeyPublic,
): string {
  if (key.revoked_at) {
    return "Revoked";
  }

  if (
    key.expires_at &&
    new Date(key.expires_at).getTime() <=
      Date.now()
  ) {
    return "Expired";
  }

  return "Active";
}

export function ApiKeyStatus({
  apiKey,
}: {
  apiKey: APIKeyPublic;
}) {
  return (
    <StatusBadge
      variant={getStatus(apiKey)}
    >
      {getLabel(apiKey)}
    </StatusBadge>
  );
}