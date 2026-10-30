import Link from "next/link";

interface WorkforceLogoProps {
  compact?: boolean;
}

export function WorkforceLogo({
  compact = false,
}: WorkforceLogoProps) {
  return (
    <Link
      href="/dashboard"
      aria-label="Workforce OS dashboard"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: compact ? 0 : 10,
        minWidth: 0,
        color: "var(--color-black)",
        textDecoration: "none",
      }}
    >
      <svg
        aria-hidden="true"
        width="34"
        height="34"
        viewBox="0 0 34 34"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          flex: "0 0 auto",
        }}
      >
        <circle
          cx="17"
          cy="17"
          r="16"
          fill="#171819"
        />

        <path
          d="M9.1 7.9C12.6 7.9 15.3 10.3 15.3 13.5C15.3 16.2 13.3 18.2 10.6 18.2C7.5 18.2 5.2 15.7 5.2 12.6C5.2 10.1 6.8 8.4 9.1 7.9Z"
          fill="#FAF8F3"
        />

        <path
          d="M24.9 7.9C22.6 8.4 21 10.1 21 12.6C21 15.7 23.3 18.2 26.4 18.2C29.1 18.2 31.1 16.2 31.1 13.5C31.1 10.3 28.4 7.9 24.9 7.9Z"
          fill="#FAF8F3"
        />

        <path
          d="M9.1 26.1C12.6 26.1 15.3 23.7 15.3 20.5C15.3 17.8 13.3 15.8 10.6 15.8C7.5 15.8 5.2 18.3 5.2 21.4C5.2 23.9 6.8 25.6 9.1 26.1Z"
          fill="#FAF8F3"
        />

        <path
          d="M24.9 26.1C22.6 25.6 21 23.9 21 21.4C21 18.3 23.3 15.8 26.4 15.8C29.1 15.8 31.1 17.8 31.1 20.5C31.1 23.7 28.4 26.1 24.9 26.1Z"
          fill="#FAF8F3"
        />

        <circle
          cx="17"
          cy="17"
          r="3.4"
          fill="#FAF8F3"
        />
      </svg>

      {!compact ? (
        <span
          style={{
            overflow: "hidden",
            color: "#171819",
            fontSize: 18,
            fontWeight: 600,
            letterSpacing: "-0.025em",
            lineHeight: 1,
            whiteSpace: "nowrap",
            textOverflow: "ellipsis",
          }}
        >
          Workforce OS
        </span>
      ) : null}
    </Link>
  );
}