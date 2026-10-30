"use client";

import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Eye,
  EyeOff,
  Laptop2,
  LockKeyhole,
  Mail,
  MonitorCheck,
  ShieldCheck,
  TrendingUp,
  Users,
} from "lucide-react";
import Link from "next/link";
import {
  useRouter,
} from "next/navigation";
import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import {
  WorkforceLogo,
} from "@/components/app-shell/workforce-logo";

import {
  startGoogleOAuth,
} from "@/lib/auth/google-oauth";

import {
  getAuthSession,
} from "@/lib/auth/session";

import {
  authService,
  persistLogin,
} from "@/services/auth.service";


const activityItems = [
  {
    id: 1,
    name:
      "Marvin McKinney",
    action:
      "Active in Figma",
    time:
      "Now",
    tone:
      "online",
  },
  {
    id: 2,
    name:
      "Theresa Webb",
    action:
      "Reviewing payroll",
    time:
      "1m",
    tone:
      "online",
  },
  {
    id: 3,
    name:
      "Ralph Edwards",
    action:
      "Working in VS Code",
    time:
      "2m",
    tone:
      "online",
  },
  {
    id: 4,
    name:
      "Dianne Russell",
    action:
      "Marketing dashboard",
    time:
      "4m",
    tone:
      "online",
  },
  {
    id: 5,
    name:
      "Cameron Williamson",
    action:
      "Idle",
    time:
      "8m",
    tone:
      "idle",
  },
];


const productivityBars = [
  42,
  58,
  54,
  72,
  64,
  81,
  76,
  88,
  79,
  92,
  84,
  89,
];


