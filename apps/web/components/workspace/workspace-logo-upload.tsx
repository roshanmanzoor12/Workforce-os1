"use client";

import { useRef, useState } from "react";
import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";

export function WorkspaceLogoUpload() {
  const { workspaceId, membership, refreshWorkspaces } = useWorkspace();
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const canEdit = membership?.role_key === "owner" || membership?.role_key === "admin";

  async function upload(file: File) {
    if (!workspaceId || !canEdit || busy) return;
    setError("");
    setMessage("");
    if (file.size > 5 * 1024 * 1024) {
      setError("Choose a JPG, PNG, or WebP smaller than 5 MB.");
      return;
    }
    const data = new FormData();
    data.append("file", file);
    setBusy(true);
    try {
      await api.postForm<{logo_url: string}>(`/workspaces/${workspaceId}/logo/upload`, data);
      await refreshWorkspaces();
      setMessage("Company logo uploaded successfully.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Logo upload failed.");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <section className="space-y-2 rounded-xl border p-5" aria-label="Upload company logo">
      <h2 className="font-semibold">Upload company logo</h2>
      <p className="text-sm text-muted-foreground">JPG, PNG or WebP, up to 5 MB. This logo belongs only to the selected workspace.</p>
      <input id="workspace-logo-file" ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp"
        disabled={!canEdit || busy} aria-label="Company logo file"
        onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file); }} />
      {busy ? <p role="status">Uploading company logo…</p> : null}
      {message ? <p role="status" className="text-sm text-green-700">{message}</p> : null}
      {error ? <p role="alert" className="text-sm text-red-600">{error}</p> : null}
    </section>
  );
}
