"use client";

import { useEffect, useRef, useState, type CSSProperties, type FormEvent } from "react";
import { Building2, Camera, Loader2, RotateCcw, Save } from "lucide-react";
import { useWorkspace } from "@/contexts/workspace-context";
import { workspacesService } from "@/services/workspaces.service";
import { workspaceLogoSrc } from "@/lib/workspace/logo-url";
import { api } from "@/lib/api/client";

const DEFAULT_PRIMARY = "#171717";
const DEFAULT_ACCENT = "#F5B700";

const panel: CSSProperties = {
  border: "1px solid #e7dece", borderRadius: 18, background: "#fffefa",
  padding: "clamp(18px, 3vw, 30px)", boxShadow: "0 4px 18px rgba(23,23,23,0.035)",
};
const fieldLabel: CSSProperties = { display: "block", fontSize: 13, fontWeight: 700, marginBottom: 9, color: "#272727" };
const field: CSSProperties = { width: "100%", border: "1px solid #d8d2c6", borderRadius: 10, padding: "13px 14px", fontSize: 14, background: "#fff", color: "#171717", boxSizing: "border-box" };

function initialsOf(value: string): string {
  const parts = value.trim().split(/\s+/).filter(Boolean);
  if (parts.length > 1) return `${parts[0]?.[0] ?? ""}${parts[1]?.[0] ?? ""}`.toUpperCase();
  return (parts[0] ?? "WS").slice(0, 2).toUpperCase();
}
function errorMessage(value: unknown): string {
  return value instanceof Error ? value.message : "The operation could not be completed.";
}

