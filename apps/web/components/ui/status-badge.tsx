type StatusBadgeVariant =
  | "online"
  | "offline"
  | "active"
  | "inactive"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

interface StatusBadgeProps {
  children: React.ReactNode;
  variant?: StatusBadgeVariant;
  showDot?: boolean;
}

interface VariantStyles {
  background: string;
  color: string;
  dot: string;
}

function getVariantStyles(
  variant: StatusBadgeVariant,
): VariantStyles {
  switch (variant) {
    case "online":
    case "active":
    case "success":
      return {
        background: "var(--color-success-soft)",
        color: "var(--color-success-dark)",
        dot: "var(--color-success)",
      };

    case "warning":
      return {
        background: "var(--color-warning-soft)",
        color: "var(--color-warning-dark)",
        dot: "var(--color-warning)",
      };

    case "danger":
      return {
        background: "var(--color-danger-soft)",
        color: "var(--color-danger-dark)",
        dot: "var(--color-danger)",
      };

    case "info":
      return {
        background: "var(--color-info-soft)",
        color: "var(--color-info-dark)",
        dot: "var(--color-info)",
      };

    case "offline":
    case "inactive":
    case "neutral":
    default:
      return {
        background: "var(--color-neutral-status-soft)",
        color: "#62666a",
        dot: "#85898e",
      };
  }
}

export function StatusBadge({
  children,
  variant = "neutral",
  showDot = true,
}: StatusBadgeProps) {
  const styles = getVariantStyles(variant);

  return (
    <span
      style={{
        display: "inline-flex",
        minHeight: 22,
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        padding: "3px 8px",
        borderRadius: 999,
        background: styles.background,
        color: styles.color,
        fontSize: "var(--font-size-xs)",
        fontWeight: 500,
        lineHeight: 1,
        whiteSpace: "nowrap",
      }}
    >
      {showDot ? (
        <span
          aria-hidden="true"
          style={{
            width: 6,
            height: 6,
            flex: "0 0 auto",
            borderRadius: "50%",
            background: styles.dot,
          }}
        />
      ) : null}

      <span>{children}</span>
    </span>
  );
}