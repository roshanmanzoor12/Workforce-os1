"use client";

import {
  Laptop2,
  Monitor,
  Wifi,
  WifiOff,
} from "lucide-react";

import type {
  Employee,
} from "@/services/employees.service";

import type {
  DevicePublic,
} from "@/types/device-management";


interface LiveScreenCardProps {
  employee:
    Employee;

  device:
    DevicePublic | null;

  selected:
    boolean;

  onSelect:
    () => void;
}


export function LiveScreenCard({
  employee,
  device,
  selected,
  onSelect,
}: LiveScreenCardProps) {
  const connected =
    device?.status ===
      "active";


  const screenReady =
    connected &&
    Boolean(
      device?.is_active,
    );


  return (
    <button
      type="button"
      onClick={
        onSelect
      }
      style={{
        display:
          "grid",

        gap:
          0,

        padding:
          0,

        overflow:
          "hidden",

        border:
          selected
            ? "1px solid #b78913"
            : "1px solid var(--color-border)",

        borderRadius:
          9,

        background:
          "#fffefa",

        color:
          "inherit",

        textAlign:
          "left",

        cursor:
          "pointer",
      }}
    >
      <div
        style={{
          position:
            "relative",

          aspectRatio:
            "16 / 9",

          display:
            "grid",

          placeItems:
            "center",

          background:
            connected
              ? "#17191b"
              : "#efeee9",

          color:
            connected
              ? "#d9d9d5"
              : "#828486",
        }}
      >
        {connected ? (
          <Monitor
            size={
              30
            }
          />
        ) : (
          <WifiOff
            size={
              27
            }
          />
        )}


        <span
          style={{
            position:
              "absolute",

            top:
              8,

            left:
              8,

            display:
              "inline-flex",

            alignItems:
              "center",

            gap:
              4,

            padding:
              "4px 7px",

            borderRadius:
              999,

            background:
              connected
                ? "rgba(37, 116, 48, 0.92)"
                : "rgba(70, 72, 73, 0.82)",

            color:
              "#fff",

            fontSize:
              8,

            fontWeight:
              600,
          }}
        >
          {connected ? (
            <Wifi
              size={
                9
              }
            />
          ) : (
            <WifiOff
              size={
                9
              }
            />
          )}

          {connected
            ? "Connected"
            : device
              ? device.status
              : "No device"}
        </span>


        {connected ? (
          <span
            style={{
              position:
                "absolute",

              right:
                8,

              bottom:
                8,

              padding:
                "4px 7px",

              borderRadius:
                5,

              background:
                "rgba(0, 0, 0, 0.58)",

              color:
                "#fff",

              fontSize:
                7,
            }}
          >
            Stream awaiting browser endpoint
          </span>
        ) : null}
      </div>


      <div
        style={{
          display:
            "grid",

          gap:
            8,

          padding:
            10,
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
              8,
          }}
        >
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
                  10,
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

                overflow:
                  "hidden",

                textOverflow:
                  "ellipsis",

                whiteSpace:
                  "nowrap",

                fontSize:
                  7,
              }}
            >
              {
                employee.employee_code
              }
              {" · "}
              {employee.job_title ??
                "Employee"}
            </div>
          </div>


          <span
            style={{
              padding:
                "3px 6px",

              borderRadius:
                999,

              background:
                screenReady
                  ? "#edf8e9"
                  : "#efefec",

              color:
                screenReady
                  ? "#34732a"
                  : "#6c6e70",

              fontSize:
                7,

              whiteSpace:
                "nowrap",
            }}
          >
            {screenReady
              ? "Agent ready"
              : "Unavailable"}
          </span>
        </div>


        <div
          style={{
            display:
              "flex",

            alignItems:
              "center",

            gap:
              5,

            color:
              "#75777a",

            fontSize:
              7,
          }}
        >
          <Laptop2
            size={
              10
            }
          />

          {device?.hostname ??
            "No registered device"}

          {device?.agent_version
            ? ` · Agent ${device.agent_version}`
            : ""}
        </div>
      </div>
    </button>
  );
}