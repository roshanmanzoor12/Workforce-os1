"use client";

import {
  Send,
} from "lucide-react";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  ChannelAttachmentPicker,
} from "@/components/channels/channel-attachment-picker";

import {
  ChannelMessageItem,
} from "@/components/channels/channel-message-item";

import {
  attachmentsService,
} from "@/services/attachments.service";

import {
  workspaceChannelsService,
  type WorkspaceChannelMessagePublic,
  type WorkspaceChannelPublic,
} from "@/services/workspace-channels.service";


interface TextChannelRoomProps {
  channel:
    WorkspaceChannelPublic;

  currentUserId:
    string | null;

  onSettings?:
    () => void;
}


export function TextChannelRoom({
  channel,

  currentUserId,

  onSettings,
}: TextChannelRoomProps) {
  const [
    messages,
    setMessages,
  ] =
    useState<WorkspaceChannelMessagePublic[]>(
      [],
    );


  const [
    content,
    setContent,
  ] =
    useState(
      "",
    );


  const [
    files,
    setFiles,
  ] =
    useState<File[]>(
      [],
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    sending,
    setSending,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const bottomRef =
    useRef<HTMLDivElement | null>(
      null,
    );


  const load =
    useCallback(
      async (
        showLoading =
          false,
      ) => {
        if (
          showLoading
        ) {
          setLoading(
            true,
          );
        }


        try {
          const result =
            await workspaceChannelsService.listMessages(
              channel.id,
              100,
            );


          setMessages(
            result,
          );


          setError(
            null,
          );

        } catch (
          cause
        ) {
          if (
            showLoading
          ) {
            setError(
              cause instanceof Error
                ? cause.message
                : "Unable to load channel messages.",
            );
          }

        } finally {
          if (
            showLoading
          ) {
            setLoading(
              false,
            );
          }
        }
      },
      [
        channel.id,
      ],
    );


  useEffect(
    () => {
      setMessages(
        [],
      );


      setContent(
        "",
      );


      setFiles(
        [],
      );


      void load(
        true,
      );
    },
    [
      load,
    ],
  );


  useEffect(
    () => {
      bottomRef.current?.scrollIntoView(
        {
          behavior:
            "smooth",
        },
      );
    },
    [
      messages.length,
    ],
  );


  async function uploadFiles():
    Promise<string[]> {
    if (
      files.length ===
      0
    ) {
      return [];
    }


    if (
      files.length >
      10
    ) {
      throw new Error(
        "A message can contain at most 10 attachments.",
      );
    }


    const uploadedIds:
      string[] =
      [];


    try {
      for (
        const file
        of files
      ) {
        const result =
          await attachmentsService.uploadChannelFile(
            channel.id,
            file,
          );


        uploadedIds.push(
          result.attachment_id,
        );
      }


      return uploadedIds;

    } catch (
      cause
    ) {
      await Promise.allSettled(
        uploadedIds.map(
          (
            attachmentId,
          ) =>
            attachmentsService.remove(
              attachmentId,
            ),
        ),
      );


      throw cause;
    }
  }


  async function send(
    event?:
      FormEvent<HTMLFormElement>,
  ) {
    event?.preventDefault();


    if (
      sending
    ) {
      return;
    }


    const text =
      content.trim();


    if (
      !text &&
      files.length ===
        0
    ) {
      return;
    }


    let uploadedIds:
      string[] =
      [];


    let createdMessageId:
      string | null =
      null;


    try {
      setSending(
        true,
      );


      setError(
        null,
      );


      uploadedIds =
        await uploadFiles();


      /*
       * The current backend MessageCreateRequest
       * requires non-empty content.
       *
       * For attachment-only sends, keep a visible
       * compact label instead of inventing an empty
       * message payload.
       */
      const created =
        await workspaceChannelsService.sendMessage(
          channel.id,
          {
            content:
              text ||
              "Attachment",
          },
        );


      createdMessageId =
        created.id;


      setMessages(
        (
          current,
        ) => [
          ...current.filter(
            (
              item,
            ) =>
              item.id !==
              created.id,
          ),

          created,
        ],
      );


      if (
        uploadedIds.length >
        0
      ) {
        await attachmentsService.bindChannelAttachments(
          channel.id,
          created.id,
          uploadedIds,
        );
      }


      setContent(
        "",
      );


      setFiles(
        [],
      );


      /*
       * Refresh after binding so attachment
       * components receive the completed relation.
       */
      await load(
        false,
      );

    } catch (
      cause
    ) {
      /*
       * If the actual message was never created,
       * all uploaded files are still unbound and
       * can be cleaned up safely.
       *
       * If the message already exists but binding
       * failed, keep the message visible rather than
       * pretending the entire send failed.
       */
      if (
        !createdMessageId &&
        uploadedIds.length >
          0
      ) {
        await Promise.allSettled(
          uploadedIds.map(
            (
              attachmentId,
            ) =>
              attachmentsService.remove(
                attachmentId,
              ),
          ),
        );
      }


      setError(
        createdMessageId
          ? "Message sent, but its attachments could not be attached."
          : cause instanceof Error
            ? cause.message
            : "Unable to send channel message.",
      );

    } finally {
      setSending(
        false,
      );
    }
  }


  return (
    <section
      style={{
        minWidth:
          0,

        flex:
          1,

        display:
          "grid",

        gridTemplateRows:
          "auto minmax(0,1fr) auto",

        minHeight:
          680,
      }}
    >
      <header
        style={{
          display:
            "flex",

          alignItems:
            "center",

          justifyContent:
            "space-between",

          gap:
            10,

          padding:
            "10px 13px",

          borderBottom:
            "1px solid var(--color-border)",
        }}
      >
        <div>
          <strong>
            {channel.channel_type ===
            "announcement"
              ? channel.name
              : `# ${channel.name}`}
          </strong>


          <div
            className="text-label"
            style={{
              marginTop:
                3,
            }}
          >
            #{channel.slug}
          </div>
        </div>


        {onSettings ? (
          <button
            type="button"
            className="button button--outline"
            onClick={
              onSettings
            }
          >
            Channel
          </button>
        ) : null}
      </header>


      <div
        style={{
          minHeight:
            0,

          overflowY:
            "auto",

          padding:
            14,
        }}
      >
        {loading ? (
          <div
            className="skeleton"
            style={{
              height:
                300,
            }}
          />
        ) : null}


        {error ? (
          <div
            style={{
              marginBottom:
                12,

              padding:
                "9px 10px",

              border:
                "1px solid #efc6c6",

              borderRadius:
                7,

              background:
                "#fff1f1",

              color:
                "#b52b2b",

              fontSize:
                9,
            }}
          >
            {error}
          </div>
        ) : null}


        {!loading &&
        messages.length ===
          0 ? (
          <div
            style={{
              display:
                "grid",

              minHeight:
                470,

              placeItems:
                "center",

              textAlign:
                "center",

              color:
                "#777",
            }}
          >
            <div>
              <strong>
                Welcome to #{channel.name}
              </strong>


              <div
                className="text-label"
                style={{
                  marginTop:
                    5,
                }}
              >
                This is the beginning of this channel.
              </div>
            </div>
          </div>
        ) : null}


        <div
          style={{
            display:
              "grid",

            gap:
              10,
          }}
        >
          {messages.map(
            (
              message,
            ) => (
              <ChannelMessageItem
                key={
                  message.id
                }
                channelId={
                  channel.id
                }
                message={
                  message
                }
                currentUserId={
                  currentUserId
                }
              />
            ),
          )}
        </div>


        <div
          ref={
            bottomRef
          }
        />
      </div>


      <form
        onSubmit={
          send
        }
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "auto minmax(0,1fr) auto",

          alignItems:
            "end",

          gap:
            8,

          padding:
            10,

          borderTop:
            "1px solid var(--color-border)",

          background:
            "#f7f4ee",
        }}
      >
        <ChannelAttachmentPicker
          files={
            files
          }
          disabled={
            sending
          }
          onChange={
            setFiles
          }
        />


        <textarea
          value={
            content
          }
          rows={
            2
          }
          maxLength={
            10000
          }
          disabled={
            sending
          }
          placeholder={
            channel.channel_type ===
            "announcement"
              ? `Post in ${channel.name}`
              : `Message #${channel.name}`
          }
          onChange={(
            event,
          ) =>
            setContent(
              event.target.value,
            )
          }
          onKeyDown={(
            event,
          ) => {
            if (
              event.key ===
                "Enter" &&
              !event.shiftKey
            ) {
              event.preventDefault();


              event.currentTarget.form?.requestSubmit();
            }
          }}
          style={{
            minHeight:
              44,

            maxHeight:
              150,

            padding:
              10,

            border:
              "1px solid var(--color-border)",

            borderRadius:
              7,

            resize:
              "vertical",

            outline:
              "none",

            background:
              "#fffefa",

            fontFamily:
              "inherit",

            fontSize:
              10,
          }}
        />


        <button
          type="submit"
          className="button button--primary"
          disabled={
            sending ||
            (
              !content.trim() &&
              files.length ===
                0
            )
          }
        >
          <Send
            size={
              14
            }
          />

          {sending
            ? "Sending..."
            : "Send"}
        </button>
      </form>
    </section>
  );
}
