"use client";

import type {
  ReactNode,
} from "react";

import {
  useWorkspace,
} from "@/contexts/workspace-context";


interface WorkspaceRequiredProps {
  children:
    ReactNode;
}


export function WorkspaceRequired({
  children,
}: WorkspaceRequiredProps) {
  const {
    workspaceId,
    loading,
    workspaceLoading,
    error,
    workspaceError,
  } =
    useWorkspace();


  /*
   * Workspace context is still resolving.
   */
  if (
    loading ||
    workspaceLoading
  ) {
    return (
      <section
        className="panel"
      >
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
            <div
              className="text-label"
            >
              Loading workspace...
            </div>
          </div>
        </div>
      </section>
    );
  }


  /*
   * Authentication may be valid while the user
   * does not currently have a resolved workspace.
   */
  if (
    !workspaceId
  ) {
    const message =
      workspaceError ??
      error;


    return (
      <section
        className="panel"
      >
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
          <div
            style={{
              width:
                "100%",

              maxWidth:
                500,
            }}
          >
            <h2
              style={{
                margin:
                  0,

                fontSize:
                  18,
              }}
            >
              Workspace required
            </h2>


            <p
              className="text-label"
              style={{
                margin:
                  "8px auto 0",

                lineHeight:
                  1.6,
              }}
            >
              Select or create a workspace before accessing this page.
            </p>


            {message ? (
              <p
                className="text-label"
                style={{
                  margin:
                    "8px auto 0",

                  lineHeight:
                    1.6,
                }}
              >
                {message}
              </p>
            ) : null}
          </div>
        </div>
      </section>
    );
  }


  /*
   * A valid workspace exists.
   * Render the protected workspace page.
   */
  return (
    <>
      {children}
    </>
  );
}


export default WorkspaceRequired;