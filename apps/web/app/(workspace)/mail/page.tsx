"use client";

import { useMemo, useState } from "react";

import {
  Archive,
  Inbox,
  Mail,
  PenSquare,
  Search,
  Send,
  Star,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";

const messages = [
  {
    id: 1,
    sender: "Theresa Webb",
    subject: "Payroll approval required",
    preview: "Please review the May payroll before 3 PM.",
    time: "9:42 AM",
    folder: "inbox",
    unread: true,
  },
  {
    id: 2,
    sender: "Ralph Edwards",
    subject: "Engineering weekly notes",
    preview: "Here are the key action items from today's sync.",
    time: "8:21 AM",
    folder: "inbox",
    unread: false,
  },
  {
    id: 3,
    sender: "Dianne Russell",
    subject: "Marketing campaign review",
    preview: "The Q2 campaign assets are ready for feedback.",
    time: "Yesterday",
    folder: "inbox",
    unread: false,
  },
  {
    id: 4,
    sender: "Marvin McKinney",
    subject: "Design system updates",
    preview: "I've published the latest component changes.",
    time: "Yesterday",
    folder: "starred",
    unread: false,
  },
];

export default function MailPage() {
  const [folder, setFolder] = useState("inbox");
  const [selectedId, setSelectedId] = useState(1);
  const [search, setSearch] = useState("");

  const visible = useMemo(() => {
    return messages.filter((message) => {
      const folderMatch =
        folder === "all" ||
        message.folder === folder ||
        (folder === "inbox" && message.folder === "inbox");

      const searchMatch =
        !search ||
        `${message.sender} ${message.subject} ${message.preview}`
          .toLowerCase()
          .includes(search.toLowerCase());

      return folderMatch && searchMatch;
    });
  }, [folder, search]);

  const selected =
    messages.find(
      (message) => message.id === selectedId,
    ) ?? visible[0];

  return (
    <div
      style={{
        width: "100%",
        maxWidth: 1700,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Mail"
        description="Manage workforce communication from one inbox."
        actions={
          <Button>
            <PenSquare size={15} />
            Compose
          </Button>
        }
      />

      <div
        style={{
          display: "grid",
          minHeight: 700,
          gridTemplateColumns:
            "210px 390px minmax(0,1fr)",
          gap: 14,
        }}
      >
        <aside className="panel">
          <div className="panel-body">
            <Button
              style={{
                width: "100%",
                marginBottom: 14,
              }}
            >
              <PenSquare size={15} />
              New Message
            </Button>

            <MailFolder
              active={folder === "inbox"}
              icon={<Inbox size={16} />}
              label="Inbox"
              count={24}
              onClick={() => setFolder("inbox")}
            />

            <MailFolder
              active={folder === "starred"}
              icon={<Star size={16} />}
              label="Starred"
              count={4}
              onClick={() => setFolder("starred")}
            />

            <MailFolder
              active={folder === "sent"}
              icon={<Send size={16} />}
              label="Sent"
              count={0}
              onClick={() => setFolder("sent")}
            />

            <MailFolder
              active={folder === "archive"}
              icon={<Archive size={16} />}
              label="Archive"
              count={0}
              onClick={() => setFolder("archive")}
            />

            <MailFolder
              active={folder === "trash"}
              icon={<Trash2 size={16} />}
              label="Trash"
              count={0}
              onClick={() => setFolder("trash")}
            />
          </div>
        </aside>

        <section
          className="panel"
          style={{
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: 12,
              borderBottom:
                "1px solid var(--color-border-subtle)",
            }}
          >
            <div className="input-group">
              <Search
                size={15}
                className="input-group__icon"
              />

              <input
                className="input"
                value={search}
                placeholder="Search mail"
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />
            </div>
          </div>

          <div
            style={{
              overflowY: "auto",
              maxHeight: 650,
            }}
          >
            {visible.map((message) => (
              <button
                key={message.id}
                type="button"
                onClick={() =>
                  setSelectedId(message.id)
                }
                style={{
                  display: "block",
                  width: "100%",
                  padding: 15,
                  border: 0,
                  borderBottom:
                    "1px solid var(--color-border-subtle)",
                  background:
                    selected?.id === message.id
                      ? "var(--color-surface-selected)"
                      : message.unread
                        ? "#fffdf7"
                        : "transparent",
                  textAlign: "left",
                  cursor: "pointer",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                  }}
                >
                  <strong
                    style={{
                      fontSize: 12,
                    }}
                  >
                    {message.sender}
                  </strong>

                  <span className="text-label">
                    {message.time}
                  </span>
                </div>

                <div
                  style={{
                    marginTop: 6,
                    fontSize: 12,
                    fontWeight: message.unread
                      ? 600
                      : 500,
                  }}
                >
                  {message.subject}
                </div>

                <p
                  style={{
                    marginTop: 4,
                    overflow: "hidden",
                    color:
                      "var(--color-text-muted)",
                    fontSize: 11,
                    whiteSpace: "nowrap",
                    textOverflow: "ellipsis",
                  }}
                >
                  {message.preview}
                </p>
              </button>
            ))}
          </div>
        </section>

        <section className="panel">
          {selected ? (
            <>
              <div className="panel-header">
                <div>
                  <h2 className="text-section-title">
                    {selected.subject}
                  </h2>

                  <div className="text-label">
                    {selected.sender} · {selected.time}
                  </div>
                </div>
              </div>

              <div
                className="panel-body"
                style={{
                  minHeight: 520,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    marginBottom: 24,
                  }}
                >
                  <div className="avatar avatar--lg">
                    {selected.sender.slice(0, 1)}
                  </div>

                  <div>
                    <strong
                      style={{
                        fontSize: 12,
                      }}
                    >
                      {selected.sender}
                    </strong>

                    <div className="text-label">
                      to you
                    </div>
                  </div>
                </div>

                <p
                  style={{
                    maxWidth: 760,
                    color: "#45494d",
                    fontSize: 13,
                    lineHeight: 1.8,
                  }}
                >
                  {selected.preview}
                  <br />
                  <br />
                  This is a frontend preview of the message
                  experience. Once the backend communication
                  endpoints are connected, the full message body,
                  attachments, recipients, threads and actions will
                  come from the real API.
                </p>
              </div>

              <div
                className="panel-footer"
                style={{
                  justifyContent: "flex-start",
                }}
              >
                <Button>
                  Reply
                </Button>

                <Button variant="outline">
                  Forward
                </Button>
              </div>
            </>
          ) : null}
        </section>
      </div>
    </div>
  );
}

function MailFolder({
  active,
  icon,
  label,
  count,
  onClick,
}: {
  active: boolean;
  icon: React.ReactNode;
  label: string;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: "flex",
        width: "100%",
        height: 38,
        alignItems: "center",
        gap: 10,
        padding: "0 10px",
        marginBottom: 3,
        border: 0,
        borderRadius: 7,
        background: active
          ? "var(--color-nav-active)"
          : "transparent",
        color: active
          ? "#fff"
          : "#55595d",
        cursor: "pointer",
      }}
    >
      {icon}

      <span
        style={{
          flex: 1,
          textAlign: "left",
          fontSize: 12,
        }}
      >
        {label}
      </span>

      {count > 0 ? (
        <span
          style={{
            fontSize: 10,
          }}
        >
          {count}
        </span>
      ) : null}
    </button>
  );
}