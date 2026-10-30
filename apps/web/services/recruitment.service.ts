import {
  api,
} from "@/lib/api/client";

import type {
  CandidateCreateRequest,
  CandidateListResponse,
  CandidateResponse,
  CandidateStatus,
  CandidateUpdateRequest,
  InterviewCreateRequest,
  InterviewListResponse,
  InterviewResponse,
  InterviewUpdateRequest,
  JobCreateRequest,
  JobListResponse,
  JobResponse,
  JobStatus,
  JobUpdateRequest,
} from "@/types/recruitment";


const basePath = (
  workspaceId: string,
) =>
  `/workspaces/${workspaceId}/recruitment`;


export const recruitmentService = {
  async listJobs(
    workspaceId: string,
    status?:
      JobStatus | null,
  ): Promise<JobListResponse> {
    return api.get<JobListResponse>(
      `${basePath(
        workspaceId,
      )}/jobs`,
      {
        query: {
          status:
            status ?? null,
        },
      },
    );
  },


  async createJob(
    workspaceId: string,
    request:
      JobCreateRequest,
  ): Promise<JobResponse> {
    return api.post<JobResponse>(
      `${basePath(
        workspaceId,
      )}/jobs`,
      request,
    );
  },


  async updateJob(
    workspaceId: string,
    jobId: string,
    request:
      JobUpdateRequest,
  ): Promise<JobResponse> {
    return api.patch<JobResponse>(
      `${basePath(
        workspaceId,
      )}/jobs/${jobId}`,
      request,
    );
  },


  async listCandidates(
    workspaceId: string,
    options: {
      jobId?:
        string | null;

      status?:
        CandidateStatus | null;
    } = {},
  ): Promise<CandidateListResponse> {
    return api.get<CandidateListResponse>(
      `${basePath(
        workspaceId,
      )}/candidates`,
      {
        query: {
          job_id:
            options.jobId ??
            null,

          status:
            options.status ??
            null,
        },
      },
    );
  },


  async createCandidate(
    workspaceId: string,
    request:
      CandidateCreateRequest,
  ): Promise<CandidateResponse> {
    return api.post<CandidateResponse>(
      `${basePath(
        workspaceId,
      )}/candidates`,
      request,
    );
  },


  async updateCandidate(
    workspaceId: string,
    candidateId: string,
    request:
      CandidateUpdateRequest,
  ): Promise<CandidateResponse> {
    return api.patch<CandidateResponse>(
      `${basePath(
        workspaceId,
      )}/candidates/${candidateId}`,
      request,
    );
  },


  async listInterviews(
    workspaceId: string,
    candidateId?:
      string | null,
  ): Promise<InterviewListResponse> {
    return api.get<InterviewListResponse>(
      `${basePath(
        workspaceId,
      )}/interviews`,
      {
        query: {
          candidate_id:
            candidateId ??
            null,
        },
      },
    );
  },


  async createInterview(
    workspaceId: string,
    request:
      InterviewCreateRequest,
  ): Promise<InterviewResponse> {
    return api.post<InterviewResponse>(
      `${basePath(
        workspaceId,
      )}/interviews`,
      request,
    );
  },


  async updateInterview(
    workspaceId: string,
    interviewId: string,
    request:
      InterviewUpdateRequest,
  ): Promise<InterviewResponse> {
    return api.patch<InterviewResponse>(
      `${basePath(
        workspaceId,
      )}/interviews/${interviewId}`,
      request,
    );
  },


  async deleteInterview(
    workspaceId: string,
    interviewId: string,
  ): Promise<void> {
    await api.delete<unknown>(
      `${basePath(
        workspaceId,
      )}/interviews/${interviewId}`,
    );
  },
};