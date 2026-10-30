"use client";

import {
  useState,
} from "react";

import {
  Loader2,
  UserPlus,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";

import {
  recruitmentService,
} from "@/services/recruitment.service";


interface CreateCandidateFormProps {
  workspaceId:
    string;

  jobId:
    string;

  onCreated:
    () => void;

  onCancel:
    () => void;
}


export function CreateCandidateForm({
  workspaceId,

  jobId,

  onCreated,

  onCancel,
}: CreateCandidateFormProps) {
  const [
    firstName,
    setFirstName,
  ] =
    useState("");


  const [
    lastName,
    setLastName,
  ] =
    useState("");


  const [
    email,
    setEmail,
  ] =
    useState("");


  const [
    phone,
    setPhone,
  ] =
    useState("");


  const [
    resumeUrl,
    setResumeUrl,
  ] =
    useState("");


  const [
    notes,
    setNotes,
  ] =
    useState("");


  const [
    saving,
    setSaving,
  ] =
    useState(false);


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  async function submit(
    event:
      React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();


    if (
      !jobId
    ) {
      setError(
        "Select a job before creating a candidate.",
      );

      return;
    }


    setSaving(true);
    setError(null);


    try {
      await recruitmentService.createCandidate(
        workspaceId,
        {
          job_id:
            jobId,

          first_name:
            firstName.trim(),

          last_name:
            lastName.trim(),

          email:
            email.trim(),

          phone:
            phone.trim() ||
            null,

          resume_url:
            resumeUrl.trim() ||
            null,

          notes:
            notes.trim() ||
            null,
        },
      );


      onCreated();

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create the candidate.",
      );
    } finally {
      setSaving(false);
    }
  }


  return (
    <form
      onSubmit={
        submit
      }
      style={{
        display:
          "grid",

        gap:
          15,
      }}
    >
      {error ? (
        <div
          role="alert"
          className="auth-error"
        >
          {error}
        </div>
      ) : null}

      <div
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "repeat(2, minmax(0, 1fr))",

          gap:
            12,
        }}
      >
        <div
          style={{
            display:
              "grid",

            gap:
              7,
          }}
        >
          <label>
            First name
          </label>

          <input
            required
            value={
              firstName
            }
            onChange={(
              event,
            ) =>
              setFirstName(
                event.target.value,
              )
            }
          />
        </div>

        <div
          style={{
            display:
              "grid",

            gap:
              7,
          }}
        >
          <label>
            Last name
          </label>

          <input
            required
            value={
              lastName
            }
            onChange={(
              event,
            ) =>
              setLastName(
                event.target.value,
              )
            }
          />
        </div>
      </div>

      <div
        style={{
          display:
            "grid",

          gap:
            7,
        }}
      >
        <label>
          Email
        </label>

        <input
          required
          type="email"
          value={
            email
          }
          onChange={(
            event,
          ) =>
            setEmail(
              event.target.value,
            )
          }
        />
      </div>

      <div
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "repeat(2, minmax(0, 1fr))",

          gap:
            12,
        }}
      >
        <div
          style={{
            display:
              "grid",

            gap:
              7,
          }}
        >
          <label>
            Phone
          </label>

          <input
            value={
              phone
            }
            onChange={(
              event,
            ) =>
              setPhone(
                event.target.value,
              )
            }
            maxLength={40}
          />
        </div>

        <div
          style={{
            display:
              "grid",

            gap:
              7,
          }}
        >
          <label>
            Resume URL
          </label>

          <input
            type="url"
            value={
              resumeUrl
            }
            onChange={(
              event,
            ) =>
              setResumeUrl(
                event.target.value,
              )
            }
            maxLength={500}
            placeholder="https://..."
          />
        </div>
      </div>

      <div
        style={{
          display:
            "grid",

          gap:
            7,
        }}
      >
        <label>
          Notes
        </label>

        <textarea
          rows={5}
          value={
            notes
          }
          onChange={(
            event,
          ) =>
            setNotes(
              event.target.value,
            )
          }
        />
      </div>

      <div
        style={{
          display:
            "flex",

          justifyContent:
            "flex-end",

          gap:
            8,
        }}
      >
        <Button
          type="button"
          variant="outline"
          onClick={
            onCancel
          }
          disabled={
            saving
          }
        >
          Cancel
        </Button>

        <Button
          type="submit"
          disabled={
            saving
          }
        >
          {saving ? (
            <Loader2
              size={15}
              className="spin"
            />
          ) : (
            <UserPlus
              size={15}
            />
          )}

          Add Candidate
        </Button>
      </div>
    </form>
  );
}