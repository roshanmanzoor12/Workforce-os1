import {
  ChevronRight,
  ClipboardList,
  Clock3,
  RefreshCw,
  Users,
} from "lucide-react";

interface BottomStatusBarProps {
  systemOperational?: boolean;
  lastSyncedLabel?: string | null;
  activeSessions?: number | null;
  serverTimeLabel?: string | null;
  summaryLabel?: string | null;
}

export function BottomStatusBar({
  systemOperational = true,
  lastSyncedLabel,
  activeSessions,
  serverTimeLabel,
  summaryLabel,
}: BottomStatusBarProps) {
  return (
    <footer
      aria-label="Workspace status"
      style={{
        position: "sticky",
        bottom: 0,
        zIndex: "var(--z-sticky)",
        padding: "10px 14px 12px",
        background:
          "linear-gradient(180deg, rgba(250,248,243,0) 0%, rgba(250,248,243,0.95) 18%, #f6f0e3 100%)",
      }}
    >
      <div
        style={{
          display: "grid",
          minHeight: 62,
          gridTemplateColumns:
            "1.05fr 1.1fr 1fr 1.1fr 1.25fr",
          overflow: "hidden",
          border: "1px solid var(--color-border)",
          borderRadius: 11,
          background: "#fffefa",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "0 18px",
          }}
        >
          <span
            style={{
              display: "grid",
              width: 34,
              height: 34,
              flex: "0 0 auto",
              placeItems: "center",
              borderRadius: "50%",
              background: systemOperational
                ? "#eef7e6"
                : "#fdebea",
            }}
          >
            <span
              style={{
                width: 13,
                height: 13,
                borderRadius: "50%",
                background: systemOperational
                  ? "#66b93f"
                  : "#e64b45",
                boxShadow: systemOperational
                  ? "0 0 0 5px rgba(102,185,63,0.10)"
                  : "0 0 0 5px rgba(230,75,69,0.10)",
              }}
            />
          </span>

          <span>
            <span
              style={{
                display: "block",
                color: "#323538",
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              Workspace Status
            </span>

            <span
              style={{
                display: "block",
                marginTop: 3,
                color: systemOperational
                  ? "#54a432"
                  : "#c53631",
                fontSize: 10,
              }}
            >
              {systemOperational
                ? "All Systems Operational"
                : "Service Attention Required"}
            </span>
          </span>
        </div>

        <StatusCell
          icon={<RefreshCw size={20} strokeWidth={1.7} />}
          title="Data Sync"
          value={
            lastSyncedLabel ||
            "Waiting for sync status"
          }
        />

        <StatusCell
          icon={<Users size={20} strokeWidth={1.7} />}
          title="Active Sessions"
          value={
            typeof activeSessions === "number"
              ? `${activeSessions} Active`
              : "Waiting for session data"
          }
        />

        <StatusCell
          icon={<Clock3 size={20} strokeWidth={1.7} />}
          title="Server Time"
          value={
            serverTimeLabel ||
            "Waiting for server time"
          }
        />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "0 18px",
            borderLeft:
              "1px solid var(--color-border)",
          }}
        >
          <ClipboardList
            size={21}
            strokeWidth={1.7}
            style={{
              flex: "0 0 auto",
              color: "#34373a",
            }}
          />

          <span
            style={{
              minWidth: 0,
              flex: 1,
            }}
          >
            <span
              style={{
                display: "block",
                color: "#323538",
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              Today&apos;s Summary
            </span>

            <span
              style={{
                display: "block",
                marginTop: 3,
                overflow: "hidden",
                color: "#85888d",
                fontSize: 10,
                whiteSpace: "nowrap",
                textOverflow: "ellipsis",
              }}
            >
              {summaryLabel ||
                "No summary data available"}
            </span>
          </span>

          <ChevronRight
            size={17}
            strokeWidth={1.7}
            color="#55595d"
          />
        </div>
      </div>
    </footer>
  );
}

interface StatusCellProps {
  icon: React.ReactNode;
  title: string;
  value: string;
}

function StatusCell({
  icon,
  title,
  value,
}: StatusCellProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "0 18px",
        borderLeft:
          "1px solid var(--color-border)",
      }}
    >
      <span
        style={{
          flex: "0 0 auto",
          color: "#34373a",
        }}
      >
        {icon}
      </span>

      <span
        style={{
          minWidth: 0,
        }}
      >
        <span
          style={{
            display: "block",
            color: "#323538",
            fontSize: 11,
            fontWeight: 600,
          }}
        >
          {title}
        </span>

        <span
          style={{
            display: "block",
            marginTop: 3,
            overflow: "hidden",
            color: "#85888d",
            fontSize: 10,
            whiteSpace: "nowrap",
            textOverflow: "ellipsis",
          }}
        >
          {value}
        </span>
      </span>
    </div>
  );
}