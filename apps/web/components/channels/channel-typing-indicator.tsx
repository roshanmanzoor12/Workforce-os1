"use client";

interface ChannelTypingIndicatorProps {
  typingUserIds: string[];
  currentUserId?: string | null;
}


export function ChannelTypingIndicator({
  typingUserIds,
  currentUserId,
}: ChannelTypingIndicatorProps) {
  const visible =
    typingUserIds.filter(
      (userId) =>
        userId
        !== currentUserId,
    );


  if (
    visible.length === 0
  ) {
    return (
      <div
        className="h-5"
        aria-hidden="true"
      />
    );
  }


  const text =
    visible.length === 1
      ? "Someone is typing..."
      : visible.length === 2
        ? "2 people are typing..."
        : `${visible.length} people are typing...`;


  return (
    <div
      className="
        flex h-5 items-center
        text-xs text-muted-foreground
      "
      aria-live="polite"
    >
      <span
        className="
          mr-2 inline-flex gap-0.5
        "
        aria-hidden="true"
      >
        <span>
          •
        </span>
        <span>
          •
        </span>
        <span>
          •
        </span>
      </span>

      <span>
        {text}
      </span>
    </div>
  );
}