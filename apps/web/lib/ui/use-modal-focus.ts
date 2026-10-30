"use client";

import { useEffect, useRef } from "react";

export function useModalFocus(
  open: boolean,
  onClose: () => void,
  busy = false,
) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  const busyRef = useRef(busy);

  closeRef.current = onClose;
  busyRef.current = busy;

  useEffect(() => {
    if (!open) return;

    const dialog = dialogRef.current;

    if (!dialog) return;

    const previous = document.activeElement;

    const selector =
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex="0"]';

    const focusable = () =>
      Array.from(
        dialog.querySelectorAll<HTMLElement>(selector),
      ).filter((element) => element.getClientRects().length > 0);

    (focusable()[0] ?? dialog).focus();

    function onKeyDown(event: KeyboardEvent) {
      if (!dialog) return;

      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();

        if (!busyRef.current) {
          closeRef.current();
        }
      }

      if (event.key !== "Tab") return;

      const elements = focusable();
      const first = elements[0];
      const last = elements[elements.length - 1];

      if (!first || !last) {
        event.preventDefault();
        dialog.focus();
      } else if (
        event.shiftKey &&
        (
          document.activeElement === first ||
          !dialog.contains(document.activeElement)
        )
      ) {
        event.preventDefault();
        last.focus();
      } else if (
        !event.shiftKey &&
        (
          document.activeElement === last ||
          !dialog.contains(document.activeElement)
        )
      ) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.removeEventListener("keydown", onKeyDown);

      if (
        previous instanceof HTMLElement &&
        previous.isConnected
      ) {
        previous.focus();
      }
    };
  }, [open]);

  return dialogRef;
}