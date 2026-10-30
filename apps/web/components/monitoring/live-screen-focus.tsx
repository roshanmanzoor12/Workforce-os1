"use client";

import {
  ChevronLeft,
  ChevronRight,
  Laptop2,
  Maximize2,
  Monitor,
  Wifi,
  WifiOff,
  X,
} from "lucide-react";

import type {
  Employee,
} from "@/services/employees.service";

import type {
  DevicePublic,
} from "@/types/device-management";


interface LiveScreenFocusProps {
  employee:
    Employee;

  device:
    DevicePublic | null;

  canGoPrevious:
    boolean;

  canGoNext:
    boolean;

  onPrevious:
    () => void;

  onNext:
    () => void;

  onClose:
    () => void;
}


function formatDate(
  value:
    string | null,
): string {
  if (!value) {
    return "Never";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return date.toLocaleString();
}


export function LiveScreenFocus({
  employee,
  device,
  canGoPrevious,
  canGoNext,
  onPrevious,
  onNext,
  onClose,
}: LiveScreenFocusProps) {
  const connected =
    device?.status ===
    "active";


  return (
    <section
      className="panel"
      style={{
        overflow:
          "hidden",
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
            12,

          padding:
            "10px 12px",

          borderBottom:
            "1px solid var(--color-border)",
        }}
      >
        <div
          style={{
            display:
              "flex",

            alignItems:
              "center",

            gap:
              9,

            minWidth:
              0,
          }}
        >
          <div
            style={{
              display:
                "grid",

              width:
                32,

              height:
                32,

              placeItems:
                "center",

              borderRadius:
                7,

              background:
                "#f3efe5",

              color:
                "#765c0c",
            }}
          >
            <Monitor
              size={
                15
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
                  11,
              }}
            >
              {
                employee.full_name
              }
            </strong>

            <div
              className="text-label"
              style={{
                marginTop:
                  2,

                fontSize:
                  8,
              }}
            >
              {
                employee.employee_code
              }
              {" · "}
              {device?.hostname ??
                "No device"}
            </div>
          </div>
        </div>


        <div
          style={{
            display:
              "flex",

            gap:
              6,
          }}
        >
          <button
            type="button"
            className="button button--outline"
            disabled={
              !canGoPrevious
            }
            onClick={
              onPrevious
            }
          >
            <ChevronLeft
              size={
                13
              }
            />
          </button>


          <button
            type="button"
            className="button button--outline"
            disabled={
              !canGoNext
            }
            onClick={
              onNext
            }
          >
            <ChevronRight
              size={
                13
              }
            />
          </button>


          <button
            type="button"
            className="button button--outline"
            onClick={
              onClose
            }
          >
            <X
              size={
                13
              }
            />

            Close
          </button>
        </div>
      </div>


      <div
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "minmax(0, 1fr) 260px",
        }}
      >
        <div
          style={{
            minHeight:
              500,

            display:
              "grid",

            placeItems:
              "center",

            position:
              "relative",

            background:
              connected
                ? "#131516"
                : "#efeee9",

            color:
              connected
                ? "#d5d7d7"
                : "#797c7e",
          }}
        >
          {connected ? (
            <div
              style={{
                textAlign:
                  "center",
              }}
            >
              <Maximize2
                size={
                  34
                }
                style={{
                  margin:
                    "0 auto 10px",
                }}
              />

              <strong
                style={{
                  display:
                    "block",

                  fontSize:
                    12,
                }}
              >
                Live screen transport ready for backend connection
              </strong>

              <p
                style={{
                  maxWidth:
                    420,

                  margin:
                    "7px auto 0",

                  color:
                    "#9fa2a2",

                  fontSize:
                    9,

                  lineHeight:
                    1.6,
                }}
              >
                The employee endpoint is connected. The authorized browser-facing screen stream will render here when the live-screen transport API is wired.
              </p>
            </div>
          ) : (
            <div
              style={{
                textAlign:
                  "center",
              }}
            >
              <WifiOff
                size={
                  30
                }
                style={{
                  margin:
                    "0 auto 9px",
                }}
              />

              <strong>
                Screen unavailable
              </strong>

              <p
                className="text-label"
                style={{
                  maxWidth:
                    360,

                  margin:
                    "6px auto 0",
                }}
              >
                This employee does not currently have an active registered endpoint.
              </p>
            </div>
          )}


          <span
            style={{
              position:
                "absolute",

              top:
                12,

              left:
                12,

              display:
                "inline-flex",

              alignItems:
                "center",

              gap:
                5,

              padding:
                "5px 8px",

              borderRadius:
                999,

              background:
                connected
                  ? "#2f7838"
                  : "#696b6d",

              color:
                "#fff",

              fontSize:
                8,
            }}
          >
            {connected ? (
              <Wifi
                size={
                  10
                }
              />
            ) : (
              <WifiOff
                size={
                  10
                }
              />
            )}

            {connected
              ? "Agent connected"
              : "Offline"}
          </span>
        </div>


        <aside
          style={{
            display:
              "grid",

            alignContent:
              "start",

            gap:
              10,

            padding:
              14,

            borderLeft:
              "1px solid var(--color-border)",

            background:
              "#faf8f3",
          }}
        >
          <strong
            style={{
              fontSize:
                10,
            }}
          >
            Employee
          </strong>


          <Detail
            label="Name"
            value={
              employee.full_name
            }
          />


          <Detail
            label="Employee Code"
            value={
              employee.employee_code
            }
          />


          <Detail
            label="Job Title"
            value={
              employee.job_title ??
              "Not assigned"
            }
          />


          <Detail
            label="Account"
            value={
              employee.user_id
                ? "Linked"
                : "Not linked"
            }
          />


          <div
            style={{
              height:
                1,

              background:
                "var(--color-border)",
            }}
          />


          <strong
            style={{
              fontSize:
                10,
            }}
          >
            Endpoint
          </strong>


          <Detail
            label="Hostname"
            value={
              device?.hostname ??
              "No device"
            }
          />


          <Detail
            label="Operating System"
            value={
              device
                ? `${device.os_name}${
                    device.os_version
                      ? ` ${device.os_version}`
                      : ""
                  }`
                : "—"
            }
          />


          <Detail
            label="Agent Version"
            value={
              device?.agent_version ??
              "—"
            }
          />


          <Detail
            label="Status"
            value={
              device?.status ??
              "No device"
            }
          />


          <Detail
            label="Last Seen"
            value={
              formatDate(
                device?.last_seen_at ??
                  null,
              )
            }
          />


          <div
            style={{
              display:
                "flex",

              alignItems:
                "center",

              gap:
                6,

              padding:
                9,

              border:
                "1px solid #e6dcc0",

              borderRadius:
                7,

              background:
                "#fff9e8",

              color:
                "#755f19",

              fontSize:
                8,

              lineHeight:
                1.5,
            }}
          >
            <Laptop2
              size={
                13
              }
            />

            Device secrets are never exposed to the browser.
          </div>
        </aside>
      </div>
    </section>
  );
}


function Detail({
  label,
  value,
}: {
  label:
    string;

  value:
    string;
}) {
  return (
    <div
      style={{
        padding:
          9,

        border:
          "1px solid #ebe6dd",

        borderRadius:
          7,

        background:
          "#fffefa",
      }}
    >
      <div
        className="text-label"
        style={{
          fontSize:
            7,
        }}
      >
        {label}
      </div>


      <strong
        style={{
          display:
            "block",

          marginTop:
            3,

          overflow:
            "hidden",

          textOverflow:
            "ellipsis",

          whiteSpace:
            "nowrap",

          fontSize:
            9,

          textTransform:
            label ===
            "Status"
              ? "capitalize"
              : undefined,
        }}
      >
        {value}
      </strong>
    </div>
  );
}