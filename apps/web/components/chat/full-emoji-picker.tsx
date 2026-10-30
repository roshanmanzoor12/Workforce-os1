"use client";

import dynamic from "next/dynamic";
import { Plus, Smile } from "lucide-react";
import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

type PanelProps = {
  onSelect: (emoji: string) => void;
};

const EmojiPanel = dynamic<PanelProps>(
  async () => {
    const module = await import("emoji-picker-react");
    const Picker = module.default;

    return function Panel({ onSelect }: PanelProps) {
      return (
        <Picker
          onEmojiClick={(data) => onSelect(data.emoji)}
          theme={module.Theme.LIGHT}
          emojiStyle={module.EmojiStyle.NATIVE}
          width="100%"
          height={390}
          autoFocusSearch
          searchDisabled={false}
          skinTonesDisabled={false}
          previewConfig={{ showPreview: false }}
        />
      );
    };
  },
  {
    ssr: false,
    loading: () => (
      <div style={{ padding: 20 }}>Loading emojis...</div>
    ),
  },
);

const QUICK_REACTIONS = [
  { emoji: "\u{1F44D}", label: "Thumbs up" },
  { emoji: "\u2764\uFE0F", label: "Heart" },
  { emoji: "\u{1F602}", label: "Laughing" },
  { emoji: "\u{1F62E}", label: "Surprised" },
  { emoji: "\u{1F622}", label: "Crying" },
  { emoji: "\u{1F64F}", label: "Folded hands" },
];

type Props = {
  onSelect: (emoji: string) => void;
  label?: string;
  className?: string;
  disabled?: boolean;
  size?: number;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  quickReactions?: boolean;
};

export function FullEmojiPicker({
  onSelect,
  label = "Choose emoji",
  className,
  disabled = false,
  size = 20,
  open,
  onOpenChange,
  quickReactions = false,
}: Props) {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const onOpenChangeRef = useRef(onOpenChange);

  const [internalOpen, setInternalOpen] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [position, setPosition] = useState({
    left: 12,
    top: 12,
    width: 350,
  });

  const isOpen = !disabled && (open ?? internalOpen);
  const compact = quickReactions && !showAll;

  useEffect(() => {
    onOpenChangeRef.current = onOpenChange;
  }, [onOpenChange]);

  useEffect(() => {
    if (!isOpen) {
      setShowAll(false);
    }
  }, [isOpen]);

  function changeOpen(value: boolean): void {
    if (onOpenChange) {
      onOpenChange(value);
    } else {
      setInternalOpen(value);
    }
  }

  function selectEmoji(emoji: string): void {
    changeOpen(false);
    onSelect(emoji);
  }

  useLayoutEffect(() => {
    if (!isOpen) {
      return;
    }

    function reposition(): void {
      const button = buttonRef.current;

      if (!button) {
        return;
      }

      const rect = button.getBoundingClientRect();
      const width = Math.min(
        compact ? 300 : 360,
        window.innerWidth - 24,
      );
      const height = Math.min(
        compact ? 52 : 392,
        window.innerHeight - 24,
      );
      const above = rect.top - height - 8;

      setPosition({
        width,
        left: Math.max(
          12,
          Math.min(
            rect.right - width,
            window.innerWidth - width - 12,
          ),
        ),
        top: above >= 12
          ? above
          : Math.max(
              12,
              Math.min(
                rect.bottom + 8,
                window.innerHeight - height - 12,
              ),
            ),
      });
    }

    reposition();

    window.addEventListener("resize", reposition);
    window.addEventListener("scroll", reposition, true);

    return () => {
      window.removeEventListener("resize", reposition);
      window.removeEventListener("scroll", reposition, true);
    };
  }, [isOpen, compact]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function close(): void {
      if (onOpenChangeRef.current) {
        onOpenChangeRef.current(false);
      } else {
        setInternalOpen(false);
      }
    }

    function outsideClick(event: PointerEvent): void {
      if (!(event.target instanceof Node)) {
        return;
      }

      if (
        buttonRef.current?.contains(event.target) ||
        panelRef.current?.contains(event.target)
      ) {
        return;
      }

      close();
    }

    function escape(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        close();
        buttonRef.current?.focus();
      }
    }

    document.addEventListener("pointerdown", outsideClick);
    document.addEventListener("keydown", escape);

    return () => {
      document.removeEventListener("pointerdown", outsideClick);
      document.removeEventListener("keydown", escape);
    };
  }, [isOpen]);

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        className={className}
        aria-label={label}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        disabled={disabled}
        onClick={() => changeOpen(!isOpen)}
      >
        <Smile size={size} />
      </button>

      {isOpen &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            ref={panelRef}
            data-workforce-emoji-picker
            role="dialog"
            aria-label={label}
            onPointerDown={(event) => event.stopPropagation()}
            onClick={(event) => event.stopPropagation()}
            style={{
              position: "fixed",
              left: position.left,
              top: position.top,
              width: position.width,
              maxHeight: "calc(100dvh - 24px)",
              overflow: "auto",
              zIndex: 10000,
              borderRadius: compact ? 999 : 12,
              background: "#fffdf7",
              boxShadow: "0 8px 28px rgba(30, 25, 15, 0.18)",
            }}
          >
            {compact ? (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 2,
                  padding: 6,
                }}
              >
                {QUICK_REACTIONS.map(({ emoji, label: title }) => (
                  <button
                    key={title}
                    type="button"
                    aria-label={title}
                    title={title}
                    onClick={() => selectEmoji(emoji)}
                    style={{
                      display: "grid",
                      placeItems: "center",
                      flex: "1 1 0",
                      minWidth: 0,
                      height: 38,
                      padding: 0,
                      border: 0,
                      borderRadius: "50%",
                      background: "transparent",
                      fontFamily: '"Segoe UI Emoji", "Apple Color Emoji", sans-serif',
                      fontSize: 24,
                      lineHeight: 1,
                      cursor: "pointer",
                    }}
                  >
                    {emoji}
                  </button>
                ))}

                <button
                  type="button"
                  aria-label="Show all emojis"
                  title="More emojis"
                  onClick={() => setShowAll(true)}
                  style={{
                    display: "grid",
                    placeItems: "center",
                    flex: "1 1 0",
                    minWidth: 0,
                    height: 38,
                    padding: 0,
                    border: 0,
                    borderRadius: "50%",
                    background: "#f0ece3",
                    color: "#403a30",
                    cursor: "pointer",
                  }}
                >
                  <Plus size={21} />
                </button>
              </div>
            ) : (
              <EmojiPanel onSelect={selectEmoji} />
            )}
          </div>,
          document.body,
        )}
    </>
  );
}