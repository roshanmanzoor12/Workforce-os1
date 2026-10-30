interface RecruitmentStatusProps {
  status: string | null | undefined;
  className?: string;
}

export function RecruitmentStatus({
  status,
  className,
}: RecruitmentStatusProps) {
  const value = status?.trim() || "unknown";

  const label = value
    .split(/[_-]+/)
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1),
    )
    .join(" ");

  return (
    <span
      className={[
        "status-badge",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      data-status={value}
    >
      {label}
    </span>
  );
}