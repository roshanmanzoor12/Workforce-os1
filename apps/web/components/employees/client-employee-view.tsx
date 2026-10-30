"use client";

import {
  Building2,
} from "lucide-react";

import {
  useWorkspace,
} from "@/contexts/workspace-context";


export function ClientEmployeeView() {
  const {
    workspace,
  } =
    useWorkspace();


  return (
    <section className="panel">
      <div
        className="panel-body"
        style={{
          minHeight:
            300,

          display:
            "grid",

          placeItems:
            "center",

          padding:
            36,

          textAlign:
            "center",
        }}
      >
        <div>
          <Building2
            size={
              32
            }
          />


          <h2
            style={{
              marginTop:
                12,
            }}
          >
            Workspace People
          </h2>


          <p
            className="text-label"
            style={{
              maxWidth:
                460,

              margin:
                "7px auto 0",

              lineHeight:
                1.6,
            }}
          >
            Client access to employee records is disabled by default for{" "}
            {workspace?.name ??
              "this workspace"}.
            Shared contacts, meetings and channels can still be available through assigned permissions.
          </p>
        </div>
      </div>
    </section>
  );
}