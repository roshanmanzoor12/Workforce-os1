"use client";

interface ChannelUnreadBadgeProps {
  count: number;
}


export function ChannelUnreadBadge({
  count,
}: ChannelUnreadBadgeProps) {
  if (
    count <= 0
  ) {
    return null;
  }


  const label =
    count > 99
      ? "99+"
      : String(
          count,
        );


  return (
    <span
      className="
        inline-flex min-w-5
        items-center justify-center
        rounded-full
        bg-foreground
        px-1.5 py-0.5
        text-[10px]
        font-semibold
        text-background
      "
      aria-label={
        `${count} unread messages`
      }
    >
      {label}
    </span>
  );
}