export function LoginClient() {
  const router =
    useRouter();

  const [
    identifier,
    setIdentifier,
  ] =
    useState("");

  const [
    password,
    setPassword,
  ] =
    useState("");

  const [
    rememberMe,
    setRememberMe,
  ] =
    useState(false);

  const [
    showPassword,
    setShowPassword,
  ] =
    useState(false);

  const [
    submitting,
    setSubmitting,
  ] =
    useState(false);

  const [
    googleSubmitting,
    setGoogleSubmitting,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(
      null,
    );


  useEffect(() => {
    const session =
      getAuthSession();

    if (
      session?.accessToken
    ) {
      router.replace(
        "/home",
      );
    }
  }, [
    router,
  ]);


  async function handleSubmit(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError(
      null,
    );

    const normalizedIdentifier =
      identifier.trim();

    if (
      normalizedIdentifier.length <
      3
    ) {
      setError(
        "Enter your email address or username.",
      );

      return;
    }

    if (!password) {
      setError(
        "Enter your password.",
      );

      return;
    }

    setSubmitting(
      true,
    );

    try {
      const result =
        await authService.login({
          identifier:
            normalizedIdentifier,

          password,

          remember_me:
            rememberMe,
        });

      persistLogin(
        result,
        rememberMe,
      );

      router.replace(
        "/home",
      );

      router.refresh();

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to sign in. Please try again.",
      );

    } finally {
      setSubmitting(
        false,
      );
    }
  }


  async function handleGoogleLogin() {
    if (
      submitting ||
      googleSubmitting
    ) {
      return;
    }

    setError(
      null,
    );

    setGoogleSubmitting(
      true,
    );

    try {
      await startGoogleOAuth(
        "login",
        rememberMe,
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Google sign in could not be started.",
      );

      setGoogleSubmitting(
        false,
      );
    }
  }


  return (
    <main className="auth-login-page">
      <section className="auth-login-panel">
        <div className="auth-login-content">
          <div
            style={{
              marginBottom:
                34,
            }}
          >
            <WorkforceLogo />
          </div>


          <div className="auth-login-heading">
            <div className="auth-login-security">
              <ShieldCheck
                size={15}
              />

              Secure workforce access
            </div>

            <h1>
              Welcome back
            </h1>

            <p>
              Sign in to continue to
              your Workforce OS
              workspace.
            </p>
          </div>


          <form
            onSubmit={
              handleSubmit
            }
          >
            <label className="auth-field">
              <span>
                Email or username
              </span>

              <div className="auth-input-wrap">
                <Mail
                  size={16}
                  className="auth-input-icon"
                />

                <input
                  className="auth-input"
                  type="text"
                  autoComplete="username"
                  value={
                    identifier
                  }
                  placeholder="name@company.com"
                  disabled={
                    submitting ||
                    googleSubmitting
                  }
                  onChange={(
                    event,
                  ) =>
                    setIdentifier(
                      event.target
                        .value,
                    )
                  }
                />
              </div>
            </label>


            <label className="auth-field">
              <div className="auth-password-heading">
                <span>
                  Password
                </span>

                <Link
                  href="/forgot-password"
                  className="auth-link"
                >
                  Forgot password?
                </Link>
              </div>

              <div className="auth-input-wrap">
                <LockKeyhole
                  size={16}
                  className="auth-input-icon"
                />

                <input
                  className="auth-input"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  autoComplete="current-password"
                  value={
                    password
                  }
                  placeholder="Enter password"
                  disabled={
                    submitting ||
                    googleSubmitting
                  }
                  onChange={(
                    event,
                  ) =>
                    setPassword(
                      event.target
                        .value,
                    )
                  }
                />

                <button
                  type="button"
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                  disabled={
                    submitting ||
                    googleSubmitting
                  }
                  onClick={() =>
                    setShowPassword(
                      (
                        current,
                      ) =>
                        !current,
                    )
                  }
                  className="auth-password-toggle"
                >
                  {showPassword ? (
                    <EyeOff
                      size={16}
                    />
                  ) : (
                    <Eye
                      size={16}
                    />
                  )}
                </button>
              </div>
            </label>


            <div className="auth-login-options">
              <label className="auth-remember-label">
                <input
                  type="checkbox"
                  checked={
                    rememberMe
                  }
                  disabled={
                    submitting ||
                    googleSubmitting
                  }
                  onChange={(
                    event,
                  ) =>
                    setRememberMe(
                      event.target
                        .checked,
                    )
                  }
                />

                Remember me
              </label>
            </div>


            {error ? (
              <div
                className="auth-error"
                role="alert"
              >
                {error}
              </div>
            ) : null}


            <button
              className="auth-submit"
              type="submit"
              disabled={
                submitting ||
                googleSubmitting
              }
            >
              {submitting ? (
                <>
                  <span className="auth-submit-spinner" />

                  Signing in...
                </>
              ) : (
                <>
                  Sign In

                  <ArrowRight
                    size={16}
                  />
                </>
              )}
            </button>
          </form>


          <div className="auth-divider">
            <span />

            <small>
              or continue with
            </small>

            <span />
          </div>


          <button
            type="button"
            className="auth-google-button"
            disabled={
              submitting ||
              googleSubmitting
            }
            onClick={() => {
              void handleGoogleLogin();
            }}
          >
            <span className="auth-google-mark">
              G
            </span>

            {googleSubmitting
              ? "Opening Google..."
              : "Continue with Google"}
          </button>


          <p className="auth-create-account">
            Don&apos;t have an
            account?{" "}

            <Link
              href="/signup"
              className="auth-link"
            >
              Create account
            </Link>
          </p>
        </div>
      </section>


      <aside className="auth-preview-panel">
        <div className="auth-preview-background-grid" />

        <div className="auth-preview-orb auth-preview-orb--one" />
        <div className="auth-preview-orb auth-preview-orb--two" />

        <div className="auth-saas-preview">
          <div className="auth-saas-copy">
            <div className="auth-preview-kicker">
              <span className="auth-live-dot" />

              Workforce intelligence
            </div>

            <h2>
              Your entire workforce.
              One operating system.
            </h2>

            <p>
              Run employees,
              attendance, activity,
              devices, productivity
              and operations from a
              single connected
              workspace.
            </p>
          </div>


          <div className="auth-dashboard-stage">
            <div className="auth-floating-card auth-floating-card--employees">
              <div className="auth-floating-icon">
                <Users
                  size={15}
                />
              </div>

              <div>
                <span>
                  Employees online
                </span>

                <strong>
                  328
                </strong>
              </div>

              <div className="auth-positive">
                +12.4%
              </div>
            </div>


            <div className="auth-floating-card auth-floating-card--device">
              <div className="auth-floating-icon">
                <MonitorCheck
                  size={15}
                />
              </div>

              <div>
                <span>
                  Device health
                </span>

                <strong>
                  94%
                </strong>
              </div>

              <CheckCircle2
                size={16}
                className="auth-check-icon"
              />
            </div>


            <div className="auth-workforce-window">
              <div className="auth-window-topbar">
                <div className="auth-window-logo">
                  <div className="auth-window-logo-mark">
                    W
                  </div>

                  <span>
                    Workforce OS
                  </span>
                </div>

                <div className="auth-window-status">
                  <span className="auth-live-dot" />

                  Live
                </div>
              </div>


              <div className="auth-window-body">
                <div className="auth-window-sidebar">
                  <SidebarItem
                    active
                  >
                    <Activity
                      size={13}
                    />
                  </SidebarItem>

                  <SidebarItem>
                    <Users
                      size={13}
                    />
                  </SidebarItem>

                  <SidebarItem>
                    <Clock3
                      size={13}
                    />
                  </SidebarItem>

                  <SidebarItem>
                    <Laptop2
                      size={13}
                    />
                  </SidebarItem>
                </div>


                <div className="auth-window-main">
                  <div className="auth-mini-header">
                    <div>
                      <span>
                        Live workforce
                      </span>

                      <strong>
                        Operations overview
                      </strong>
                    </div>

                    <small>
                      Today
                    </small>
                  </div>


                  <div className="auth-mini-metrics">
                    <MiniMetric
                      label="Active"
                      value="272"
                      meta="+8.2%"
                    />

                    <MiniMetric
                      label="Attendance"
                      value="96.8%"
                      meta="+2.1%"
                    />

                    <MiniMetric
                      label="Productivity"
                      value="82.4%"
                      meta="+4.8%"
                    />
                  </div>


                  <div className="auth-mini-grid">
                    <div className="auth-productivity-card">
                      <div className="auth-card-heading">
                        <div>
                          <span>
                            Productivity
                          </span>

                          <strong>
                            Weekly trend
                          </strong>
                        </div>

                        <TrendingUp
                          size={15}
                        />
                      </div>


                      <div className="auth-productivity-chart">
                        {productivityBars.map(
                          (
                            height,
                            index,
                          ) => (
                            <span
                              key={
                                index
                              }
                              style={{
                                height:
                                  `${height}%`,

                                animationDelay:
                                  `${index * 80}ms`,
                              }}
                            />
                          ),
                        )}
                      </div>


                      <div className="auth-chart-labels">
                        <span>
                          Mon
                        </span>

                        <span>
                          Tue
                        </span>

                        <span>
                          Wed
                        </span>

                        <span>
                          Thu
                        </span>

                        <span>
                          Fri
                        </span>
                      </div>
                    </div>


                    <div className="auth-activity-card">
                      <div className="auth-card-heading">
                        <div>
                          <span>
                            Activity
                          </span>

                          <strong>
                            Live feed
                          </strong>
                        </div>

                        <span className="auth-live-dot" />
                      </div>


                      <div className="auth-activity-feed-window">
                        <div className="auth-activity-feed-track">
                          {[
                            ...activityItems,
                            ...activityItems,
                          ].map(
                            (
                              item,
                              index,
                            ) => (
                              <ActivityRow
                                key={`${item.id}-${index}`}
                                name={
                                  item.name
                                }
                                action={
                                  item.action
                                }
                                time={
                                  item.time
                                }
                                tone={
                                  item.tone
                                }
                              />
                            ),
                          )}
                        </div>
                      </div>
                    </div>
                  </div>


                  <div className="auth-device-row">
                    <div className="auth-device-summary">
                      <div className="auth-device-icon">
                        <Laptop2
                          size={15}
                        />
                      </div>

                      <div>
                        <span>
                          Monitored
                          devices
                        </span>

                        <strong>
                          412 endpoints
                        </strong>
                      </div>
                    </div>


                    <div className="auth-device-statuses">
                      <StatusPill
                        label="Healthy"
                        value="388"
                        status="healthy"
                      />

                      <StatusPill
                        label="Attention"
                        value="17"
                        status="warning"
                      />

                      <StatusPill
                        label="Offline"
                        value="7"
                        status="offline"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>


            <div className="auth-floating-card auth-floating-card--attendance">
              <div className="auth-floating-icon">
                <Clock3
                  size={15}
                />
              </div>

              <div>
                <span>
                  Attendance
                </span>

                <strong>
                  96.8%
                </strong>
              </div>
            </div>
          </div>


          <div className="auth-preview-footer">
            <div>
              <ShieldCheck
                size={14}
              />

              Role-based access
            </div>

            <div>
              <Activity
                size={14}
              />

              Live operations
            </div>

            <div>
              <MonitorCheck
                size={14}
              />

              Device visibility
            </div>
          </div>
        </div>
      </aside>
    </main>
  );
}


