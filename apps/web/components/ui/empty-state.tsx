import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  minHeight?: number;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  minHeight = 280,
}: EmptyStateProps) {
  return (
    <div
      className="empty-state"
      style={{
        minHeight,
      }}
    >
      <div className="empty-state__content">
        {icon ? (
          <div className="empty-state__icon">
            {icon}
          </div>
        ) : null}

        <h3 className="empty-state__title">
          {title}
        </h3>

        {description ? (
          <p className="empty-state__description">
            {description}
          </p>
        ) : null}

        {action ? (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              marginTop: 16,
            }}
          >
            {action}
          </div>
        ) : null}
      </div>
    </div>
  );
}