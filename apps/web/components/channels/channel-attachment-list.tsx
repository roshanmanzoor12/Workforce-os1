"use client";

import {
  Download,
  File,
  FileAudio,
  FileImage,
  FileVideo,
  Loader2,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  attachmentsService,
} from "@/services/attachments.service";

import type {
  AttachmentKind,
  BoundAttachmentResponse,
} from "@/types/attachments";


interface ChannelAttachmentListProps {
  attachments:
    BoundAttachmentResponse[];
}


function formatBytes(
  value:
    number,
): string {
  if (
    value <
    1024
  ) {
    return `${value} B`;
  }


  if (
    value <
    1024 *
      1024
  ) {
    return `${(
      value /
      1024
    ).toFixed(
      value >=
      100 *
        1024
        ? 0
        : 1,
    )} KB`;
  }


  return `${(
    value /
    1024 /
    1024
  ).toFixed(
    value >=
    100 *
      1024 *
      1024
      ? 0
      : 1,
  )} MB`;
}


function AttachmentIcon({
  kind,
}: {
  kind:
    AttachmentKind;
}) {
  if (
    kind ===
    "IMAGE"
  ) {
    return (
      <FileImage
        size={
          18
        }
      />
    );
  }


  if (
    kind ===
    "VIDEO"
  ) {
    return (
      <FileVideo
        size={
          18
        }
      />
    );
  }


  if (
    kind ===
    "AUDIO"
  ) {
    return (
      <FileAudio
        size={
          18
        }
      />
    );
  }


  return (
    <File
      size={
        18
      }
    />
  );
}


export function ChannelAttachmentList({
  attachments,
}: ChannelAttachmentListProps) {
  const [
    downloadingId,
    setDownloadingId,
  ] =
    useState<string | null>(
      null,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  async function download(
    attachment:
      BoundAttachmentResponse,
  ) {
    try {
      setDownloadingId(
        attachment.attachment_id,
      );


      setError(
        null,
      );


      const result =
        await attachmentsService.createDownload(
          attachment.attachment_id,
        );


      window.open(
        result.download_url,
        "_blank",
        "noopener,noreferrer",
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to download attachment.",
      );

    } finally {
      setDownloadingId(
        null,
      );
    }
  }


  if (
    attachments.length ===
    0
  ) {
    return null;
  }


  return (
    <div
      style={{
        display:
          "grid",

        gap:
          7,

        marginTop:
          8,

        maxWidth:
          520,
      }}
    >
      {attachments.map(
        (
          attachment,
        ) => {
          const downloading =
            downloadingId ===
            attachment.attachment_id;


          return (
            <button
              key={
                attachment.attachment_id
              }
              type="button"
              onClick={() => {
                void download(
                  attachment,
                );
              }}
              disabled={
                downloading
              }
              style={{
                width:
                  "100%",

                display:
                  "grid",

                gridTemplateColumns:
                  "28px minmax(0,1fr) 24px",

                alignItems:
                  "center",

                gap:
                  10,

                padding:
                  "9px 11px",

                border:
                  "1px solid var(--border, #e5e7eb)",

                borderRadius:
                  9,

                background:
                  "#faf8f3",

                color:
                  "inherit",

                textAlign:
                  "left",

                cursor:
                  downloading
                    ? "wait"
                    : "pointer",

                opacity:
                  downloading
                    ? 0.7
                    : 1,
              }}
            >
              <AttachmentIcon
                kind={
                  attachment.kind
                }
              />


              <span
                style={{
                  minWidth:
                    0,
                }}
              >
                <span
                  style={{
                    display:
                      "block",

                    overflow:
                      "hidden",

                    whiteSpace:
                      "nowrap",

                    textOverflow:
                      "ellipsis",

                    fontWeight:
                      700,
                  }}
                >
                  {attachment.filename}
                </span>


                <span
                  style={{
                    display:
                      "block",

                    marginTop:
                      2,

                    opacity:
                      0.6,

                    fontSize:
                      11,
                  }}
                >
                  {formatBytes(
                    attachment.size_bytes,
                  )}

                  {" · "}

                  {attachment.kind.toLowerCase()}
                </span>
              </span>


              {downloading ? (
                <Loader2
                  size={
                    16
                  }
                />
              ) : (
                <Download
                  size={
                    16
                  }
                />
              )}
            </button>
          );
        },
      )}


      {error ? (
        <div
          style={{
            color:
              "#b52b2b",

            fontSize:
              11,
          }}
        >
          {error}
        </div>
      ) : null}
    </div>
  );
}