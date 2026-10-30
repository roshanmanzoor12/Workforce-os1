import type { DevicePresence } from "@/types/device";

interface HeartbeatIndicatorProps {
  presence: DevicePresence;
  lastSeenLabel?: string | null;
  compact?: boolean;
}

export function HeartbeatIndicator({
  presence,
  lastSeenLabel,
  compact = false,
}: HeartbeatIndicatorProps) {
  const online = presence === "online";

  const label =
    presence === "online"
      ? "Online"
      : presence === "offline"
        ? "Offline"
        : "Unknown";

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <span
        aria-hidden="true"
        style={{
          position: "relative",
          display: "grid",
          width: compact ? 9 : 11,
          height: compact ? 9 : 11,
          placeItems: "center",
        }}
      >
        <span
          style={{
            width: compact ? 7 : 8,
            height: compact ? 7 : 8,
            borderRadius: "50%",
            background: online
              ? "var(--color-success)"
              : presence === "offline"
                ? "#8b8f93"
                : "#b8babd",
          }}
        />

        {online ? (
          <span
            style={{
              position: "absolute",
              inset: -3,
              border:
                "1px solid rgba(99,184,63,0.28)",
              borderRadius: "50%",
            }}
          />
        ) : null}
      </span>

      <span>
        <span
          style={{
            display: "block",
            color: online
              ? "var(--color-success-dark)"
              : "#5f6367",
            fontSize: compact ? 10 : 11,
            fontWeight: 500,
          }}
        >
          {label}
        </span>

        {!compact && lastSeenLabel ? (
          <span
            style={{
              display: "block",
              marginTop: 2,
              color:
                "var(--color-text-muted)",
              fontSize: 10,
            }}
          >
            {lastSeenLabel}
          </span>
        ) : null}
      </span>
    </div>
  );
}