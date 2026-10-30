"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Plus,
  UserPlus,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";

import {
  PageHeader,
} from "@/components/ui/page-header";

import {
  PermissionGate,
} from "@/components/workspace/permission-gate";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  recruitmentService,
} from "@/services/recruitment.service";

import type {
  CandidateResponse,
  InterviewResponse,
  JobResponse,
} from "@/types/recruitment";

import {
  CandidatesTable,
} from "@/components/recruitment/candidates-table";

import {
  CreateCandidateForm,
} from "@/components/recruitment/create-candidate-form";

import {
  CreateJobForm,
} from "@/components/recruitment/create-job-form";

import {
  InterviewsTable,
} from "@/components/recruitment/interviews-table";

import {
  JobsTable,
} from "@/components/recruitment/jobs-table";

import {
  RecruitmentModal,
} from "@/components/recruitment/recruitment-modal";


export function RecruitmentContent() {
  const {
    workspaceId,
  } =
    useWorkspace();


  const [
    jobs,
    setJobs,
  ] =
    useState<JobResponse[]>(
      [],
    );


  const [
    candidates,
    setCandidates,
  ] =
    useState<
      CandidateResponse[]
    >([]);


  const [
    interviews,
    setInterviews,
  ] =
    useState<
      InterviewResponse[]
    >([]);


  const [
    selectedJobId,
    setSelectedJobId,
  ] =
    useState<
      string | null
    >(null);


  const [
    loading,
    setLoading,
  ] =
    useState(true);


  const [
    candidatesLoading,
    setCandidatesLoading,
  ] =
    useState(false);


  const [
    interviewsLoading,
    setInterviewsLoading,
  ] =
    useState(false);


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const [
    modal,
    setModal,
  ] =
    useState<
      | "job"
      | "candidate"
      | null
    >(null);


  const selectedJob =
    useMemo(
      () =>
        jobs.find(
          (
            job,
          ) =>
            job.id ===
            selectedJobId,
        ) ??
        null,

      [
        jobs,
        selectedJobId,
      ],
    );


  const loadJobs =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          return;
        }


        setLoading(true);
        setError(null);


        try {
          const response =
            await recruitmentService.listJobs(
              workspaceId,
            );


          setJobs(
            response.items,
          );


          setSelectedJobId(
            (
              current,
            ) =>
              current &&
              response.items.some(
                (
                  job,
                ) =>
                  job.id ===
                  current,
              )
                ? current
                : response.items[0]
                    ?.id ??
                  null,
          );
        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load recruitment jobs.",
          );
        } finally {
          setLoading(false);
        }
      },
      [
        workspaceId,
      ],
    );


  const loadCandidates =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          return;
        }


        setCandidatesLoading(
          true,
        );


        try {
          const response =
            await recruitmentService.listCandidates(
              workspaceId,
              {
                jobId:
                  selectedJobId,
              },
            );


          setCandidates(
            response.items,
          );
        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load candidates.",
          );
        } finally {
          setCandidatesLoading(
            false,
          );
        }
      },
      [
        workspaceId,
        selectedJobId,
      ],
    );


  const loadInterviews =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          return;
        }


        setInterviewsLoading(
          true,
        );


        try {
          const response =
            await recruitmentService.listInterviews(
              workspaceId,
            );


          setInterviews(
            response.items,
          );
        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load interviews.",
          );
        } finally {
          setInterviewsLoading(
            false,
          );
        }
      },
      [
        workspaceId,
      ],
    );


  useEffect(() => {
    void loadJobs();
  }, [
    loadJobs,
  ]);


  useEffect(() => {
    if (
      selectedJobId
    ) {
      void loadCandidates();
    } else {
      setCandidates([]);
    }
  }, [
    loadCandidates,
    selectedJobId,
  ]);


  useEffect(() => {
    void loadInterviews();
  }, [
    loadInterviews,
  ]);


  async function deleteInterview(
    interviewId:
      string,
  ) {
    if (
      !workspaceId
    ) {
      return;
    }


    try {
      await recruitmentService.deleteInterview(
        workspaceId,
        interviewId,
      );


      setInterviews(
        (
          current,
        ) =>
          current.filter(
            (
              item,
            ) =>
              item.id !==
              interviewId,
          ),
      );
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to delete the interview.",
      );
    }
  }


  async function createdJob() {
    setModal(null);

    await loadJobs();
  }


  async function createdCandidate() {
    setModal(null);

    await loadCandidates();
  }


  if (
    !workspaceId
  ) {
    return null;
  }


  return (
    <div
      style={{
        maxWidth:
          1600,

        margin:
          "0 auto",

        display:
          "grid",

        gap:
          18,
      }}
    >
      <PageHeader
        title="Recruitment"
        description="Manage job openings, candidates and hiring activity from the live workspace API."
        actions={
          <div
            style={{
              display:
                "flex",

              gap:
                8,

              flexWrap:
                "wrap",
            }}
          >
            <PermissionGate
              permission="recruitment:manage"
            >
              <Button
                onClick={() =>
                  setModal(
                    "job",
                  )
                }
              >
                <Plus
                  size={15}
                />
                Create Job
              </Button>
            </PermissionGate>

            <PermissionGate
              permission="recruitment:manage"
            >
              <Button
                variant="outline"
                disabled={
                  !selectedJobId
                }
                onClick={() =>
                  setModal(
                    "candidate",
                  )
                }
              >
                <UserPlus
                  size={15}
                />
                Add Candidate
              </Button>
            </PermissionGate>
          </div>
        }
      />

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
            "minmax(0, 1.3fr) minmax(300px, .7fr)",

          gap:
            18,
        }}
      >
        <JobsTable
          jobs={
            jobs
          }
          loading={
            loading
          }
          selectedJobId={
            selectedJobId
          }
          onSelect={
            setSelectedJobId
          }
          onRefresh={
            () =>
              void loadJobs()
          }
        />

        <section
          className="panel"
        >
          <header
            className="panel-header"
          >
            <h2>
              Selected Opening
            </h2>
          </header>

          <div
            className="panel-body"
          >
            {selectedJob ? (
              <>
                <strong>
                  {
                    selectedJob.title
                  }
                </strong>

                <p className="text-label">
                  {
                    selectedJob.description ||
                    "No description provided."
                  }
                </p>

                <div
                  className="text-label"
                  style={{
                    display:
                      "grid",

                    gap:
                      7,

                    marginTop:
                      14,
                  }}
                >
                  <span>
                    Status:{" "}
                    {
                      selectedJob.status
                    }
                  </span>

                  <span>
                    Location:{" "}
                    {
                      selectedJob.location ||
                      "Unspecified"
                    }
                  </span>

                  <span>
                    Employment:{" "}
                    {
                      selectedJob.employment_type ||
                      "Unspecified"
                    }
                  </span>
                </div>
              </>
            ) : (
              <p className="text-label">
                Select a job opening to see its details and candidates.
              </p>
            )}
          </div>
        </section>
      </div>

      <PermissionGate
        permission="recruitment:view"
      >
        <CandidatesTable
          candidates={
            candidates
          }
          loading={
            candidatesLoading
          }
          onRefresh={
            () =>
              void loadCandidates()
          }
        />
      </PermissionGate>

      <PermissionGate
        permission="recruitment:view"
      >
        <InterviewsTable
          interviews={
            interviews
          }
          loading={
            interviewsLoading
          }
          onDelete={
            deleteInterview
          }
        />
      </PermissionGate>

      <RecruitmentModal
        open={
          modal ===
          "job"
        }
        title="Create Job"
        description="Create a real workspace recruitment opening."
        onClose={() =>
          setModal(null)
        }
      >
        <CreateJobForm
          workspaceId={
            workspaceId
          }
          onCreated={
            createdJob
          }
          onCancel={() =>
            setModal(null)
          }
        />
      </RecruitmentModal>

      <RecruitmentModal
        open={
          modal ===
          "candidate"
        }
        title="Add Candidate"
        description={
          selectedJob
            ? `Add a candidate to ${selectedJob.title}.`
            : "Select a job before adding a candidate."
        }
        onClose={() =>
          setModal(null)
        }
      >
        {selectedJobId ? (
          <CreateCandidateForm
            workspaceId={
              workspaceId
            }
            jobId={
              selectedJobId
            }
            onCreated={
              createdCandidate
            }
            onCancel={() =>
              setModal(null)
            }
          />
        ) : (
          <p className="text-label">
            Select a job opening first.
          </p>
        )}
      </RecruitmentModal>
    </div>
  );
}