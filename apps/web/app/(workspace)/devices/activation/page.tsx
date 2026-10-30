"use client";

import {
  Check,
  Copy,
  KeyRound,
  Plus,
  RefreshCcw,
  ShieldCheck,
  Trash2,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  hasPermission,
} from "@/lib/workspace/access";

import {
  deviceManagementService,
} from "@/services/device-management.service";

import type {
  DeviceActivationCodePublic,
} from "@/types/device-management";


function formatDate(
  value:
    string | null,
): string {
  if (
    !value
  ) {
    return "No expiry";
  }


  const date =
    new Date(
      value,
    );


  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }


  return date.toLocaleString();
}


export default function DeviceActivationPage() {
  const {
    workspaceId,

    workspace,

    navigationView,

    permissions,
  } =
    useWorkspace();


  const [
    activationCodes,
    setActivationCodes,
  ] =
    useState<DeviceActivationCodePublic[]>(
      [],
    );


  const [
    label,
    setLabel,
  ] =
    useState(
      "",
    );


  const [
    maxUses,
    setMaxUses,
  ] =
    useState(
      "1",
    );


  const [
    expiresAt,
    setExpiresAt,
  ] =
    useState(
      "",
    );


  const [
    latestSecret,
    setLatestSecret,
  ] =
    useState<string | null>(
      null,
    );


  const [
    copied,
    setCopied,
  ] =
    useState(
      false,
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    creating,
    setCreating,
  ] =
    useState(
      false,
    );


  const [
    actionId,
    setActionId,
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


  const [
    success,
    setSuccess,
  ] =
    useState<string | null>(
      null,
    );


  const canManageDevices =
    navigationView ===
      "owner" ||
    navigationView ===
      "admin" ||
    hasPermission(
      permissions,
      "devices.manage",
      navigationView,
    );


  const activeCount =
    useMemo(
      () =>
        activationCodes.filter(
          (item) =>
            item.status ===
              "active" &&
            item.is_active,
        ).length,
      [
        activationCodes,
      ],
    );


  const load =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          setLoading(
            false,
          );

          return;
        }


        try {
          setLoading(
            true,
          );


          setError(
            null,
          );


          const response =
            await deviceManagementService.listActivationCodes(
              workspaceId,
              true,
            );


          setActivationCodes(
            response.activation_codes,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load activation codes.",
          );

        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
      ],
    );


  useEffect(
    () => {
      void load();
    },
    [
      load,
    ],
  );


  async function createCode() {
    if (
      !workspaceId ||
      !canManageDevices ||
      creating
    ) {
      return;
    }


    const parsedUses =
      maxUses.trim()
        ? Number(
            maxUses,
          )
        : null;


    if (
      parsedUses !==
        null &&
      (
        !Number.isInteger(
          parsedUses,
        ) ||
        parsedUses <=
          0
      )
    ) {
      setError(
        "Maximum uses must be a positive whole number.",
      );

      return;
    }


    let expiration:
      string | null =
        null;


    if (
      expiresAt
    ) {
      const date =
        new Date(
          expiresAt,
        );


      if (
        Number.isNaN(
          date.getTime(),
        )
      ) {
        setError(
          "Expiration date is invalid.",
        );

        return;
      }


      expiration =
        date.toISOString();
    }


    try {
      setCreating(
        true,
      );


      setError(
        null,
      );


      setSuccess(
        null,
      );


      setLatestSecret(
        null,
      );


      const response =
        await deviceManagementService.createActivationCode(
          workspaceId,
          {
            label:
              label.trim() ||
              null,

            expires_at:
              expiration,

            max_uses:
              parsedUses,
          },
        );


      setActivationCodes(
        (current) => [
          response.activation,
          ...current.filter(
            (item) =>
              item.id !==
              response.activation.id,
          ),
        ],
      );


      setLatestSecret(
        response.activation_code,
      );


      setLabel(
        "",
      );


      setMaxUses(
        "1",
      );


      setExpiresAt(
        "",
      );


      setSuccess(
        "Device activation code created. Copy it now because the full secret is only returned at creation.",
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create activation code.",
      );

    } finally {
      setCreating(
        false,
      );
    }
  }


  async function revokeCode(
    activation:
      DeviceActivationCodePublic,
  ) {
    if (
      !workspaceId ||
      !canManageDevices ||
      actionId
    ) {
      return;
    }


    const confirmed =
      window.confirm(
        "Revoke this device activation code?",
      );


    if (
      !confirmed
    ) {
      return;
    }


    try {
      setActionId(
        activation.id,
      );


      setError(
        null,
      );


      await deviceManagementService.revokeActivationCode(
        workspaceId,
        activation.id,
      );


      setActivationCodes(
        (current) =>
          current.map(
            (item) =>
              item.id ===
              activation.id
                ? {
                    ...item,

                    status:
                      "revoked",

                    is_active:
                      false,

                    revoked_at:
                      new Date().toISOString(),
                  }
                : item,
          ),
      );


      setSuccess(
        "Activation code revoked.",
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to revoke activation code.",
      );

    } finally {
      setActionId(
        null,
      );
    }
  }


  async function copySecret() {
    if (
      !latestSecret
    ) {
      return;
    }


    try {
      await navigator.clipboard.writeText(
        latestSecret,
      );


      setCopied(
        true,
      );


      window.setTimeout(
        () => {
          setCopied(
            false,
          );
        },
        1200,
      );

    } catch {
      setError(
        "Unable to copy activation code.",
      );
    }
  }


  return (
    <WorkspaceRequired>
      <div
        style={{
          display:
            "grid",

          gap:
            16,
        }}
      >
        <div
          style={{
            display:
              "flex",

            alignItems:
              "flex-start",

            justifyContent:
              "space-between",

            gap:
              16,
          }}
        >
          <div>
            <div
              style={{
                display:
                  "flex",

                alignItems:
                  "center",

                gap:
                  6,

                color:
                  "#9a7000",

                fontSize:
                  10,

                fontWeight:
                  600,
              }}
            >
              <KeyRound
                size={
                  13
                }
              />

              Endpoint Enrollment
            </div>


            <h1
              style={{
                marginTop:
                  5,
              }}
            >
              Device Activation
            </h1>


            <p
              className="text-label"
              style={{
                marginTop:
                  4,
              }}
            >
              Generate enrollment codes for Workforce OS Agent devices in{" "}
              {workspace?.name ??
                "this workspace"}.
            </p>
          </div>


          <button
            type="button"
            className="button button--outline"
            onClick={() => {
              void load();
            }}
          >
            <RefreshCcw
              size={
                14
              }
            />

            Refresh
          </button>
        </div>


        {error ? (
          <div
            style={errorStyle}
          >
            {error}
          </div>
        ) : null}


        {success ? (
          <div
            style={successStyle}
          >
            {success}
          </div>
        ) : null}


        {latestSecret ? (
          <section
            className="panel"
            style={{
              border:
                "1px solid #e6c25a",
            }}
          >
            <div
              className="panel-body"
              style={{
                display:
                  "grid",

                gap:
                  10,

                padding:
                  14,
              }}
            >
              <strong
                style={{
                  display:
                    "flex",

                  alignItems:
                    "center",

                  gap:
                    7,
                }}
              >
                <ShieldCheck
                  size={
                    14
                  }
                />

                New Activation Code
              </strong>


              <p
                className="text-label"
              >
                Store or send this code securely. The complete secret will not be retrievable later.
              </p>


              <div
                style={{
                  display:
                    "flex",

                  alignItems:
                    "center",

                  gap:
                    8,
                }}
              >
                <code
                  style={{
                    flex:
                      1,

                    padding:
                      "11px 12px",

                    border:
                      "1px solid var(--color-border)",

                    borderRadius:
                      7,

                    background:
                      "#f7f4ee",

                    fontSize:
                      11,

                    wordBreak:
                      "break-all",
                  }}
                >
                  {
                    latestSecret
                  }
                </code>


                <button
                  type="button"
                  className="button button--primary"
                  onClick={() => {
                    void copySecret();
                  }}
                >
                  {copied ? (
                    <Check
                      size={
                        13
                      }
                    />
                  ) : (
                    <Copy
                      size={
                        13
                      }
                    />
                  )}

                  {copied
                    ? "Copied"
                    : "Copy"}
                </button>
              </div>
            </div>
          </section>
        ) : null}


        {canManageDevices ? (
          <section
            className="panel"
          >
            <div
              style={{
                padding:
                  "11px 14px",

                borderBottom:
                  "1px solid var(--color-border)",
              }}
            >
              <strong>
                Create Activation Code
              </strong>

              <p
                className="text-label"
                style={{
                  marginTop:
                    3,
                }}
              >
                The desktop agent uses this code during first-time device registration.
              </p>
            </div>


            <div
              className="panel-body"
              style={{
                display:
                  "grid",

                gridTemplateColumns:
                  "minmax(220px, 1fr) 160px 220px auto",

                gap:
                  10,

                alignItems:
                  "end",

                padding:
                  14,
              }}
            >
              <label
                style={labelStyle}
              >
                Label

                <input
                  value={
                    label
                  }
                  placeholder="Example: September onboarding"
                  onChange={(
                    event,
                  ) =>
                    setLabel(
                      event.target.value,
                    )
                  }
                  style={inputStyle}
                />
              </label>


              <label
                style={labelStyle}
              >
                Max Uses

                <input
                  type="number"
                  min={
                    1
                  }
                  value={
                    maxUses
                  }
                  onChange={(
                    event,
                  ) =>
                    setMaxUses(
                      event.target.value,
                    )
                  }
                  style={inputStyle}
                />
              </label>


              <label
                style={labelStyle}
              >
                Expires At

                <input
                  type="datetime-local"
                  value={
                    expiresAt
                  }
                  onChange={(
                    event,
                  ) =>
                    setExpiresAt(
                      event.target.value,
                    )
                  }
                  style={inputStyle}
                />
              </label>


              <button
                type="button"
                className="button button--primary"
                disabled={
                  creating
                }
                onClick={() => {
                  void createCode();
                }}
              >
                <Plus
                  size={
                    14
                  }
                />

                {creating
                  ? "Creating..."
                  : "Create Code"}
              </button>
            </div>
          </section>
        ) : null}


        <section
          className="panel"
        >
          <div
            style={{
              display:
                "flex",

              alignItems:
                "center",

              justifyContent:
                "space-between",

              padding:
                "11px 14px",

              borderBottom:
                "1px solid var(--color-border)",
            }}
          >
            <div>
              <strong>
                Activation Codes
              </strong>

              <div
                className="text-label"
                style={{
                  marginTop:
                    2,
                }}
              >
                {activeCount} active · {activationCodes.length} total
              </div>
            </div>
          </div>


          {loading ? (
            <div
              className="skeleton"
              style={{
                height:
                  220,

                margin:
                  14,
              }}
            />
          ) : activationCodes.length ===
            0 ? (
            <div
              style={{
                padding:
                  34,

                textAlign:
                  "center",

                color:
                  "#7a7d80",

                fontSize:
                  10,
              }}
            >
              No activation codes created yet.
            </div>
          ) : (
            <div
              style={{
                overflowX:
                  "auto",
              }}
            >
              <table
                style={{
                  width:
                    "100%",

                  borderCollapse:
                    "collapse",

                  fontSize:
                    9,
                }}
              >
                <thead>
                  <tr>
                    <Th>
                      Label
                    </Th>

                    <Th>
                      Prefix
                    </Th>

                    <Th>
                      Status
                    </Th>

                    <Th>
                      Uses
                    </Th>

                    <Th>
                      Expires
                    </Th>

                    <Th>
                      Created
                    </Th>

                    <Th>
                      Actions
                    </Th>
                  </tr>
                </thead>


                <tbody>
                  {activationCodes.map(
                    (
                      activation,
                    ) => (
                      <tr
                        key={
                          activation.id
                        }
                      >
                        <Td>
                          {activation.label ??
                            "Unlabelled"}
                        </Td>

                        <Td>
                          <code>
                            {activation.code_prefix ??
                              "—"}
                          </code>
                        </Td>

                        <Td>
                          <StatusPill
                            status={
                              activation.status
                            }
                          />
                        </Td>

                        <Td>
                          {activation.used_count}
                          {" / "}
                          {activation.max_uses ??
                            "∞"}
                        </Td>

                        <Td>
                          {formatDate(
                            activation.expires_at,
                          )}
                        </Td>

                        <Td>
                          {formatDate(
                            activation.created_at,
                          )}
                        </Td>

                        <Td>
                          {canManageDevices &&
                          activation.status ===
                            "active" ? (
                            <button
                              type="button"
                              className="button button--outline"
                              disabled={
                                actionId ===
                                activation.id
                              }
                              onClick={() => {
                                void revokeCode(
                                  activation,
                                );
                              }}
                              style={{
                                color:
                                  "#b32e2e",
                              }}
                            >
                              <Trash2
                                size={
                                  12
                                }
                              />

                              Revoke
                            </button>
                          ) : (
                            "—"
                          )}
                        </Td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </WorkspaceRequired>
  );
}


function StatusPill({
  status,
}: {
  status:
    string;
}) {
  const active =
    status ===
    "active";


  return (
    <span
      style={{
        display:
          "inline-block",

        padding:
          "3px 6px",

        borderRadius:
          999,

        background:
          active
            ? "#edf8e9"
            : "#f0efec",

        color:
          active
            ? "#34732a"
            : "#686a6c",

        textTransform:
          "capitalize",
      }}
    >
      {status}
    </span>
  );
}


function Th({
  children,
}: {
  children:
    React.ReactNode;
}) {
  return (
    <th
      style={{
        padding:
          "9px 11px",

        borderBottom:
          "1px solid var(--color-border)",

        background:
          "#f7f4ee",

        color:
          "#6c6e70",

        fontSize:
          8,

        textAlign:
          "left",
      }}
    >
      {children}
    </th>
  );
}


function Td({
  children,
}: {
  children:
    React.ReactNode;
}) {
  return (
    <td
      style={{
        padding:
          "10px 11px",

        borderBottom:
          "1px solid #efebe3",
      }}
    >
      {children}
    </td>
  );
}


const labelStyle = {
  display:
    "grid",

  gap:
    5,

  fontSize:
    9,
} as const;


const inputStyle = {
  width:
    "100%",

  height:
    36,

  padding:
    "0 10px",

  border:
    "1px solid var(--color-border)",

  borderRadius:
    7,

  outline:
    "none",

  background:
    "#fffefa",

  fontSize:
    10,
} as const;


const errorStyle = {
  padding:
    "10px 12px",

  border:
    "1px solid #efc6c6",

  borderRadius:
    7,

  background:
    "#fff0f0",

  color:
    "#b52b2b",

  fontSize:
    10,
} as const;


const successStyle = {
  padding:
    "10px 12px",

  border:
    "1px solid #cce5c4",

  borderRadius:
    7,

  background:
    "#f0faed",

  color:
    "#34732a",

  fontSize:
    10,
} as const;