"use client";

import {
  Hash,
  Plus,
} from "lucide-react";


interface ChannelWorkspaceEmptyProps {
  canCreate:
    boolean;

  onCreateDefault?():
    Promise<void>;
}


export function ChannelWorkspaceEmpty({
  canCreate,
  onCreateDefault,
}: ChannelWorkspaceEmptyProps) {
  return (
    <div
      style={{
        flex:
          1,

        minHeight:
          420,

        display:
          "grid",

        placeItems:
          "center",

        padding:
          32,

        textAlign:
          "center",
      }}
    >
      <div
        style={{
          maxWidth:
            440,
        }}
      >
        <div
          style={{
            width:
              56,

            height:
              56,

            display:
              "grid",

            placeItems:
              "center",

            margin:
              "0 auto 14px",

            borderRadius:
              14,

            background:
              "rgba(99,102,241,.12)",
          }}
        >
          <Hash
            size={26}
          />
        </div>

        <h2
          style={{
            margin:
              0,
          }}
        >
          No workspace channels
        </h2>

        <p
          style={{
            margin:
              "8px auto 0",

            opacity:
              0.65,

            lineHeight:
              1.6,
          }}
        >
          Create a text, announcement,
          or voice channel to start
          collaborating with your team.
        </p>

        {canCreate &&
        onCreateDefault ? (
          <button
            type="button"
            onClick={() =>
              void onCreateDefault()
            }
            style={{
              marginTop:
                18,

              minHeight:
                40,

              padding:
                "0 15px",

              display:
                "inline-flex",

              alignItems:
                "center",

              gap:
                7,

              cursor:
                "pointer",
            }}
          >
            <Plus
              size={16}
            />

            Create general
          </button>
        ) : null}
      </div>
    </div>
  );
}