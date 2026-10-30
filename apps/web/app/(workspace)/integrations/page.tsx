"use client";

import {
  useState,
} from "react";

import {
  Activity,
  Boxes,
  KeyRound,
  Webhook,
} from "lucide-react";

import {
  IntegrationCard,
  type IntegrationCardData,
} from "@/components/integrations/integration-card";

import {
  APIKeyList,
} from "@/components/integrations/api-key-list";

import {
  PageHeader,
} from "@/components/ui/page-header";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  hasPermission,
} from "@/lib/workspace/access";

const integrations: IntegrationCardData[] =
  [
    {
      id: "google-workspace",
      name: "Google Workspace",
      description:
        "Workspace identity and productivity integration.",
      category:
        "Productivity",
      status:
        "available",
    },
    {
      id: "slack",
      name: "Slack",
      description:
        "Team messaging and notification integration.",
      category:
        "Communication",
      status:
        "available",
    },
    {
      id: "microsoft-teams",
      name: "Microsoft Teams",
      description:
        "Microsoft collaboration and messaging integration.",
      category:
        "Communication",
      status:
        "available",
    },
    {
      id: "github",
      name: "GitHub",
      description:
        "Development activity and repository integration.",
      category:
        "Development",
      status:
        "available",
    },
    {
      id: "notion",
      name: "Notion",
      description:
        "Knowledge and documentation integration.",
      category:
        "Knowledge",
      status:
        "available",
    },
    {
      id: "zoom",
      name: "Zoom",
      description:
        "Meeting and conferencing integration.",
      category:
        "Meetings",
      status:
        "available",
    },
  ];

export default function IntegrationsPage() {
  return (
    <WorkspaceRequired>
      <IntegrationsContent />
    </WorkspaceRequired>
  );
}

function IntegrationsContent() {
  const {
    workspaceId,
    effectivePermissions,
    effectiveNavigationView,
  } = useWorkspace();

  const [
    selectedCategory,
    setSelectedCategory,
  ] = useState(
    "All",
  );

  const [
    message,
    setMessage,
  ] = useState<
    string | null
  >(null);

  const canManage =
    hasPermission(
      effectivePermissions,
      "integrations.manage",
      effectiveNavigationView,
    );

  const categories = [
    "All",
    ...Array.from(
      new Set(
        integrations.map(
          (item) =>
            item.category,
        ),
      ),
    ),
  ];

  const visibleIntegrations =
    selectedCategory ===
    "All"
      ? integrations
      : integrations.filter(
          (item) =>
            item.category ===
            selectedCategory,
        );

  function manageIntegration(
    integration: IntegrationCardData,
  ) {
    setMessage(
      `${integration.name} connection UI is ready for its backend connector contract. No fake connection state was created.`,
    );
  }

  return (
    <div
      style={{
        maxWidth: 1500,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Integrations"
        description="Connect WorkforceOS with external services, manage API access, and monitor integration readiness."
      />

      {message ? (
        <div
          role="status"
          style={{
            marginBottom: 16,
            padding: 11,
            border:
              "1px solid var(--color-border)",
            borderRadius: 9,
            background:
              "var(--color-muted)",
            fontSize: 12,
          }}
        >
          {message}
        </div>
      ) : null}

      <section
        className="panel"
        style={{
          marginBottom: 18,
        }}
      >
        <div
          className="panel-body"
          style={{
            display: "grid",
            gap: 14,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <Activity
              size={17}
            />

            <div>
              <strong
                style={{
                  fontSize: 13,
                }}
              >
                Integration Health
              </strong>

              <p
                className="text-label"
                style={{
                  margin:
                    "4px 0 0",
                }}
              >
                API credential management is connected to the workspace backend. Provider OAuth connectors are shown only as integration placeholders until their backend contracts are implemented.
              </p>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(180px, 1fr))",
              gap: 10,
            }}
          >
            <HealthItem
              icon={
                <KeyRound
                  size={16}
                />
              }
              label="API Keys"
              value="Backend Connected"
            />

            <HealthItem
              icon={
                <Webhook
                  size={16}
                />
              }
              label="Webhooks"
              value="Backend Contract Pending"
            />

            <HealthItem
              icon={
                <Boxes
                  size={16}
                />
              }
              label="Provider Apps"
              value="Connector Dependent"
            />
          </div>
        </div>
      </section>

      {workspaceId ? (
        <APIKeyList
          workspaceId={
            workspaceId
          }
          canManage={
            canManage
          }
        />
      ) : null}

      <section
        className="panel"
        style={{
          marginTop: 18,
        }}
      >
        <div
          className="panel-body"
          style={{
            display: "grid",
            gap: 16,
          }}
        >
          <div>
            <h2
              style={{
                margin: 0,
                fontSize: 16,
              }}
            >
              Connected Apps
            </h2>

            <p
              className="text-label"
              style={{
                margin:
                  "5px 0 0",
              }}
            >
              External applications supported by the WorkforceOS integration surface.
            </p>
          </div>

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 7,
            }}
          >
            {categories.map(
              (category) => (
                <button
                  key={category}
                  type="button"
                  onClick={() =>
                    setSelectedCategory(
                      category,
                    )
                  }
                  style={{
                    minHeight: 34,
                    padding:
                      "0 11px",
                    border:
                      "1px solid var(--color-border)",
                    borderRadius: 999,
                    background:
                      selectedCategory ===
                      category
                        ? "var(--color-foreground)"
                        : "var(--color-surface)",
                    color:
                      selectedCategory ===
                      category
                        ? "var(--color-surface)"
                        : "var(--color-foreground)",
                    cursor:
                      "pointer",
                    fontSize: 11,
                    fontWeight: 600,
                  }}
                >
                  {category}
                </button>
              ),
            )}
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(250px, 1fr))",
              gap: 11,
            }}
          >
            {visibleIntegrations.map(
              (integration) => (
                <IntegrationCard
                  key={
                    integration.id
                  }
                  integration={
                    integration
                  }
                  onManage={
                    manageIntegration
                  }
                />
              ),
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function HealthItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 9,
        padding: 12,
        border:
          "1px solid var(--color-border)",
        borderRadius: 9,
      }}
    >
      <span
        style={{
          width: 30,
          height: 30,
          display: "grid",
          placeItems: "center",
          borderRadius: 8,
          background:
            "var(--color-muted)",
        }}
      >
        {icon}
      </span>

      <span>
        <span
          className="text-label"
          style={{
            display: "block",
          }}
        >
          {label}
        </span>

        <strong
          style={{
            display: "block",
            marginTop: 3,
            fontSize: 11,
          }}
        >
          {value}
        </strong>
      </span>
    </div>
  );
}