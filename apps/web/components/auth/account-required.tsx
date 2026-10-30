"use client";

import type { ReactNode } from "react";

import { useWorkspace } from "@/contexts/workspace-context";

interface AccountRequiredProps {
  children: ReactNode;
}

export function AccountRequired({
  children,
}: AccountRequiredProps) {
  const {
    user,
    loading,
    error,
    refreshBootstrap,
  } = useWorkspace();

  if (loading) {
    return (
      <section className="panel" aria-busy="true">
        <div className="panel-body">
          <p>Loading your account...</p>
        </div>
      </section>
    );
  }

  if (!user) {
    return (
      <section className="panel" role="alert">
        <div className="panel-body">
          <h2>Your account could not be loaded</h2>

          <p style={{ marginTop: 8 }}>
            {error ?? "Please sign in to access your personal account."}
          </p>

          <button
            type="button"
            className="button button--primary"
            style={{ marginTop: 16 }}
            onClick={() => {
              void refreshBootstrap();
            }}
          >
            Retry
          </button>
        </div>
      </section>
    );
  }

  return <>{children}</>;
}