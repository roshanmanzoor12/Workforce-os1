import type { ReactNode } from "react";

type MetricTone =
  | "default"
  | "brand"
  | "success"
  | "warning"
  | "danger"
  | "info";

interface MetricCardProps {
  label: string;
  value: ReactNode;
  meta?: ReactNode;
  icon?: ReactNode;
  tone?: MetricTone;
}

function getToneStyles(
  tone: MetricTone,
): {
  background: string;
  border: string;
  color: string;
} {
  switch (tone) {
    case "brand":
      return {
        background: "var(--color-brand-softer)",
        border: "#f1dfaa",
        color: "#b27b00",
      };

    case "success":
      return {
        background: "var(--color-success-soft)",
        border: "#d9ebce",
        color: "var(--color-success-dark)",
      };

    case "warning":
      return {
        background: "var(--color-warning-soft)",
        border: "#f0dfac",
        color: "var(--color-warning-dark)",
      };

    case "danger":
      return {
        background: "var(--color-danger-soft)",
        border: "#f3d3d0",
        color: "var(--color-danger)",
      };

    case "info":
      return {
        background: "var(--color-info-soft)",
        border: "#d6e6f6",
        color: "var(--color-info-dark)",
      };

    default:
      return {
        background: "#f7f5f0",
        border: "var(--color-border)",
        color: "#5d6165",
      };
  }
}

export function MetricCard({
  label,
  value,
  meta,
  icon,
  tone = "default",
}: MetricCardProps) {
  const toneStyles = getToneStyles(tone);

  return (
    <section
      style={{
        position: "relative",
        minWidth: 0,
        minHeight: 116,
        padding: "17px 18px",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        background: "var(--color-surface)",
      }}
    >
      <div
        style={{
          paddingRight: icon ? 58 : 0,
        }}
      >
        <div
          style={{
            color: "var(--color-text-muted)",
            fontSize: "var(--font-size-sm)",
            fontWeight: 500,
          }}
        >
          {label}
        </div>

        <div
          style={{
            marginTop: 6,
            color: "var(--color-ink)",
            fontSize: "1.75rem",
            fontWeight: 400,
            lineHeight: 1.1,
            letterSpacing: "-0.025em",
          }}
        >
          {value}
        </div>

        {meta ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 5,
              marginTop: 10,
              color: "var(--color-text-muted)",
              fontSize: "var(--font-size-xs)",
              lineHeight: 1.4,
            }}
          >
            {meta}
          </div>
        ) : null}
      </div>

      {icon ? (
        <div
          aria-hidden="true"
          style={{
            position: "absolute",
            top: 17,
            right: 17,
            display: "grid",
            width: 46,
            height: 46,
            placeItems: "center",
            border: `1px solid ${toneStyles.border}`,
            borderRadius: "50%",
            background: toneStyles.background,
            color: toneStyles.color,
          }}
        >
          {icon}
        </div>
      ) : null}
    </section>
  );
}