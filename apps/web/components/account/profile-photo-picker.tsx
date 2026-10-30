"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Camera, Check, ImagePlus, Loader2, Trash2, X } from "lucide-react";
import { useWorkspace } from "@/contexts/workspace-context";
import { personalAccountService } from "@/services/personal-account.service";
import { avatarImageUrl, UserAvatar } from "./user-avatar";
import styles from "./profile-photo-picker.module.css";

const presets = [
  ["coral", "Coral", "#ffe1d4"], ["lavender", "Lavender", "#eae1fa"],
  ["sunshine", "Sunshine", "#fff0bb"], ["mint", "Mint", "#d8eee0"],
  ["sky", "Sky", "#dceafa"], ["aqua", "Aqua", "#d5eeee"],
  ["periwinkle", "Periwinkle", "#e1e5fa"], ["rose", "Rose", "#f8dfe5"],
  ["sand", "Sand", "#eee3d2"], ["ice", "Ice", "#e0eff6"],
  ["apricot", "Apricot", "#ffe4ce"], ["mauve", "Mauve", "#ebdfee"],
] as const;
type Selection = "upload" | "google" | "preset" | "none";

export function ProfilePhotoPicker() {
  const { user } = useWorkspace();
  return user ? <ProfilePhotoPickerForUser key={user.id} /> : null;
}