function SidebarItem({
  children,
  active = false,
}: {
  children:
    React.ReactNode;

  active?:
    boolean;
}) {
  return (
    <div
      className={
        active
          ? "auth-mini-sidebar-item auth-mini-sidebar-item--active"
          : "auth-mini-sidebar-item"
      }
    >
      {children}
    </div>
  );
}


function MiniMetric({
  label,
  value,
  meta,
}: {
  label:
    string;

  value:
    string;

  meta:
    string;
}) {
  return (
    <div className="auth-mini-metric">
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {meta}
      </small>
    </div>
  );
}


function ActivityRow({
  name,
  action,
  time,
  tone,
}: {
  name:
    string;

  action:
    string;

  time:
    string;

  tone:
    string;
}) {
  return (
    <div className="auth-activity-row">
      <span
        className={
          tone ===
          "online"
            ? "auth-activity-avatar auth-activity-avatar--online"
            : "auth-activity-avatar auth-activity-avatar--idle"
        }
      >
        {name
          .split(" ")
          .map(
            (
              part,
            ) =>
              part[0],
          )
          .join("")
          .slice(
            0,
            2,
          )}
      </span>

      <div>
        <strong>
          {name}
        </strong>

        <span>
          {action}
        </span>
      </div>

      <small>
        {time}
      </small>
    </div>
  );
}


function StatusPill({
  label,
  value,
  status,
}: {
  label:
    string;

  value:
    string;

  status:
    | "healthy"
    | "warning"
    | "offline";
}) {
  return (
    <div className="auth-device-pill">
      <span
        className={
          `auth-device-pill-dot auth-device-pill-dot--${status}`
        }
      />

      <div>
        <strong>
          {value}
        </strong>

        <span>
          {label}
        </span>
      </div>
    </div>
  );
}