export default function WorkspaceAppearancePage() {
  const { workspaceId, workspace, membership, workspaceLoading, refreshWorkspaces } = useWorkspace();
  const fileRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [primaryColor, setPrimaryColor] = useState(DEFAULT_PRIMARY);
  const [accentColor, setAccentColor] = useState(DEFAULT_ACCENT);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [logoFailed, setLogoFailed] = useState(false);
  const canEdit = membership?.role_key === "owner" || membership?.role_key === "admin";

  useEffect(() => {
    setName(workspace?.name ?? "");
    setPrimaryColor(workspace?.primary_color ?? DEFAULT_PRIMARY);
    setAccentColor(workspace?.accent_color ?? DEFAULT_ACCENT);
    setLogoFailed(false);
    setError("");
    setSuccess("");
  }, [workspaceId, workspace?.name, workspace?.logo_url, workspace?.primary_color, workspace?.accent_color]);

  async function uploadLogo(file: File) {
    if (!workspaceId || !canEdit || uploading || saving) return;
    setError(""); setSuccess("");
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Choose a JPG, PNG or WebP image."); return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("The company image must be 5 MB or smaller."); return;
    }
    const data = new FormData();
    data.append("file", file);
    setUploading(true);
    try {
      await api.postForm<{ logo_url: string }>(`/workspaces/${workspaceId}/logo/upload`, data);
      await refreshWorkspaces();
      setLogoFailed(false);
      setSuccess("Company photo updated successfully.");
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function saveAppearance(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!workspaceId || !canEdit || saving || uploading) return;
    const nextName = name.trim().replace(/\s+/g, " ");
    if (nextName.length < 2 || nextName.length > 200) {
      setError("Workspace name must contain 2–200 characters."); return;
    }
    setSaving(true); setError(""); setSuccess("");
    try {
      // Important: never send logo_url from the theme form. File uploads own that field.
      await workspacesService.update(workspaceId, {
        name: nextName,
        primary_color: primaryColor,
        accent_color: accentColor,
      });
      await refreshWorkspaces();
      setSuccess("Company name and theme saved successfully.");
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setSaving(false);
    }
  }

  if (workspaceLoading && !workspace) return <main role="status" style={{ padding: 28 }}>Loading workspace…</main>;
  if (!workspaceId || !workspace || !membership) return <main role="alert" style={{ padding: 28 }}>Select an active workspace to edit its appearance.</main>;

  const logoSrc = workspaceLogoSrc(workspace.logo_url);
  const showLogo = Boolean(logoSrc) && !logoFailed;
  const working = saving || uploading;

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "28px 22px 64px", display: "grid", gap: 22, color: "#171717" }}>
      <header>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Building2 size={29} aria-hidden="true" />
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800 }}>Workspace Appearance</h1>
        </div>
        <p style={{ margin: "9px 0 0", color: "#77746d", fontSize: 14 }}>
          Customize this company workspace. Your personal photo and Workforce OS application logo are separate.
        </p>
      </header>

      <section style={panel} aria-label="Company appearance">
        <div style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap", marginBottom: 28 }}>
          <div style={{ position: "relative", width: 104, height: 104, flexShrink: 0 }}>
            <input
              ref={fileRef} id="workspace-company-photo" type="file"
              accept="image/png,image/jpeg,image/webp" disabled={!canEdit || working}
              aria-label="Choose a company photo" style={{ display: "none" }}
              onChange={(event) => { const file = event.target.files?.[0]; if (file) void uploadLogo(file); }}
            />
            <button
              type="button" disabled={!canEdit || working}
              aria-label="Change company photo" title={canEdit ? "Change company photo" : "Company photo"}
              onClick={() => fileRef.current?.click()}
              style={{ position: "relative", display: "grid", placeItems: "center", width: 100, height: 100,
                background: primaryColor, color: "#fff", borderRadius: 22, border: "1px solid #e6dfd4",
                overflow: "visible", cursor: canEdit ? "pointer" : "default", padding: 0 }}
            >
              <span style={{ width: "100%", height: "100%", overflow: "hidden", borderRadius: 21, display: "grid", placeItems: "center", fontSize: 27, fontWeight: 800 }}>
                {showLogo ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={logoSrc} alt={`${workspace.name} logo`} style={{ width: "100%", height: "100%", objectFit: "cover" }} onError={() => setLogoFailed(true)} />
                ) : initialsOf(name || workspace.name)}
              </span>
              {canEdit && (
                <span aria-hidden="true" style={{ position: "absolute", bottom: -7, right: -7, width: 33, height: 33, borderRadius: "50%", background: DEFAULT_ACCENT,
                  color: "#171717", border: "3px solid #fffefa", display: "grid", placeItems: "center" }}>
                  {uploading ? <Loader2 size={16} className="animate-spin" /> : <Camera size={17} />}
                </span>
              )}
            </button>
          </div>
          <div style={{ flex: "1 1 200px" }}>
            <h2 style={{ margin: 0, fontSize: 24, fontWeight: 750 }}>{name || workspace.name}</h2>
            <p style={{ margin: "5px 0", fontSize: 13, color: "#77746d" }}>Company workspace photo</p>
            <p style={{ margin: 0, fontSize: 12, color: "#77746d" }}>
              {canEdit ? "Click the photo or camera icon to upload a JPG, PNG or WebP (max 5 MB)." : "Only workspace Owners and Admins can change this photo."}
            </p>
          </div>
        </div>

        <form onSubmit={(event) => void saveAppearance(event)} style={{ display: "grid", gap: 24 }}>
          <div>
            <label htmlFor="workspace-name" style={fieldLabel}>Company / workspace name</label>
            <input id="workspace-name" value={name} minLength={2} maxLength={200} required
              disabled={!canEdit || working} onChange={(event) => setName(event.target.value)} style={field} />
          </div>

          <div>
            <h2 style={{ fontSize: 19, margin: "0 0 6px", fontWeight: 750 }}>Company theme colors</h2>
            <p style={{ fontSize: 13, color: "#77746d", margin: "0 0 16px" }}>Each workspace saves its own colors. Default: black and yellow.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
              {([
                ["Primary color", primaryColor, setPrimaryColor],
                ["Accent color", accentColor, setAccentColor],
              ] as const).map(([title, value, setValue]) => (
                <label key={title} style={{ border: "1px solid #e4dfd5", padding: 14, borderRadius: 11, display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                  <span><strong style={{ fontSize: 13, display: "block" }}>{title}</strong><small style={{ color: "#807c73" }}>{value.toUpperCase()}</small></span>
                  <input type="color" aria-label={title} value={value} disabled={!canEdit || working}
                    onChange={(event) => setValue(event.target.value)} style={{ width: 48, height: 38, cursor: "pointer" }} />
                </label>
              ))}
            </div>
            <div aria-label="Company colors preview" style={{ display: "flex", overflow: "hidden", borderRadius: 10, marginTop: 15, border: "1px solid #e8e0d3" }}>
              <span style={{ flex: 1, textAlign: "center", padding: 16, background: primaryColor, color: "#fff", fontSize: 13, fontWeight: 650 }}>Primary</span>
              <span style={{ flex: 1, textAlign: "center", padding: 16, background: accentColor, color: "#171717", fontSize: 13, fontWeight: 650 }}>Accent</span>
            </div>
            {canEdit && <button type="button" disabled={working} onClick={() => { setPrimaryColor(DEFAULT_PRIMARY); setAccentColor(DEFAULT_ACCENT); }}
              style={{ display: "inline-flex", alignItems: "center", gap: 6, marginTop: 13, border: 0, color: "#4c4538", textDecoration: "underline", background: "transparent", cursor: "pointer", padding: 0, fontSize: 13 }}>
              <RotateCcw size={13} /> Use black & yellow defaults
            </button>}
          </div>
          {error && <p role="alert" style={{ margin: 0, background: "#fff0ef", border: "1px solid #ffc9c4", padding: 12, borderRadius: 9, color: "#a52216", fontSize: 13 }}>{error}</p>}
          {success && <p role="status" style={{ margin: 0, background: "#f0f8ed", border: "1px solid #d3ebcc", padding: 12, borderRadius: 9, color: "#28713a", fontSize: 13 }}>{success}</p>}
          {canEdit && <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button type="submit" disabled={working} style={{ display: "inline-flex", alignItems: "center", gap: 9, padding: "13px 19px", background: DEFAULT_PRIMARY, color: "#fff", border: 0, borderRadius: 10, fontWeight: 700, cursor: working ? "wait" : "pointer", opacity: working ? 0.7 : 1 }}>
              {working ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              {saving ? "Saving…" : uploading ? "Uploading photo…" : "Save company appearance"}
            </button>
          </div>}
        </form>
      </section>
    </main>
  );
}
