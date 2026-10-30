import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
}

export function PageHeader({
  title,
  description,
  actions,
}: PageHeaderProps) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 24,
        marginBottom: 22,
      }}
    >
      <div
        style={{
          minWidth: 0,
          flex: "1 1 auto",
        }}
      >
        <h1
          style={{
            margin: 0,
            color: "var(--color-black)",
            fontSize: "var(--font-size-3xl)",
            fontWeight: 500,
            lineHeight: 1.2,
            letterSpacing: "-0.025em",
          }}
        >
          {title}
        </h1>

        {description ? (
          <p
            style={{
              maxWidth: 720,
              marginTop: 7,
              color: "var(--color-text-muted)",
              fontSize: "var(--font-size-md)",
              lineHeight: 1.5,
            }}
          >
            {description}
          </p>
        ) : null}
      </div>

      {actions ? (
        <div
          style={{
            display: "flex",
            flex: "0 0 auto",
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 10,
          }}
        >
          {actions}
        </div>
      ) : null}
    </header>
  );
}