function ProfilePhotoPickerForUser() {
  const { user, updateUser } = useWorkspace();
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const headingId = useId();
  const [open, setOpen] = useState(false);
  const [source, setSource] = useState<Selection>("upload");
  const [preset, setPreset] = useState<string>("coral");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [googlePhoto, setGooglePhoto] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [x, setX] = useState(0);
  const [y, setY] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loadingGoogle, setLoadingGoogle] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const owner = useRef(user?.id);
  owner.current = user?.id;

  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => {
    if (!open || !user) return;
    const currentOwner = user.id;
    let stopped = false;
    const panel = dialog.current;
    if (panel && !panel.open) panel.showModal();
    setLoadingGoogle(true);
    personalAccountService.get().then(account => {
      if (!stopped && owner.current === currentOwner) setGooglePhoto(account.google_avatar_url ?? null);
    }).catch(() => {
      if (!stopped) setError("Google photo could not be checked. Upload a photo or choose an avatar, or reopen to retry.");
    }).finally(() => { if (!stopped) setLoadingGoogle(false); });
    return () => { stopped = true; if (panel?.open) panel.close(); };
  }, [open, user?.id]);

  function close() {
    if (busy) return;
    dialog.current?.close();
    setOpen(false); setFile(null); setError("");
    trigger.current?.focus();
  }
  function show() {
    setSaved(""); setError(""); setGooglePhoto(null); setFile(null);
    const chosen = user?.avatar_url?.match(/\/presets\/([a-z]+)\.webp$/)?.[1];
    setPreset(chosen ?? "coral");
    setSource(chosen ? "preset" : user?.avatar_source === "google" ? "google" : "upload");
    setZoom(1); setX(0); setY(0); setOpen(true);
  }
  function chooseFile(next?: File) {
    if (!next) return;
    setError("");
    if (!["image/jpeg", "image/png", "image/webp"].includes(next.type) || next.size > 5 * 1024 * 1024) {
      setError("Choose a JPG, PNG or WebP photo smaller than 5 MB."); return;
    }
    setFile(next); setZoom(1); setX(0); setY(0); setSource("upload");
  }
  async function save() {
    if (busy || !user) return;
    const currentOwner = user.id;
    setBusy(true); setError("");
    try {
      const result = source === "upload"
        ? file ? await personalAccountService.uploadAvatar(file, zoom, x, y, currentOwner) : null
        : await personalAccountService.chooseAvatar(source, source === "preset" ? preset : undefined, currentOwner);
      if (!mounted.current || owner.current !== currentOwner) return;
      if (!result) throw new Error("Choose a photo to upload first.");
      updateUser(result.user);
      dialog.current?.close(); setOpen(false); setFile(null);
      setSaved("Profile photo updated across your account.");
      trigger.current?.focus();
    } catch (cause) {
      if (mounted.current && owner.current === currentOwner) setError(cause instanceof Error ? cause.message : "Photo could not be saved. Retry.");
    } finally { if (mounted.current) setBusy(false); }
  }
  const presetUrl = `/api/v1/personal/avatars/presets/${preset}.webp`;
  const selectedUrl = source === "preset" ? presetUrl : source === "google" ? googlePhoto : user?.avatar_url;
  const canSave = source === "upload" ? Boolean(file) : source === "google" ? Boolean(googlePhoto) : true;

  if (!user) return null;
  return <div className={styles.root}>
    <button ref={trigger} type="button" className={styles.trigger} onClick={show}
      aria-label="Change profile photo" aria-haspopup="dialog">
      <UserAvatar userId={user.id} name={user.username} />
      <span className={styles.camera}><Camera size={12} aria-hidden="true" /></span>
    </button>
    <span className={styles.srOnly} role="status">{saved}</span>
    {open && <dialog ref={dialog} className={styles.dialog} aria-labelledby={headingId}
      onCancel={event => { event.preventDefault(); close(); }}
      onClick={event => { if (event.target === event.currentTarget) close(); }}>
      <div className={styles.panel}>
        <header className={styles.header}>
          <div><h2 id={headingId}>Your profile photo</h2><p>One photo, everywhere you work.</p></div>
          <button className={styles.iconButton} type="button" aria-label="Close photo picker" disabled={busy} onClick={close}><X size={19} /></button>
        </header>
        <div className={styles.previewRow}>
          <div className={styles.preview}>
            {source === "upload" && preview
              ? <div className={styles.cropViewport}><img src={preview} alt="Your photo crop preview"
                  style={{ width: `${zoom * 100}%`, height: `${zoom * 100}%`,
                    left: `${-(zoom - 1) * (x + 1) * 50}%`, top: `${-(zoom - 1) * (y + 1) * 50}%`,
                    objectPosition: `${(x + 1) * 50}% ${(y + 1) * 50}%` }} /></div>
              : <UserAvatar src={source === "none" ? null : selectedUrl} name={user.username} />}
          </div>
          <div className={styles.previewText}><strong>{[user.first_name, user.last_name].filter(Boolean).join(" ") || user.username}</strong>
            <p>Your header, chats, friends and calls will use this photo.</p>
            <button className={styles.uploadButton} type="button" disabled={busy} onClick={() => input.current?.click()}><ImagePlus size={16} />{file ? "Choose another photo" : "Upload a photo"}</button>
            <small>JPG, PNG or WebP · up to 5 MB</small>
          </div>
        </div>
        <input ref={input} className={styles.srOnly} type="file" accept="image/jpeg,image/png,image/webp" disabled={busy}
          aria-label="Choose profile photo file" onChange={event => { chooseFile(event.target.files?.[0]); event.target.value = ""; }} />
        {file && source === "upload" && <fieldset className={styles.cropControls} disabled={busy}>
          <legend>Frame your photo</legend>
          <label>Zoom<input aria-label="Photo zoom" type="range" min="1" max="3" step="0.01" value={zoom} onChange={event => setZoom(Number(event.target.value))} /></label>
          <label>Left / right<input aria-label="Horizontal photo position" type="range" min="-1" max="1" step="0.01" value={x} onChange={event => setX(Number(event.target.value))} /></label>
          <label>Up / down<input aria-label="Vertical photo position" type="range" min="-1" max="1" step="0.01" value={y} onChange={event => setY(Number(event.target.value))} /></label>
        </fieldset>}
        <div className={styles.options}>
          <button type="button" disabled={busy || !googlePhoto} className={source === "google" ? styles.activeOption : styles.option}
            aria-pressed={source === "google"} onClick={() => { setSource("google"); setError(""); }}>
            <span className={styles.miniPhoto}><UserAvatar src={googlePhoto} name="Google" animated={false} /></span>
            <span>Use Google photo<small>{loadingGoogle ? "Checking your connected account…" : googlePhoto ? "From your connected Google account" : "Sign in with Google to make it available"}</small></span>
            {source === "google" && <Check size={16} />}
          </button>
          <button type="button" disabled={busy} className={source === "none" ? styles.activeOption : styles.option}
            aria-pressed={source === "none"} onClick={() => { setSource("none"); setError(""); }}><Trash2 size={17} /><span>Remove photo<small>Use your initials</small></span>{source === "none" && <Check size={16} />}</button>
        </div>
        <section className={styles.avatarSection} aria-label="Default 3D avatars">
          <h3>Or choose a 3D avatar</h3><p>A little character. Pick your color.</p>
          <div className={styles.grid}>
            {presets.map(([id, label, color]) => <button key={id} type="button" disabled={busy}
              className={`${styles.preset} ${source === "preset" && preset === id ? styles.selectedPreset : ""}`}
              aria-label={`${label} 3D avatar`} aria-pressed={source === "preset" && preset === id}
              onClick={() => { setSource("preset"); setPreset(id); setError(""); }}>
              <span className={styles.presetPicture} style={{ background: color }}><UserAvatar src={`/api/v1/personal/avatars/presets/${id}.webp`} name={label} animated={false} /></span>
              <span>{label}</span>{source === "preset" && preset === id && <span className={styles.selectedCheck}><Check size={11} /></span>}
            </button>)}
          </div>
        </section>
        {error && <p role="alert" className={styles.error}>{error}</p>}
        <footer className={styles.footer}><button type="button" className={styles.cancelButton} disabled={busy} onClick={close}>Cancel</button>
          <button type="button" className={styles.saveButton} disabled={busy || !canSave} onClick={() => void save()}>{busy ? <Loader2 className={styles.spin} size={16} /> : <Check size={16} />}{busy ? "Saving photo…" : "Save photo"}</button></footer>
      </div>
    </dialog>}
  </div>;
}
