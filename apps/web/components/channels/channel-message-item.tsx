"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  ChannelAttachmentList,
} from "@/components/channels/channel-attachment-list";

import {
  subscribeToChannelAttachmentBound,
} from "@/lib/realtime/channel-attachment-events";

import {
  attachmentsService,
} from "@/services/attachments.service";

import type {
  BoundAttachment,
} from "@/types/attachments";

import type {
  WorkspaceChannelMessage,
} from "@/types/channels";


interface ChannelMessageItemProps {
  channelId: string;

  message:
    WorkspaceChannelMessage;

  currentUserId?:
    | string
    | null;
}


export function ChannelMessageItem({
  channelId,

  message,

  currentUserId = null,
}: ChannelMessageItemProps) {
  const [
    attachments,
    setAttachments,
  ] =
    useState<
      BoundAttachment[]
    >(
      [],
    );


  const [
    attachmentsLoading,
    setAttachmentsLoading,
  ] =
    useState(
      true,
    );


  const [
    attachmentsRefreshing,
    setAttachmentsRefreshing,
  ] =
    useState(
      false,
    );


  const mountedRef =
    useRef(
      true,
    );


  const requestVersionRef =
    useRef(
      0,
    );


  useEffect(
    () => {
      mountedRef.current =
        true;


      return () => {
        mountedRef.current =
          false;
      };
    },
    [],
  );


  const loadAttachments =
    useCallback(
      async (
        background = false,
      ) => {
        const requestVersion =
          requestVersionRef.current +
          1;


        requestVersionRef.current =
          requestVersion;


        if (
          background
        ) {
          setAttachmentsRefreshing(
            true,
          );
        } else {
          setAttachmentsLoading(
            true,
          );
        }


        try {
          const result =
            await attachmentsService
              .listChannelAttachments(
                channelId,
                message.id,
              );


          if (
            !mountedRef.current ||
            requestVersion !==
              requestVersionRef.current
          ) {
            return;
          }


          setAttachments(
            result.attachments ??
              [],
          );

        } catch {
          /*
           * Initial attachment loading may fail without
           * preventing the message itself from rendering.
           *
           * Background realtime refresh failures retain
           * the last successfully loaded attachment state.
           */
          if (
            !background &&
            mountedRef.current &&
            requestVersion ===
              requestVersionRef.current
          ) {
            setAttachments(
              [],
            );
          }

        } finally {
          if (
            !mountedRef.current ||
            requestVersion !==
              requestVersionRef.current
          ) {
            return;
          }


          if (
            background
          ) {
            setAttachmentsRefreshing(
              false,
            );
          } else {
            setAttachmentsLoading(
              false,
            );
          }
        }
      },
      [
        channelId,
        message.id,
      ],
    );


  useEffect(
    () => {
      void loadAttachments(
        false,
      );
    },
    [
      loadAttachments,
    ],
  );


  useEffect(
    () => {
      return (
        subscribeToChannelAttachmentBound(
          (
            payload,
          ) => {
            if (
              payload.channel_id !==
              channelId
            ) {
              return;
            }


            if (
              payload.message_id !==
              message.id
            ) {
              return;
            }


            void loadAttachments(
              true,
            );
          },
        )
      );
    },
    [
      channelId,
      loadAttachments,
      message.id,
    ],
  );


  const createdAt =
    new Date(
      message.created_at,
    );


  const createdLabel =
    Number.isNaN(
      createdAt.getTime(),
    )
      ? message.created_at
      : createdAt
          .toLocaleString();


  const isCurrentUser =
    Boolean(
      currentUserId &&
      message.sender_user_id ===
        currentUserId,
    );


  return (
    <article
      data-own-message={
        isCurrentUser
          ? "true"
          : "false"
      }
      style={{
        padding:
          "4px 0",
      }}
    >
      <div
        style={{
          display:
            "flex",

          gap:
            8,

          alignItems:
            "baseline",
        }}
      >
        <strong>
          {isCurrentUser
            ? "You"
            : message.sender_user_id
              ? message
                  .sender_user_id
                  .slice(
                    0,
                    8,
                  )
              : "System"}
        </strong>


        <small
          style={{
            opacity:
              0.55,
          }}
        >
          {createdLabel}
        </small>
      </div>


      {message.deleted_at ? (
        <div
          style={{
            marginTop:
              3,

            opacity:
              0.55,

            fontStyle:
              "italic",
          }}
        >
          Message deleted
        </div>
      ) : (
        <>
          <div
            style={{
              marginTop:
                3,

              whiteSpace:
                "pre-wrap",

              overflowWrap:
                "anywhere",
            }}
          >
            {message.content}
          </div>


          {attachmentsLoading ? (
            <div
              style={{
                marginTop:
                  7,

                fontSize:
                  11,

                opacity:
                  0.5,
              }}
            >
              Loading attachments…
            </div>
          ) : (
            <>
              <ChannelAttachmentList
                attachments={
                  attachments
                }
              />


              {attachmentsRefreshing ? (
                <span
                  aria-live="polite"
                  style={{
                    position:
                      "absolute",

                    width:
                      1,

                    height:
                      1,

                    padding:
                      0,

                    margin:
                      -1,

                    overflow:
                      "hidden",

                    clip:
                      "rect(0, 0, 0, 0)",

                    whiteSpace:
                      "nowrap",

                    border:
                      0,
                  }}
                >
                  Refreshing attachments
                </span>
              ) : null}
            </>
          )}


          {message.edited_at ? (
            <div
              style={{
                marginTop:
                  3,

                fontSize:
                  11,

                opacity:
                  0.5,
              }}
            >
              Edited
            </div>
          ) : null}
        </>
      )}
    </article>
  );
}