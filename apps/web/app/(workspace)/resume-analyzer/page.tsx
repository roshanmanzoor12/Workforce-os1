"use client";

import { useState } from "react";

import {
  FileSearch,
  FileText,
  Upload,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

export default function ResumeAnalyzerPage() {
  const [fileName, setFileName] =
    useState<string | null>(null);

  return (
    <div
      style={{
        maxWidth: 1200,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Resume Analyzer"
        description="Review candidate resumes and prepare structured hiring insights."
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "minmax(0,1fr) 420px",
          gap: 16,
        }}
      >
        <section className="panel">
          <div className="panel-header">
            <h2 className="text-section-title">
              Upload Resume
            </h2>
          </div>

          <div
            className="panel-body"
            style={{
              minHeight: 440,
              display: "grid",
              placeItems: "center",
            }}
          >
            <label
              style={{
                width: "100%",
                maxWidth: 520,
                padding: 40,
                border:
                  "1px dashed var(--color-border-strong)",
                borderRadius: 10,
                textAlign: "center",
                cursor: "pointer",
                background:
                  "var(--color-surface-subtle)",
              }}
            >
              <Upload
                size={34}
                style={{
                  margin: "0 auto",
                  color: "#b17b00",
                }}
              />

              <h3
                style={{
                  marginTop: 14,
                  fontSize: 14,
                }}
              >
                Choose a resume
              </h3>

              <p
                className="text-muted"
                style={{
                  marginTop: 6,
                  fontSize: 11,
                }}
              >
                PDF or DOCX
              </p>

              <input
                type="file"
                accept=".pdf,.doc,.docx"
                className="sr-only"
                onChange={(event) =>
                  setFileName(
                    event.target.files?.[0]
                      ?.name ?? null,
                  )
                }
              />
            </label>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2 className="text-section-title">
              Analysis
            </h2>
          </div>

          <div className="panel-body">
            {fileName ? (
              <>
                <div
                  style={{
                    display: "flex",
                    gap: 10,
                    alignItems: "center",
                    padding: 12,
                    borderRadius: 8,
                    background:
                      "var(--color-surface-subtle)",
                  }}
                >
                  <FileText size={20} />

                  <div>
                    <strong
                      style={{
                        display: "block",
                        fontSize: 12,
                      }}
                    >
                      {fileName}
                    </strong>

                    <span className="text-label">
                      Ready for analysis
                    </span>
                  </div>
                </div>

                <Button
                  style={{
                    width: "100%",
                    marginTop: 14,
                  }}
                >
                  <FileSearch size={15} />
                  Analyze Resume
                </Button>

                <div
                  style={{
                    marginTop: 20,
                  }}
                >
                  <StatusBadge variant="warning">
                    Backend AI required
                  </StatusBadge>

                  <p
                    className="text-muted"
                    style={{
                      marginTop: 8,
                      fontSize: 11,
                      lineHeight: 1.6,
                    }}
                  >
                    File selection works now.
                    Resume analysis will connect
                    to the backend later.
                  </p>
                </div>
              </>
            ) : (
              <div
                style={{
                  padding: "60px 20px",
                  textAlign: "center",
                }}
              >
                <FileSearch
                  size={32}
                  style={{
                    margin: "0 auto",
                    color: "#96999d",
                  }}
                />

                <p
                  className="text-muted"
                  style={{
                    marginTop: 12,
                    fontSize: 11,
                  }}
                >
                  Upload a resume to begin.
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}