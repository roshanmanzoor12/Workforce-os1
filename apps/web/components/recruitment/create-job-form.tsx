"use client";

import {
  useState,
} from "react";

import {
  BriefcaseBusiness,
  Loader2,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";

import {
  recruitmentService,
} from "@/services/recruitment.service";

import type {
  JobCreateRequest,
} from "@/types/recruitment";


interface CreateJobFormProps {
  workspaceId:
    string;

  onCreated:
    () => void;

  onCancel:
    () => void;
}


export function CreateJobForm({
  workspaceId,

  onCreated,

  onCancel,
}: CreateJobFormProps) {
  const [
    title,
    setTitle,
  ] =
    useState("");


  const [
    location,
    setLocation,
  ] =
    useState("");


  const [
    employmentType,
    setEmploymentType,
  ] =
    useState("");


  const [
    description,
    setDescription,
  ] =
    useState("");


  const [
    closingDate,
    setClosingDate,
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
      title.trim().length <
      2
    ) {
      setError(
        "Job title must contain at least 2 characters.",
      );

      return;
    }


    setSaving(true);
    setError(null);


    const payload:
      JobCreateRequest = {
      title:
        title.trim(),

      department_id:
        null,

      description:
        description.trim() ||
        null,

      location:
        location.trim() ||
        null,

      employment_type:
        employmentType.trim() ||
        null,

      closing_date:
        closingDate
          ? new Date(
              `${closingDate}T23:59:59`,
            ).toISOString()
          : null,
    };


    try {
      await recruitmentService.createJob(
        workspaceId,
        payload,
      );

      onCreated();
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create the job.",
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
          16,
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

          gap:
            7,
        }}
      >
        <label>
          Job title
        </label>

        <input
          required
          minLength={2}
          maxLength={150}
          value={
            title
          }
          onChange={(
            event,
          ) =>
            setTitle(
              event.target.value,
            )
          }
          placeholder="e.g. Senior Frontend Engineer"
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
            Location
          </label>

          <input
            value={
              location
            }
            onChange={(
              event,
            ) =>
              setLocation(
                event.target.value,
              )
            }
            placeholder="Remote / New York"
            maxLength={200}
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
            Employment type
          </label>

          <input
            value={
              employmentType
            }
            onChange={(
              event,
            ) =>
              setEmploymentType(
                event.target.value,
              )
            }
            placeholder="Full-time"
            maxLength={50}
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
          Closing date
        </label>

        <input
          type="date"
          value={
            closingDate
          }
          onChange={(
            event,
          ) =>
            setClosingDate(
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
          Description
        </label>

        <textarea
          value={
            description
          }
          onChange={(
            event,
          ) =>
            setDescription(
              event.target.value,
            )
          }
          rows={6}
          placeholder="Describe the role, responsibilities and requirements."
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

          flexWrap:
            "wrap",
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
            <BriefcaseBusiness
              size={15}
            />
          )}

          Create Job
        </Button>
      </div>
    </form>
  );
}