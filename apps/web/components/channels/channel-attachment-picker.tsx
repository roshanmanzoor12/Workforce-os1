"use client";

import {
  FileAudio,
  FileImage,
  FileText,
  FileVideo,
  Paperclip,
  X,
} from "lucide-react";

import {
  type ChangeEvent,
  useRef,
  useState,
} from "react";


interface ChannelAttachmentPickerProps {
  files: File[];

  disabled?: boolean;

  onChange: (
    files: File[],
  ) => void;
}


const MAX_ATTACHMENTS =
  10;


export function ChannelAttachmentPicker({
  files,

  disabled =
    false,

  onChange,
}: ChannelAttachmentPickerProps) {
  const inputRef =
    useRef<HTMLInputElement | null>(
      null,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  function openPicker() {
    if (
      disabled
    ) {
      return;
    }


    inputRef.current?.click();
  }


  function handleFiles(
    event:
      ChangeEvent<HTMLInputElement>,
  ) {
    const selected =
      Array.from(
        event.target.files ??
          [],
      );


    /*
     * Reset native input immediately.
     *
     * This allows selecting the same file again
     * after removing it from the pending list.
     */
    event.target.value =
      "";


    if (
      selected.length ===
      0
    ) {
      return;
    }


    const next =
      [...files];


    for (
      const file
      of selected
    ) {
      /*
       * Avoid accidental duplicate selections.
       *
       * name + size + lastModified gives us a useful
       * browser-side identity for a pending File.
       */
      const duplicate =
        next.some(
          (
            existing,
          ) =>
            existing.name ===
              file.name &&
            existing.size ===
              file.size &&
            existing.lastModified ===
              file.lastModified,
        );


      if (
        duplicate
      ) {
        continue;
      }


      if (
        next.length >=
        MAX_ATTACHMENTS
      ) {
        break;
      }


      next.push(
        file,
      );
    }


    if (
      files.length +
        selected.length >
      MAX_ATTACHMENTS
    ) {
      setError(
        `You can attach up to ${MAX_ATTACHMENTS} files to one message.`,
      );
    } else {
      setError(
        null,
      );
    }


    onChange(
      next,
    );
  }


  function removeFile(
    index:
      number,
  ) {
    if (
      disabled
    ) {
      return;
    }


    onChange(
      files.filter(
        (
          _,
          fileIndex,
        ) =>
          fileIndex !==
          index,
      ),
    );


    setError(
      null,
    );
  }


  function clearFiles() {
    if (
      disabled
    ) {
      return;
    }


    onChange(
      [],
    );


    setError(
      null,
    );


    if (
      inputRef.current
    ) {
      inputRef.current.value =
        "";
    }
  }


  return (
    <div
      style={{
        position:
          "relative",
      }}
    >
      <input
        ref={
          inputRef
        }
        type="file"
        multiple
        disabled={
          disabled
        }
        onChange={
          handleFiles
        }
        style={{
          display:
            "none",
        }}
      />


      <button
        type="button"
        title={
          files.length >=
          MAX_ATTACHMENTS
            ? `Maximum ${MAX_ATTACHMENTS} attachments reached`
            : "Attach files"
        }
        disabled={
          disabled ||
          files.length >=
            MAX_ATTACHMENTS
        }
        onClick={
          openPicker
        }
        style={{
          display:
            "grid",

          width:
            42,

          height:
            42,

          placeItems:
            "center",

          border:
            "1px solid var(--border, #e5e7eb)",

          borderRadius:
            8,

          background:
            "#fffefa",

          color:
            "#55585a",

          cursor:
            disabled ||
            files.length >=
              MAX_ATTACHMENTS
              ? "not-allowed"
              : "pointer",

          opacity:
            disabled
              ? 0.55
              : 1,
        }}
      >
        <Paperclip
          size={
            17
          }
        />
      </button>


      {files.length >
      0 ? (
        <div
          style={{
            position:
              "absolute",

            left:
              0,

            bottom:
              50,

            zIndex:
              30,

            width:
              340,

            maxWidth:
              "min(340px, calc(100vw - 40px))",

            overflow:
              "hidden",

            border:
              "1px solid var(--border, #e5e7eb)",

            borderRadius:
              9,

            background:
              "#fffefa",

            boxShadow:
              "0 12px 34px rgba(0,0,0,.14)",
          }}
        >
          <div
            style={{
              display:
                "flex",

              alignItems:
                "center",

              justifyContent:
                "space-between",

              gap:
                8,

              padding:
                "9px 10px",

              borderBottom:
                "1px solid var(--border, #e5e7eb)",
            }}
          >
            <div>
              <strong
                style={{
                  fontSize:
                    9,
                }}
              >
                Attachments
              </strong>


              <div
                style={{
                  marginTop:
                    2,

                  color:
                    "#838587",

                  fontSize:
                    7,
                }}
              >
                {files.length} /{" "}
                {MAX_ATTACHMENTS}
              </div>
            </div>


            <button
              type="button"
              disabled={
                disabled
              }
              title="Remove all attachments"
              onClick={
                clearFiles
              }
              style={{
                display:
                  "grid",

                width:
                  27,

                height:
                  27,

                placeItems:
                  "center",

                border:
                  "1px solid var(--border, #e5e7eb)",

                borderRadius:
                  6,

                background:
                  "transparent",

                color:
                  "#777",

                cursor:
                  disabled
                    ? "not-allowed"
                    : "pointer",
              }}
            >
              <X
                size={
                  12
                }
              />
            </button>
          </div>


          <div
            style={{
              display:
                "grid",

              gap:
                1,

              maxHeight:
                300,

              overflowY:
                "auto",
            }}
          >
            {files.map(
              (
                file,
                index,
              ) => (
                <PendingFileRow
                  key={`${file.name}-${file.size}-${file.lastModified}-${index}`}
                  file={
                    file
                  }
                  disabled={
                    disabled
                  }
                  onRemove={() =>
                    removeFile(
                      index,
                    )
                  }
                />
              ),
            )}
          </div>


          {error ? (
            <div
              style={{
                padding:
                  "8px 10px",

                borderTop:
                  "1px solid #f1c5c5",

                background:
                  "#fff2f2",

                color:
                  "#b52b2b",

                fontSize:
                  7,
              }}
            >
              {error}
            </div>
          ) : null}


          {files.length <
          MAX_ATTACHMENTS ? (
            <button
              type="button"
              disabled={
                disabled
              }
              onClick={
                openPicker
              }
              style={{
                width:
                  "100%",

                padding:
                  "8px 10px",

                border:
                  0,

                borderTop:
                  "1px solid var(--border, #e5e7eb)",

                background:
                  "#faf8f3",

                color:
                  "#55585a",

                textAlign:
                  "left",

                fontSize:
                  8,

                fontWeight:
                  600,

                cursor:
                  disabled
                    ? "not-allowed"
                    : "pointer",
              }}
            >
              + Add more files
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}


function PendingFileRow({
  file,

  disabled,

  onRemove,
}: {
  file:
    File;

  disabled:
    boolean;

  onRemove:
    () => void;
}) {
  return (
    <div
      style={{
        display:
          "grid",

        gridTemplateColumns:
          "32px minmax(0,1fr) 28px",

        alignItems:
          "center",

        gap:
          8,

        padding:
          "8px 9px",

        background:
          "#fffefa",
      }}
    >
      <div
        style={{
          display:
            "grid",

          width:
            30,

          height:
            30,

          placeItems:
            "center",

          borderRadius:
            6,

          background:
            "#eee9df",

          color:
            "#5d5f61",
        }}
      >
        <PendingFileIcon
          file={
            file
          }
        />
      </div>


      <div
        style={{
          minWidth:
            0,
        }}
      >
        <strong
          style={{
            display:
              "block",

            overflow:
              "hidden",

            textOverflow:
              "ellipsis",

            whiteSpace:
              "nowrap",

            fontSize:
              8,
          }}
        >
          {file.name}
        </strong>


        <div
          style={{
            marginTop:
              2,

            color:
              "#888",

            fontSize:
              7,
          }}
        >
          {formatBytes(
            file.size,
          )}

          {file.type ? (
            <>
              {" · "}
              {shortContentType(
                file.type,
              )}
            </>
          ) : null}
        </div>
      </div>


      <button
        type="button"
        disabled={
          disabled
        }
        title={`Remove ${file.name}`}
        onClick={
          onRemove
        }
        style={{
          display:
            "grid",

          width:
            26,

          height:
            26,

          placeItems:
            "center",

          border:
            0,

          borderRadius:
            6,

          background:
            "transparent",

          color:
            "#777",

          cursor:
            disabled
              ? "not-allowed"
              : "pointer",

          opacity:
            disabled
              ? 0.5
              : 1,
        }}
      >
        <X
          size={
            12
          }
        />
      </button>
    </div>
  );
}


function PendingFileIcon({
  file,
}: {
  file:
    File;
}) {
  if (
    file.type.startsWith(
      "image/",
    )
  ) {
    return (
      <FileImage
        size={
          15
        }
      />
    );
  }


  if (
    file.type.startsWith(
      "video/",
    )
  ) {
    return (
      <FileVideo
        size={
          15
        }
      />
    );
  }


  if (
    file.type.startsWith(
      "audio/",
    )
  ) {
    return (
      <FileAudio
        size={
          15
        }
      />
    );
  }


  return (
    <FileText
      size={
        15
      }
    />
  );
}


function shortContentType(
  value: string,
): string {
  const parts =
    value.split(
      "/",
    );

  const group =
    parts[0] ??
    "";

  const subtype =
    parts[1] ??
    "";

  if (
    !subtype
  ) {
    return value;
  }

  if (
    group ===
    "image"
  ) {
    return "image";
  }

  if (
    group ===
    "video"
  ) {
    return "video";
  }

  if (
    group ===
    "audio"
  ) {
    return "audio";
  }

  const cleanSubtype =
    subtype.split(
      ";",
    )[0] ??
    subtype;

  return cleanSubtype.slice(
    0,
    24,
  );
}


function formatBytes(
  bytes:
    number,
): string {
  if (
    bytes <
    1024
  ) {
    return `${bytes} B`;
  }


  const kilobytes =
    bytes /
    1024;


  if (
    kilobytes <
    1024
  ) {
    return `${kilobytes.toFixed(
      kilobytes >=
      100
        ? 0
        : 1,
    )} KB`;
  }


  const megabytes =
    kilobytes /
    1024;


  if (
    megabytes <
    1024
  ) {
    return `${megabytes.toFixed(
      megabytes >=
      100
        ? 0
        : 1,
    )} MB`;
  }


  const gigabytes =
    megabytes /
    1024;


  return `${gigabytes.toFixed(
    1,
  )} GB`;
}