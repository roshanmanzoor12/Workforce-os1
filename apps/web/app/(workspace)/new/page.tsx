"use client";

import {
  ArrowLeft,
  Building2,
} from "lucide-react";

import Link from "next/link";

import {
  type FormEvent,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import {
  saveLastWorkspaceId,
} from "@/lib/app/bootstrap-storage";

import {
  workspaceService,
} from "@/services/workspace.service";


export default function CreateWorkspacePage() {
  const router =
    useRouter();

  const [
    name,
    setName,
  ] =
    useState("");

  const [
    slug,
    setSlug,
  ] =
    useState("");

  const [
    timezone,
    setTimezone,
  ] =
    useState(
      Intl.DateTimeFormat()
        .resolvedOptions()
        .timeZone ||
        "UTC",
    );

  const [
    submitting,
    setSubmitting,
  ] =
    useState(
      false,
    );

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  async function submit(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError(
      null,
    );

    if (
      name.trim().length <
      2
    ) {
      setError(
        "Enter a workspace name.",
      );

      return;
    }

    setSubmitting(
      true,
    );

    try {
      const result =
        await workspaceService.create({
          name:
            name.trim(),

          slug:
            slug.trim()
              ? slug
                  .trim()
                  .toLowerCase()
              : null,

          timezone:
            timezone.trim() ||
            "UTC",

          logo_url:
            null,
        });

      saveLastWorkspaceId(
        result.workspace.id,
      );

      try {
        await workspaceService.provision(
          result.workspace.id,
        );
      } catch {
        // Workspace exists even if provisioning needs retry.
      }

      router.replace(
        "/dashboard",
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create workspace.",
      );

    } finally {
      setSubmitting(
        false,
      );
    }
  }


  return (
    <div
      style={{
        maxWidth:
          680,
        margin:
          "0 auto",
      }}
    >
      <Link
        href="/home"
        style={{
          display:
            "inline-flex",
          alignItems:
            "center",
          gap:
            7,
          marginBottom:
            20,
          color:
            "var(--color-text-muted)",
          textDecoration:
            "none",
          fontSize:
            12,
        }}
      >
        <ArrowLeft size={14} />

        Back to Personal Home
      </Link>


      <section className="panel">
        <div className="panel-header">
          <div>
            <h1 className="text-section-title">
              Create workspace
            </h1>

            <div className="text-label">
              Create a company workspace for your team.
            </div>
          </div>

          <Building2
            size={22}
          />
        </div>

        <div className="panel-body">
          <form
            onSubmit={
              submit
            }
          >
            <label className="field">
              <span className="field-label">
                Workspace Name
              </span>

              <input
                className="input"
                value={
                  name
                }
                placeholder="Digital Promotix"
                disabled={
                  submitting
                }
                onChange={(
                  event,
                ) =>
                  setName(
                    event.target
                      .value,
                  )
                }
              />
            </label>


            <label className="field">
              <span className="field-label">
                Workspace Slug
              </span>

              <input
                className="input"
                value={
                  slug
                }
                placeholder="digital-promotix"
                disabled={
                  submitting
                }
                onChange={(
                  event,
                ) =>
                  setSlug(
                    event.target
                      .value,
                  )
                }
              />
            </label>


            <label className="field">
              <span className="field-label">
                Timezone
              </span>

              <input
                className="input"
                value={
                  timezone
                }
                disabled={
                  submitting
                }
                onChange={(
                  event,
                ) =>
                  setTimezone(
                    event.target
                      .value,
                  )
                }
              />
            </label>


            {error ? (
              <div
                className="auth-error"
                style={{
                  marginTop:
                    14,
                }}
              >
                {error}
              </div>
            ) : null}


            <button
              type="submit"
              className="button button--primary"
              disabled={
                submitting
              }
              style={{
                marginTop:
                  18,
              }}
            >
              {submitting
                ? "Creating workspace..."
                : "Create Workspace"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}