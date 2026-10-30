"use client";

import {
  Send,
} from "lucide-react";

import {
  useEffect,
  useRef,
  useState,
} from "react";


interface ChannelMessageComposerProps {
  disabled?: boolean;

  submitting?: boolean;

  onSend:
    (
      content: string,
    ) => Promise<void>;

  onTypingStart?:
    () => void;

  onTypingStop?:
    () => void;
}


export function ChannelMessageComposer({
  disabled = false,
  submitting = false,
  onSend,
  onTypingStart,
  onTypingStop,
}: ChannelMessageComposerProps) {
  const [
    value,
    setValue,
  ] =
    useState(
      "",
    );


  const typingRef =
    useRef(
      false,
    );


  const typingTimerRef =
    useRef<
      ReturnType<
        typeof setTimeout
      >
      | null
    >(
      null,
    );


  function stopTyping() {
    if (
      typingTimerRef.current
    ) {
      clearTimeout(
        typingTimerRef.current,
      );

      typingTimerRef.current =
        null;
    }


    if (
      typingRef.current
    ) {
      typingRef.current =
        false;

      onTypingStop?.();
    }
  }


  function scheduleTypingStop() {
    if (
      typingTimerRef.current
    ) {
      clearTimeout(
        typingTimerRef.current,
      );
    }


    typingTimerRef.current =
      setTimeout(
        () => {
          stopTyping();
        },
        1400,
      );
  }


  useEffect(
    () => {
      return () => {
        stopTyping();
      };
    },
    [],
  );


  async function submit() {
    const content =
      value.trim();


    if (
      !content
      || disabled
      || submitting
    ) {
      return;
    }


    stopTyping();


    await onSend(
      content,
    );


    setValue(
      "",
    );
  }


  return (
    <div
      className="
        border-t
        bg-background
        p-3
      "
    >
      <div
        className="
          flex items-end
          gap-2
          rounded-xl
          border
          bg-muted/20
          p-2
        "
      >
        <textarea
          value={
            value
          }
          disabled={
            disabled
            || submitting
          }
          rows={1}
          placeholder="Message channel"
          onChange={(
            event,
          ) => {
            setValue(
              event.target.value,
            );


            if (
              !typingRef.current
              && event.target.value
                .trim()
            ) {
              typingRef.current =
                true;

              onTypingStart?.();
            }


            if (
              event.target.value
                .trim()
            ) {
              scheduleTypingStop();

            } else {
              stopTyping();
            }
          }}
          onKeyDown={(
            event,
          ) => {
            if (
              event.key
              !== "Enter"
            ) {
              return;
            }


            if (
              event.shiftKey
            ) {
              return;
            }


            event.preventDefault();

            void submit();
          }}
          className="
            min-h-10
            max-h-32
            flex-1
            resize-none
            bg-transparent
            px-2
            py-2
            text-sm
            outline-none
          "
        />


        <button
          type="button"
          disabled={
            disabled
            || submitting
            || !value.trim()
          }
          onClick={() => {
            void submit();
          }}
          className="
            inline-flex
            h-9
            w-9
            items-center
            justify-center
            rounded-lg
            bg-foreground
            text-background
            disabled:opacity-40
          "
          aria-label="Send message"
        >
          <Send
            size={16}
          />
        </button>
      </div>
    </div>
  );
}