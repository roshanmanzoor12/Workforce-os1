"use client";

import type {
  ReactNode,
} from "react";

import {
  X,
} from "lucide-react";


interface RecruitmentModalProps {
  open: boolean;

  title: string;

  description?:
    | string
    | null;

  children:
    ReactNode;

  onClose:
    () => void;
}


export function RecruitmentModal({
  open,

  title,

  description,

  children,

  onClose,
}: RecruitmentModalProps) {
  if (!open) {
    return null;
  }


  return (
    <div
      role="presentation"
      onMouseDown={(
        event,
      ) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose();
        }
      }}
      style={{
        position:
          "fixed",

        inset:
          0,

        zIndex:
          120,

        display:
          "grid",

        placeItems:
          "center",

        padding:
          18,

        background:
          "rgba(15,23,42,.46)",
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        style={{
          width:
            "min(100%, 620px)",

          maxHeight:
            "calc(100dvh - 36px)",

          overflowY:
            "auto",

          background:
            "var(--color-surface)",

          border:
            "1px solid var(--color-border)",

          borderRadius:
            14,

          boxShadow:
            "0 24px 70px rgba(0,0,0,.22)",
        }}
      >
        <header
          style={{
            display:
              "flex",

            alignItems:
              "flex-start",

            justifyContent:
              "space-between",

            gap:
              16,

            padding:
              "18px 20px",

            borderBottom:
              "1px solid var(--color-border)",
          }}
        >
          <div>
            <h2
              style={{
                margin:
                  0,

                fontSize:
                  18,
              }}
            >
              {title}
            </h2>

            {description ? (
              <p
                className="text-label"
                style={{
                  margin:
                    "5px 0 0",

                  lineHeight:
                    1.55,
                }}
              >
                {description}
              </p>
            ) : null}
          </div>

          <button
            type="button"
            onClick={
              onClose
            }
            aria-label="Close"
            style={{
              width:
                34,

              height:
                34,

              flexShrink:
                0,

              display:
                "grid",

              placeItems:
                "center",

              border:
                0,

              borderRadius:
                8,

              background:
                "transparent",

              cursor:
                "pointer",
            }}
          >
            <X size={18} />
          </button>
        </header>

        <div
          style={{
            padding:
              20,
          }}
        >
          {children}
        </div>
      </section>
    </div>
  );
}