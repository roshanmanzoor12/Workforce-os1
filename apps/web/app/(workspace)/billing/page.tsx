"use client";

import { api, ApiError } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";
import WorkspaceBillingPage from "./workspace/page";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import type {
  ReactNode,
} from "react";

import {
  AlertCircle,
  ArrowRight,
  Building2,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronRight,
  CreditCard,
  Download,
  FileText,
  HardDrive,
  Loader2,
  Mail,
  Monitor,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";

/*
 * Account billing uses the shared authenticated API client.
 * Payment status and permissions are always verified by the server.
 * Workspace access uses the workspace billing owner's subscription.
 */

type Tab =
  | "Overview"
  | "Plans"
  | "Subscription"
  | "Invoices"
  | "Payment methods"
  | "Usage";

type PlanCode =
  | "free"
  | "starter"
  | "professional"
  | "business";

type InvoiceFilter =
  | "all"
  | "paid"
  | "pending";

type BillingInterval =
  | "month"
  | "year";

interface BillingPlan {
  code: PlanCode;
  display_name: string;
  workspace_limit: number;
  member_limit_per_workspace: number;
  monitoring_enabled: boolean;
  live_screen_enabled: boolean;
  advanced_analytics_enabled: boolean;
}

interface Subscription {
  plan_code: PlanCode;
  status:
    | "none"
    | "trialing"
    | "active"
    | "past_due"
    | "canceled"
    | "unpaid";
  current_period_start: string | null;
  current_period_end: string | null;
}

interface Entitlements {
  plan_code: PlanCode;
  subscription_status: Subscription["status"];
  workspace_limit: number | null;
  workspace_count: number;
  create_workspace: boolean;
  monitoring: boolean;
  live_screen: boolean;
  advanced_analytics: boolean;
}

interface WorkspaceAccess {
  /*
   * This page does not assume fields that were not inspected.
   * Exact workspace creation response can be typed when its
   * current backend schema/source is supplied.
   */
  [key: string]: unknown;
}

interface CatalogPlan {
  code: PlanCode;
  name: string;
  description: string;
  device_limit: number | null;
  workspace_limit: number;
  retention_days: number | null;
  reporting: boolean;
  payroll: boolean;
  channels: boolean;
  meetings: boolean;
  monitoring: boolean;
  live_screen: boolean;
  ai_assistance: boolean;
  monthly_amount_minor: number | null;
  yearly_amount_minor: number | null;
  currency: string;
  checkout_enabled: boolean;
}

interface PaymentMethod {
  id: string;
  brand: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  is_default: boolean;
}

interface InvoiceLine {
  description: string;
  quantity: number;
  amount_minor: number;
}

interface Invoice {
  account_name: string | null;
  invoice_email: string | null;
  billing_address: string[];
  id: string;
  number: string;
  issued_at: string;
  due_at: string | null;
  paid_at: string | null;
  period_start: string | null;
  period_end: string | null;
  description: string;
  status:
    | "draft"
    | "open"
    | "paid"
    | "void"
    | "uncollectible";
  currency: string;
  subtotal_minor: number;
  tax_minor: number;
  total_minor: number;
  amount_due_minor: number;
  lines: InvoiceLine[];
}

interface UsageMetric {
  used: number | null;
  limit: number | null;
}

interface BillingDetails {
  billing_exempt: boolean;
  /*
   * PROPOSED response from GET /billing/details.
   *
   * All private values must belong to the authenticated billing
   * account. Never accept an arbitrary customer ID from the browser.
   */
  can_manage_billing: boolean;
  trial_eligible: boolean;
  trial_end: string | null;
  billing_interval: BillingInterval;
  cancel_at_period_end: boolean;
  access_status:
    | "active"
    | "trialing"
    | "restricted"
    | "none";
  invoice_email: string | null;
  account_name: string | null;
  billing_address: string[];
  seller_name: string;
  seller_address: string[];
  logo_url: string | null;
  tax_id: string | null;
  catalog: CatalogPlan[];
  payment_methods: PaymentMethod[];
  invoices: Invoice[];
  usage: {
    devices: UsageMetric;
    workspaces: UsageMetric;
    storage_bytes: UsageMetric;
    ai_requests: UsageMetric;
  };
}

interface BillingData {
  plans: BillingPlan[];
  subscription: Subscription;
  entitlements: Entitlements;
  workspaceAccess: WorkspaceAccess;
  details: BillingDetails | null;
}

interface CheckoutResponse {
  url: string;
}

interface PortalResponse {
  url: string;
}

const TABS: Tab[] = [
  "Overview",
  "Plans",
  "Subscription",
  "Invoices",
  "Payment methods",
  "Usage",
];

/*
 * Requested package specification.
 *
 * This is product copy, not the source of actual permissions.
 * Backend entitlements remain authoritative.
 *
 * Existing backend code mapping:
 *
 * starter      -> Starter
 * professional -> Plus
 * business     -> Advanced
 *
 * Advanced device and retention limits were not specified.
 * Prices were not specified.
 */
const REQUESTED_PLANS: CatalogPlan[] = [
  {
    code: "starter",
    name: "Starter",
    description: "Core tools for one workspace.",
    device_limit: 30,
    workspace_limit: 1,
    retention_days: 30,
    reporting: true,
    payroll: true,
    channels: false,
    meetings: false,
    monitoring: true,
    live_screen: true,
    ai_assistance: false,
    monthly_amount_minor: null,
    yearly_amount_minor: null,
    currency: "USD",
    checkout_enabled: false,
  },
  {
    code: "professional",
    name: "Plus",
    description: "More devices and AI workspace insights.",
    device_limit: 50,
    workspace_limit: 1,
    retention_days: 40,
    reporting: true,
    payroll: true,
    channels: true,
    meetings: false,
    monitoring: true,
    live_screen: true,
    ai_assistance: true,
    monthly_amount_minor: null,
    yearly_amount_minor: null,
    currency: "USD",
    checkout_enabled: false,
  },
  {
    code: "business",
    name: "Advanced",
    description: "Manage work across three workspaces.",
    device_limit: null,
    workspace_limit: 3,
    retention_days: null,
    reporting: true,
    payroll: true,
    channels: true,
    meetings: false,
    monitoring: true,
    live_screen: true,
    ai_assistance: true,
    monthly_amount_minor: null,
    yearly_amount_minor: null,
    currency: "USD",
    checkout_enabled: false,
  },
];

class BillingError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "BillingError";
    this.status = status;
  }
}

async function getJSON<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  try {
    return await api.request<T>(`/billing${path}`, options);
  } catch (cause) {
    if (cause instanceof ApiError) {
      throw new BillingError(cause.message, cause.status);
    }
    throw cause;
  }
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Karachi",
  }).format(date);
}

function formatMoney(
  amountMinor: number | null | undefined,
  currency = "USD",
): string {
  if (
    amountMinor === null ||
    amountMinor === undefined ||
    !Number.isFinite(amountMinor)
  ) {
    return "Price not configured";
  }

  try {
    const formatter = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency.toUpperCase(),
    });

    const digits =
      formatter.resolvedOptions().maximumFractionDigits ?? 2;

    return formatter.format(amountMinor / 10 ** digits);
  } catch {
    return "Invalid currency";
  }
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }

  const units = ["KB", "MB", "GB", "TB"];
  let amount = value / 1024;
  let index = 0;

  while (amount >= 1024 && index < units.length - 1) {
    amount /= 1024;
    index += 1;
  }

  return `${amount.toFixed(1)} ${units[index]}`;
}

function planName(code: PlanCode): string {
  return (
    REQUESTED_PLANS.find((plan) => plan.code === code)?.name ??
    "Free"
  );
}

function statusLabel(value: string): string {
  const labels: Record<string, string> = {
    none: "No subscription",
    active: "Active",
    trialing: "Trial",
    past_due: "Past due",
    canceled: "Canceled",
    unpaid: "Unpaid",
    paid: "Paid",
    open: "Pending",
    draft: "Draft",
    void: "Void",
    uncollectible: "Uncollectible",
    restricted: "Restricted",
  };

  return labels[value] ?? value;
}

function safeImageURL(value: string | null): string | undefined {
  if (!value || typeof window === "undefined") {
    return undefined;
  }

  try {
    const url = new URL(value, window.location.origin);

    if (
      url.origin === window.location.origin ||
      url.protocol === "https:"
    ) {
      return url.href;
    }
  } catch {
    return undefined;
  }

  return undefined;
}

function redirectToStripe(value: string): void {
  const url = new URL(value);

  const allowedHosts = [
    "checkout.stripe.com",
    "billing.stripe.com",
    "invoice.stripe.com",
  ];

  if (
    url.protocol !== "https:" ||
    !allowedHosts.includes(url.hostname)
  ) {
    throw new Error("The server returned an invalid Stripe URL.");
  }

  window.location.assign(url.href);
}

function Badge({
  value,
}: {
  value: string;
}) {
  const tone =
    ["active", "paid", "trialing"].includes(value)
      ? "good"
      : ["past_due", "unpaid", "restricted", "uncollectible"].includes(
          value,
        )
        ? "danger"
        : "neutral";

  return (
    <span className={`bill-badge ${tone}`}>
      <span aria-hidden="true" />
      {statusLabel(value)}
    </span>
  );
}

function Panel({
  title,
  action,
  children,
  className = "",
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`bill-panel ${className}`}>
      {title && (
        <div className="bill-panel-heading">
          <h2>{title}</h2>
          {action}
        </div>
      )}

      {children}
    </section>
  );
}

function Empty({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="bill-empty">
      <FileText size={24} aria-hidden="true" />
      <p>{children}</p>
    </div>
  );
}

function UsageBar({
  label,
  metric,
  bytes = false,
  unlimited = false,
}: {
  label: string;
  metric: UsageMetric;
  bytes?: boolean;
  unlimited?: boolean;
}) {
  const hasUsage = metric.used !== null;
  const percentage =
    metric.used !== null && metric.limit !== null && metric.limit > 0
      ? Math.min(100, Math.max(0, (metric.used / metric.limit) * 100))
      : 0;

  const used = metric.used === null
    ? "Unavailable"
    : bytes
      ? formatBytes(metric.used)
      : metric.used.toLocaleString();

  const limit = unlimited ? "Unlimited" : metric.limit === null
    ? "Not configured"
    : bytes
      ? formatBytes(metric.limit)
      : metric.limit.toLocaleString();

  return (
    <div className="bill-usage">
      <div className="bill-between">
        <strong>{label}</strong>
        <span>
          {used} / {limit}
        </span>
      </div>

      <div
        className="bill-meter"
        role={
          hasUsage && metric.limit !== null && metric.limit > 0
            ? "progressbar"
            : undefined
        }
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={
          hasUsage && metric.limit !== null && metric.limit > 0
            ? metric.limit
            : undefined
        }
        aria-valuenow={
          hasUsage && metric.limit !== null && metric.limit > 0
            ? Math.min(metric.used ?? 0, metric.limit)
            : undefined
        }
        aria-valuetext={`${used} of ${limit}`}
      >
        <span style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

export default function Page() {
  const { mode } = useWorkspace();
  return mode === "workspace" ? <WorkspaceBillingPage /> : <AccountBillingPage />;
}

function AccountBillingPage() {
  const { refreshBilling } = useWorkspace();
  const [tab, setTab] = useState<Tab>("Overview");
  const [interval, setInterval] =
    useState<BillingInterval>("month");
  const [data, setData] = useState<BillingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] =
    useState<InvoiceFilter>("all");
  const [dateRange, setDateRange] = useState("12");
  const [selected, setSelected] = useState<string[]>([]);
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [trialCheckout, setTrialCheckout] = useState(false);
  const [checkoutPlan, setCheckoutPlan] =
    useState<CatalogPlan | null>(null);

  const invoiceDialog = useRef<HTMLDialogElement>(null);
  const checkoutDialog = useRef<HTMLDialogElement>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError("");
    setNotice("");

    try {
      let details: BillingDetails | null = null;

      try {
        details = await getJSON<BillingDetails>("/details", { signal });
      } catch (cause) {
        if (cause instanceof BillingError && [404, 501, 503].includes(cause.status)) {
          if (!signal?.aborted) {
            setNotice(cause.status === 503
              ? "Payment services are unavailable or not configured. Please retry later."
              : "Payment services have not been installed yet.");
          }
        } else {
          throw cause;
        }
      }

      // Read after reconciliation so all sections use the refreshed state.
      const [plansResponse, subscription, entitlements, workspaceAccess] =
        await Promise.all([
          getJSON<{ plans: BillingPlan[] }>("/plans", { signal }),
          getJSON<Subscription>("/subscription", { signal }),
          getJSON<Entitlements>("/entitlements", { signal }),
          getJSON<WorkspaceAccess>("/workspace-access", { signal }),
        ]);

      if (signal?.aborted) return;

      // Reconciliation above has verified the selected trial/paid plan.
      // Update the shared sidebar/selector state as well as this page.
      await refreshBilling();
      if (signal?.aborted) return;

      setData({ plans: plansResponse.plans, subscription, entitlements, workspaceAccess, details });
      setInterval(details?.billing_interval ?? "month");
      setSelected([]);
    } catch (cause) {
      if (!signal?.aborted) setError(errorMessage(cause));
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [refreshBilling]);

  useEffect(() => {
    const controller = new AbortController();

    void load(controller.signal);

    return () => controller.abort();
  }, [load]);

  useEffect(() => {
    if (invoice && !invoiceDialog.current?.open) {
      invoiceDialog.current?.showModal();
    }
  }, [invoice]);

  useEffect(() => {
    if (checkoutPlan && !checkoutDialog.current?.open) {
      checkoutDialog.current?.showModal();
    }
  }, [checkoutPlan]);

  const details = data?.details ?? null;
  const subscription = data?.subscription ?? null;
  const entitlements = data?.entitlements ?? null;

  const catalog = details?.catalog.length
    ? details.catalog
    : REQUESTED_PLANS;

  const currentPlan = subscription
    ? catalog.find(
        (plan) => plan.code === subscription.plan_code,
      )
    : undefined;

  const currentName = details?.billing_exempt ? "Unlimited" :
    currentPlan?.name ??
    (subscription ? planName(subscription.plan_code) : "—");

  const defaultCard =
    details?.payment_methods.find((card) => card.is_default) ??
    details?.payment_methods[0];

  const invoices = details?.invoices ?? [];

  const restricted = details
    ? details.access_status === "restricted"
    : subscription
      ? ["past_due", "unpaid"].includes(subscription.status)
      : false;

  const canManage = details?.can_manage_billing === true;

  const visibleInvoices = invoices
    .filter((item) => {
      const matchesQuery = [
        item.number,
        item.description,
      ]
        .join(" ")
        .toLowerCase()
        .includes(query.toLowerCase());

      const matchesStatus =
        filter === "all" ||
        (filter === "paid" && item.status === "paid") ||
        (filter === "pending" && item.status === "open");

      let matchesDate = true;

      if (dateRange !== "all") {
        const start = new Date();

        start.setMonth(
          start.getMonth() - Number(dateRange),
        );

        matchesDate =
          new Date(item.issued_at).getTime() >= start.getTime();
      }

      return matchesQuery && matchesStatus && matchesDate;
    })
    .sort(
      (first, second) =>
        new Date(second.issued_at).getTime() -
        new Date(first.issued_at).getTime(),
    );

  const allVisibleSelected =
    visibleInvoices.length > 0 &&
    visibleInvoices.every((item) => selected.includes(item.id));

  async function openPortal() {
    if (!canManage || busy) {
      return;
    }

    setBusy("portal");
    setError("");

    try {
      const result = await getJSON<PortalResponse>(
        "/portal",
        {
          method: "POST",
          body: JSON.stringify({}),
        },
      );

      redirectToStripe(result.url);
    } catch (portalError) {
      setError(errorMessage(portalError));
    } finally {
      setBusy(null);
    }
  }

  async function beginCheckout(withTrial: boolean) {
    if (!checkoutPlan || !canManage || busy) {
      return;
    }

    setBusy("checkout");
    setError("");

    try {
      /*
       * The server must:
       *
       * - Ignore client-supplied prices.
       * - Recheck trial eligibility.
       * - Require payment method collection for a trial.
       * - Use setup mode for a one-time, card-only 72-hour trial.
       * - Prevent duplicate active subscriptions.
       * - Return a Stripe-hosted Checkout URL.
       *
       * A checkout redirect must never unlock features locally.
       */
      const result = await getJSON<CheckoutResponse>(
        "/checkout",
        {
          method: "POST",
          body: JSON.stringify({
            plan_code: checkoutPlan.code,
            interval,
            with_trial: withTrial,
          }),
        },
      );

      redirectToStripe(result.url);
    } catch (checkoutError) {
      setError(errorMessage(checkoutError));
    } finally {
      setBusy(null);
    }
  }

  async function downloadPDF(item: Invoice) {
    const blob = await api.request<Blob>(
      `/billing/invoices/${encodeURIComponent(item.id)}/pdf`,
      { method: "GET" },
      { responseType: "blob" },
    );

    if (!blob.type.toLowerCase().includes("application/pdf")) {
      throw new Error("The invoice endpoint did not return a PDF.");
    }

    const objectURL = URL.createObjectURL(blob);
    const anchor = document.createElement("a");

    anchor.href = objectURL;
    anchor.download =
      `${item.number.replace(/[^a-zA-Z0-9_-]/g, "_")}.pdf`;

    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();

    window.setTimeout(() => {
      URL.revokeObjectURL(objectURL);
    }, 1000);
  }

  async function downloadInvoices(items: Invoice[]) {
    if (busy || !items.length) {
      return;
    }

    setBusy("download");
    setError("");

    try {
      for (const item of items) {
        await downloadPDF(item);
      }
    } catch (downloadError) {
      setError(errorMessage(downloadError));
    } finally {
      setBusy(null);
    }
  }

  function toggleInvoice(id: string) {
    setSelected((previous) =>
      previous.includes(id)
        ? previous.filter((value) => value !== id)
        : [...previous, id],
    );
  }

  function toggleAllVisible() {
    const visibleIDs = visibleInvoices.map((item) => item.id);

    setSelected((previous) =>
      allVisibleSelected
        ? previous.filter((id) => !visibleIDs.includes(id))
        : Array.from(new Set([...previous, ...visibleIDs])),
    );
  }

  function closeInvoice() {
    invoiceDialog.current?.close();
    setInvoice(null);
  }

  function closeCheckout() {
    checkoutDialog.current?.close();
    setCheckoutPlan(null);
  }

  function renderInvoiceTable(items: Invoice[], selectable: boolean) {
    return (
      <div className="bill-table-scroll">
        <table className="bill-table">
          <thead>
            <tr>
              {selectable && (
                <th className="bill-check-cell">
                  <input
                    type="checkbox"
                    aria-label="Select all visible invoices"
                    checked={allVisibleSelected}
                    onChange={toggleAllVisible}
                    disabled={!items.length}
                  />
                </th>
              )}
              <th>Invoice ID</th>
              <th>Date</th>
              <th>Description</th>
              <th>Amount</th>
              <th>Status</th>
              <th className="bill-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                {selectable && (
                  <td className="bill-check-cell">
                    <input
                      type="checkbox"
                      aria-label={`Select invoice ${item.number}`}
                      checked={selected.includes(item.id)}
                      onChange={() => toggleInvoice(item.id)}
                    />
                  </td>
                )}

                <td>
                  <strong>{item.number}</strong>
                </td>
                <td>{formatDate(item.issued_at)}</td>
                <td>{item.description}</td>
                <td>
                  {formatMoney(item.total_minor, item.currency)}
                </td>
                <td>
                  <Badge value={item.status} />
                </td>
                <td>
                  <div className="bill-row-actions">
                    <button
                      type="button"
                      className="bill-link"
                      onClick={() => setInvoice(item)}
                    >
                      View
                    </button>

                    <button
                      type="button"
                      className="bill-link"
                      disabled={busy !== null}
                      onClick={() => {
                        void downloadInvoices([item]);
                      }}
                      aria-label={`Download ${item.number} as PDF`}
                    >
                      <Download size={14} />
                      PDF
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!items.length && (
          <Empty>
            {details
              ? "No invoices match this view."
              : "Invoices will appear after the billing backend is connected."}
          </Empty>
        )}
      </div>
    );
  }

  function renderUsage() {
    if (!details) {
      return (
        <Empty>
          Device, storage, and AI usage are not available yet.
        </Empty>
      );
    }

    return (
      <div className="bill-usage-list">
        <UsageBar
          label="Registered devices"
          metric={details.usage.devices}
          unlimited={details.billing_exempt}
        />
        <UsageBar
          label="Workspaces"
          metric={details.usage.workspaces}
          unlimited={details.billing_exempt}
        />
        <UsageBar
          label="Stored data"
          metric={details.usage.storage_bytes}
          bytes
        />
        <UsageBar
          label="AI requests"
          metric={details.usage.ai_requests}
        />
      </div>
    );
  }

  const portalButton = (
    label: string,
    primary = false,
  ) => (
    <button
      type="button"
      className={`bill-button ${primary ? "primary" : ""}`}
      disabled={!canManage || busy !== null}
      onClick={() => {
        void openPortal();
      }}
      title={
        !details
          ? "Requires the billing backend extension"
          : !canManage
            ? "Billing administrator permission is required"
            : undefined
      }
    >
      {busy === "portal" && (
        <Loader2 size={15} className="bill-spin" />
      )}
      {label}
    </button>
  );

  return (
    <main className="billing-page">
      <header className="bill-header">
        <div className="bill-between bill-heading-row">
          <div>
            <h1>Account Billing</h1>
            <p>
              Manage your account subscription, payments and workspace allowance.
            </p>
          </div>

          <button
            type="button"
            className="bill-button primary"
            onClick={() => setTab("Plans")}
          >
            View plans
            <ArrowRight size={15} />
          </button>
        </div>

        <nav className="bill-tabs" aria-label="Billing sections">
          {TABS.map((item) => (
            <button
              key={item}
              type="button"
              aria-current={tab === item ? "page" : undefined}
              className={tab === item ? "active" : ""}
              onClick={() => setTab(item)}
            >
              {item}
            </button>
          ))}
        </nav>
      </header>

      {error && (
        <div className="bill-message error" role="alert">
          <AlertCircle size={18} />
          <span>{error}</span>
          <button
            type="button"
            className="bill-link"
            onClick={() => {
              void load();
            }}
            disabled={loading || busy !== null}
          >
            Retry
          </button>
        </div>
      )}

      {notice && (
        <div className="bill-message" role="status">
          <AlertCircle size={18} />
          <span>{notice}</span>
        </div>
      )}

      {details?.billing_exempt && (
        <div className="bill-message" role="status">
          <ShieldCheck size={20} />
          <span>Unlimited billing access: no subscription expiry, workspace or device billing cap. All plan features are included. No trial or payment is required.</span>
        </div>
      )}

      {subscription?.status === "trialing" && details?.trial_end && (
        <div className="bill-message" role="status">
          <ShieldCheck size={20} />
          <div>
            <strong>{currentName} trial active</strong>
            <p>
              {entitlements?.workspace_limit ?? currentPlan?.workspace_limit ?? "—"} workspace allowance
              {currentPlan?.device_limit != null ? ` · ${currentPlan.device_limit} registered devices` : ""}.
              {" "}Your selected plan’s features are available until {formatDate(details.trial_end)}.
              {" "}Use the workspace selector to create or open your workspace.
            </p>
          </div>
        </div>
      )}

      {restricted && (
        <div className="bill-message warning" role="alert">
          <AlertCircle size={20} />

          <div>
            <strong>Your workspace subscription needs attention.</strong>
            <p>
              Renew your subscription to restore access to paid
              workspace features.
            </p>
          </div>

          {portalButton("Renew subscription", true)}
        </div>
      )}

      {loading ? (
        <div className="bill-loading" role="status">
          <Loader2 size={23} className="bill-spin" />
          <p>Loading billing details…</p>
        </div>
      ) : (
        <>
          {tab === "Overview" && (
            <>
              <div className="bill-overview-grid">
                <Panel className="bill-highlight">
                  <div className="bill-plan-summary">
                    <div className="bill-icon large yellow">
                      <Building2 size={30} />
                    </div>

                    <div>
                      <div className="bill-inline">
                        <h2>{currentName}</h2>
                        {subscription && (
                          <Badge value={subscription.status} />
                        )}
                      </div>

                      <p>Your workspace account subscription</p>

                      <div className="bill-meta">
                        <span>
                          <CalendarDays size={16} />
                          {details?.billing_exempt ? "No payment required" : details
                            ? details.billing_interval === "year"
                              ? "Yearly billing"
                              : "Monthly billing"
                            : "Billing cycle unavailable"}
                        </span>

                        <span>
                          <RefreshCw size={16} />
                          Period ends:{" "}
                          {formatDate(
                            subscription?.current_period_end,
                          )}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bill-actions">
                    {portalButton("Manage subscription", true)}

                    <button
                      type="button"
                      className="bill-button"
                      onClick={() => setTab("Plans")}
                    >
                      Compare plans
                    </button>
                  </div>
                </Panel>

                <Panel title="Billing status">
                  <div className="bill-icon green">
                    <CheckCircle2 size={23} />
                  </div>

                  <h3 className="bill-status-title">
                    {restricted
                      ? "Payment needs attention"
                      : subscription?.status === "trialing"
                        ? "Your trial is running"
                        : subscription?.status === "active"
                          ? "Subscription active"
                          : "Review your subscription"}
                  </h3>

                  <p>
                    {details?.trial_end
                      ? `Trial ends ${formatDate(details.trial_end)}.`
                      : "Your verified subscription status is shown here."}
                  </p>
                </Panel>

                <Panel title="Payment method">
                  <div className="bill-icon">
                    <CreditCard size={23} />
                  </div>

                  <h3 className="bill-status-title">
                    {defaultCard
                      ? `${defaultCard.brand} ending ${defaultCard.last4}`
                      : "No payment method available"}
                  </h3>

                  <p>
                    {defaultCard
                      ? `Expires ${String(
                          defaultCard.exp_month,
                        ).padStart(2, "0")}/${defaultCard.exp_year}`
                      : "Manage cards securely through Stripe."}
                  </p>

                  <div className="bill-top-gap">
                    {portalButton("Update method")}
                  </div>
                </Panel>
              </div>

              <div className="bill-main-grid">
                <Panel
                  title="Recent invoices"
                  action={
                    <button
                      type="button"
                      className="bill-link"
                      onClick={() => setTab("Invoices")}
                    >
                      View all
                      <ChevronRight size={15} />
                    </button>
                  }
                >
                  {renderInvoiceTable(
                    [...invoices]
                      .sort(
                        (a, b) =>
                          new Date(b.issued_at).getTime() -
                          new Date(a.issued_at).getTime(),
                      )
                      .slice(0, 3),
                    false,
                  )}
                </Panel>

                <Panel
                  title="Workspace usage"
                  action={<span className="bill-muted">Current period</span>}
                >
                  {renderUsage()}

                  <button
                    type="button"
                    className="bill-button bill-top-gap"
                    onClick={() => setTab("Usage")}
                  >
                    View usage
                    <ChevronRight size={14} />
                  </button>
                </Panel>
              </div>

              <div className="bill-main-grid">
                <Panel title="Workspace entitlements">
                  <div className="bill-entitlement-row">
                    <div className="bill-icon">
                      <Building2 size={23} />
                    </div>

                    <div className="bill-grow">
                      <strong>Workspace allowance</strong>
                      <p>
                        {entitlements
                          ? entitlements.workspace_limit === null
                            ? `${entitlements.workspace_count} workspaces used · Unlimited allowance`
                            : `${entitlements.workspace_count} of ${entitlements.workspace_limit} workspaces used`
                          : "Not available"}
                      </p>
                    </div>

                    <span className="bill-small-tag">
                      {entitlements?.create_workspace
                        ? "Creation available"
                        : "Creation unavailable"}
                    </span>
                  </div>

                  <div className="bill-feature-strip">
                    <span>
                      Monitoring
                      <strong>
                        {entitlements?.monitoring
                          ? "Enabled"
                          : "Unavailable"}
                      </strong>
                    </span>

                    <span>
                      Live screen
                      <strong>
                        {entitlements?.live_screen
                          ? "Enabled"
                          : "Unavailable"}
                      </strong>
                    </span>

                    <span>
                      Advanced analytics
                      <strong>
                        {entitlements?.advanced_analytics
                          ? "Enabled"
                          : "Unavailable"}
                      </strong>
                    </span>
                  </div>
                </Panel>

                <Panel title="Billing preferences">
                  <div className="bill-detail-row">
                    <Mail size={19} />
                    <div>
                      <strong>Invoice email</strong>
                      <p>{details?.invoice_email ?? "Not available"}</p>
                    </div>
                  </div>

                  <div className="bill-detail-row">
                    <CalendarDays size={19} />
                    <div>
                      <strong>Displayed timezone</strong>
                      <p>Asia/Karachi</p>
                    </div>
                  </div>

                  {portalButton("Manage billing details")}
                </Panel>
              </div>
            </>
          )}

          {tab === "Plans" && details?.billing_exempt && (
            <Panel title="Unlimited billing access">
              <p>This account already includes all plan features. No trial or paid plan is needed.</p>
            </Panel>
          )}
          {tab === "Plans" && !details?.billing_exempt && (
            <Panel>
              <div className="bill-between bill-section-intro">
                <div>
                  <h2>Choose your workspace plan</h2>
                  <p>
                    Compare device limits, workspace access and
                    included tools.
                  </p>
                </div>

                <div
                  className="bill-cycle"
                  role="group"
                  aria-label="Billing interval"
                >
                  <button
                    type="button"
                    aria-pressed={interval === "month"}
                    className={interval === "month" ? "active" : ""}
                    onClick={() => setInterval("month")}
                  >
                    Monthly
                  </button>

                  <button
                    type="button"
                    aria-pressed={interval === "year"}
                    className={interval === "year" ? "active" : ""}
                    onClick={() => setInterval("year")}
                  >
                    Yearly
                  </button>
                </div>
              </div>

              {!details && (
                <p className="bill-plan-note">
                  Requested package specification. Your current
                  backend limits remain authoritative until the
                  plan configuration is updated.
                </p>
              )}

              <div className="bill-plan-grid">
                {catalog.map((plan) => {
                  const isCurrent =
                    subscription?.plan_code === plan.code;

                  const amount =
                    interval === "month"
                      ? plan.monthly_amount_minor
                      : plan.yearly_amount_minor;

                  const available =
                    canManage &&
                    plan.checkout_enabled &&
                    amount !== null;

                  return (
                    <article
                      key={plan.code}
                      className={`bill-plan-card ${
                        plan.code === "professional"
                          ? "featured"
                          : ""
                      }`}
                    >
                      <div className="bill-between">
                        <div className="bill-icon yellow">
                          {plan.ai_assistance
                            ? <Sparkles size={24} />
                            : <Building2 size={24} />}
                        </div>

                        {isCurrent && (
                          <span className="bill-small-tag">
                            Current plan
                          </span>
                        )}
                      </div>

                      <h3>{plan.name}</h3>
                      <p>{plan.description}</p>

                      <div className="bill-price">
                        <strong>
                          {formatMoney(amount, plan.currency)}
                        </strong>

                        {amount !== null && (
                          <span>
                            / {interval === "month" ? "month" : "year"}
                          </span>
                        )}
                      </div>

                      <button
                        type="button"
                        className={`bill-button ${
                          plan.code === "professional"
                            ? "primary"
                            : ""
                        }`}
                        disabled={!available || busy !== null}
                        onClick={() => {
                          if (
                            subscription?.status === "active"
                          ) {
                            void openPortal();
                          } else {
                            setTrialCheckout(false);
                            setCheckoutPlan(plan);
                          }
                        }}
                      >
                        {isCurrent && subscription?.status === "active"
                          ? "Manage plan"
                          : "Choose plan"}
                        <ArrowRight size={14} />
                      </button>

                      {details?.trial_eligible && (
                        <button
                          type="button"
                          className="bill-button"
                          style={{ marginTop: 10 }}
                          disabled={!canManage || busy !== null || plan.device_limit === null || plan.retention_days === null}
                          onClick={() => {
                            setTrialCheckout(true);
                            setCheckoutPlan(plan);
                          }}
                        >
                          Start 3-day free trial
                        </button>
                      )}

                      <ul className="bill-benefits">
                        {[
                          plan.device_limit === null
                            ? "Device limit to be configured"
                            : `${plan.device_limit} registered devices`,
                          `${plan.workspace_limit} ${
                            plan.workspace_limit === 1
                              ? "workspace"
                              : "workspaces"
                          }`,
                          plan.retention_days === null
                            ? "Retention period to be configured"
                            : `${plan.retention_days} days data retention`,
                          ...(plan.reporting ? ["Reports"] : []),
                          ...(plan.payroll ? ["Payroll"] : []),
                          ...(plan.monitoring
                            ? ["Employee activity monitoring"]
                            : []),
                          ...(plan.live_screen
                            ? ["Live screen monitoring"]
                            : []),
                          ...(plan.channels ? ["Team channels"] : []),
                          ...(plan.meetings ? ["Meetings"] : []),
                          ...(plan.ai_assistance
                            ? ["AI reporting and workspace insights"]
                            : []),
                        ].map((feature) => (
                          <li key={feature}>
                            <span>
                              <Check size={12} />
                            </span>
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </article>
                  );
                })}
              </div>

              <div className="bill-table-scroll bill-top-gap">
                <table className="bill-table comparison">
                  <thead>
                    <tr>
                      <th>Feature</th>
                      {catalog.map((plan) => (
                        <th key={plan.code}>{plan.name}</th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {[
                      {
                        label: "Registered devices",
                        value: (plan: CatalogPlan) =>
                          plan.device_limit ?? "To be configured",
                      },
                      {
                        label: "Workspace allowance",
                        value: (plan: CatalogPlan) =>
                          plan.workspace_limit,
                      },
                      {
                        label: "Data retention",
                        value: (plan: CatalogPlan) =>
                          plan.retention_days === null
                            ? "To be configured"
                            : `${plan.retention_days} days`,
                      },
                      {
                        label: "Reports and payroll",
                        value: (plan: CatalogPlan) =>
                          plan.reporting && plan.payroll
                            ? "Included"
                            : "Not included",
                      },
                      {
                        label: "Team channels",
                        value: (plan: CatalogPlan) =>
                          plan.channels ? "Included" : "Not included",
                      },
                      {
                        label: "AI workspace assistance",
                        value: (plan: CatalogPlan) =>
                          plan.ai_assistance
                            ? "Included"
                            : "Not included",
                      },
                      {
                        label: "Meetings",
                        value: (plan: CatalogPlan) =>
                          plan.meetings ? "Included" : "Not included",
                      },
                    ].map((row) => (
                      <tr key={row.label}>
                        <td>{row.label}</td>
                        {catalog.map((plan) => (
                          <td key={plan.code}>
                            {row.value(plan)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="bill-security-note">
                <ShieldCheck size={19} />
                <p>
                  Eligible first-time accounts can choose a
                  three-day trial without an automatic trial-end charge. Checkout displays the exact
                  recurring price and payment terms before confirmation.
                </p>
              </div>
            </Panel>
          )}

          {tab === "Subscription" && (
            <>
              <div className="bill-two-columns">
                <Panel
                  title="Your workspace subscription"
                  className="bill-highlight"
                >
                  <div className="bill-plan-summary">
                    <div className="bill-icon large yellow">
                      <Building2 size={29} />
                    </div>

                    <div>
                      <div className="bill-inline">
                        <h2>{currentName}</h2>
                        {subscription && (
                          <Badge value={subscription.status} />
                        )}
                      </div>

                      <p>
                        {details
                          ? details.billing_interval === "year"
                            ? "Yearly billing"
                            : "Monthly billing"
                          : "Billing cycle unavailable"}
                      </p>
                    </div>
                  </div>

                  <div className="bill-date-grid">
                    <div>
                      <span>Period started</span>
                      <strong>
                        {formatDate(subscription?.current_period_start)}
                      </strong>
                    </div>

                    <div>
                      <span>Period ends</span>
                      <strong>
                        {details?.billing_exempt ? "No expiry" : formatDate(subscription?.current_period_end)}
                      </strong>
                    </div>

                    <div>
                      <span>Trial ends</span>
                      <strong>
                        {details?.trial_end
                          ? formatDate(details.trial_end)
                          : "No active trial"}
                      </strong>
                    </div>
                  </div>

                  <div className="bill-actions">
                    {portalButton("Manage plan", true)}
                    {portalButton("Change billing cycle")}
                  </div>
                </Panel>

                <Panel title="Subscription details">
                  <div className="bill-detail-row">
                    <div className="bill-icon">
                      <CreditCard size={23} />
                    </div>

                    <div className="bill-grow">
                      <strong>Payment method</strong>
                      <p>
                        {defaultCard
                          ? `${defaultCard.brand} ending ${defaultCard.last4}`
                          : "Not available"}
                      </p>
                    </div>

                    {portalButton("Update")}
                  </div>

                  <div className="bill-detail-row">
                    <div className="bill-icon">
                      <Mail size={22} />
                    </div>

                    <div className="bill-grow">
                      <strong>Invoice email</strong>
                      <p>{details?.invoice_email ?? "Not available"}</p>
                    </div>

                    {portalButton("Update")}
                  </div>
                </Panel>
              </div>

              <Panel title="Plan benefits">
                <div className="bill-benefit-grid">
                  <div>
                    <Monitor size={24} />
                    <strong>Device allowance</strong>
                    <p>
                      {details?.billing_exempt ? "Unlimited registered devices" : currentPlan?.device_limit !== null &&
                      currentPlan?.device_limit !== undefined
                        ? `${currentPlan.device_limit} registered devices`
                        : "Not configured"}
                    </p>
                  </div>

                  <div>
                    <Building2 size={24} />
                    <strong>Workspaces</strong>
                    <p>
                      {details?.billing_exempt ? "Unlimited" : entitlements?.workspace_limit ?? "—"} available
                    </p>
                  </div>

                  <div>
                    <HardDrive size={24} />
                    <strong>Data retention</strong>
                    <p>
                      {currentPlan?.retention_days !== null &&
                      currentPlan?.retention_days !== undefined
                        ? `${currentPlan.retention_days} days`
                        : "Not configured"}
                    </p>
                  </div>

                  <div>
                    <Sparkles size={24} />
                    <strong>AI assistance</strong>
                    <p>
                      {details
                        ? currentPlan?.ai_assistance
                          ? "Included"
                          : "Not included"
                        : "Not available"}
                    </p>
                  </div>
                </div>
              </Panel>

              <div className="bill-two-columns">
                <Panel title="Renewal settings">
                  <div className="bill-detail-row">
                    <CalendarDays size={24} />

                    <div className="bill-grow">
                      <strong>Automatic renewal</strong>
                      <p>
                        {!details
                          ? "Renewal settings are not available."
                          : details.cancel_at_period_end
                            ? `Cancellation scheduled for ${formatDate(
                                subscription?.current_period_end,
                              )}.`
                            : "Renewal follows your Stripe subscription settings."}
                      </p>
                    </div>
                  </div>

                  {portalButton("Manage renewal")}
                </Panel>

                <Panel title="Cancel subscription">
                  <p>
                    Review cancellation terms and the exact access
                    end date in the secure billing portal.
                  </p>

                  <div className="bill-top-gap">
                    {portalButton("Manage cancellation")}
                  </div>
                </Panel>
              </div>
            </>
          )}

          {tab === "Invoices" && (
            <div className="bill-invoice-grid">
              <Panel title="Invoices">
                <div className="bill-invoice-toolbar">
                  <label className="bill-search">
                    <Search size={17} aria-hidden="true" />
                    <input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Search invoice ID or description…"
                      aria-label="Search invoices"
                    />
                  </label>

                  <select
                    value={dateRange}
                    onChange={(event) =>
                      setDateRange(event.target.value)
                    }
                    aria-label="Invoice date range"
                  >
                    <option value="12">Last 12 months</option>
                    <option value="6">Last 6 months</option>
                    <option value="3">Last 3 months</option>
                    <option value="all">All dates</option>
                  </select>
                </div>

                <div className="bill-between bill-filter-row">
                  <div className="bill-filters">
                    {(["all", "paid", "pending"] as const).map(
                      (value) => (
                        <button
                          key={value}
                          type="button"
                          className={filter === value ? "active" : ""}
                          aria-pressed={filter === value}
                          onClick={() => setFilter(value)}
                        >
                          {value.charAt(0).toUpperCase() +
                            value.slice(1)}
                        </button>
                      ),
                    )}
                  </div>

                  <button
                    type="button"
                    className="bill-button primary"
                    disabled={!selected.length || busy !== null}
                    onClick={() => {
                      void downloadInvoices(
                        invoices.filter((item) =>
                          selected.includes(item.id),
                        ),
                      );
                    }}
                  >
                    {busy === "download"
                      ? <Loader2 size={16} className="bill-spin" />
                      : <Download size={16} />}
                    Download selected
                  </button>
                </div>

                {renderInvoiceTable(visibleInvoices, true)}

                <div className="bill-table-footer">
                  <span>
                    {visibleInvoices.length} invoice
                    {visibleInvoices.length === 1 ? "" : "s"}
                  </span>
                  <span>{selected.length} selected</span>
                </div>
              </Panel>

              <Panel title="Billing details">
                <div className="bill-detail-row">
                  <Mail size={22} />

                  <div>
                    <strong>Invoice email</strong>
                    <p>{details?.invoice_email ?? "Not available"}</p>
                    <small>
                      Invoices and receipts are sent to this address.
                    </small>
                  </div>
                </div>

                {portalButton("Edit billing details")}

                <div className="bill-detail-row">
                  <Building2 size={22} />

                  <div>
                    <strong>Billing account</strong>
                    <p>{details?.account_name ?? "Not available"}</p>

                    {details?.billing_address.map((line, index) => (
                      <p key={`${line}-${index}`}>{line}</p>
                    ))}
                  </div>
                </div>

                <p className="bill-muted">
                  Invoice dates, totals and payment status come
                  from the billing server.
                </p>
              </Panel>
            </div>
          )}

          {tab === "Payment methods" && (
            <div className="bill-two-columns">
              <div className="bill-stack">
                <Panel title="Saved payment methods">
                  {details?.payment_methods.length ? (
                    details.payment_methods.map((card) => (
                      <div
                        className={`bill-card-row ${
                          card.is_default ? "default" : ""
                        }`}
                        key={card.id}
                      >
                        <div className="bill-icon">
                          <CreditCard size={26} />
                        </div>

                        <div className="bill-grow">
                          <strong>
                            {card.brand} ending {card.last4}
                          </strong>

                          {card.is_default && (
                            <span className="bill-default-label">
                              Default
                            </span>
                          )}

                          <p>
                            Expires{" "}
                            {String(card.exp_month).padStart(2, "0")}
                            /{card.exp_year}
                          </p>
                        </div>

                        {portalButton("Manage")}
                      </div>
                    ))
                  ) : (
                    <Empty>
                      {details
                        ? "No saved payment methods."
                        : "Saved payment methods are not connected yet."}
                    </Empty>
                  )}

                  <div className="bill-top-gap">
                    {portalButton("Add payment method", true)}
                  </div>
                </Panel>

                <Panel title="Billing address">
                  <div className="bill-detail-row">
                    <Building2 size={25} />

                    <div className="bill-grow">
                      <strong>
                        {details?.account_name ?? "Not available"}
                      </strong>

                      {details?.billing_address.length ? (
                        details.billing_address.map((line, index) => (
                          <p key={`${line}-${index}`}>{line}</p>
                        ))
                      ) : (
                        <p>No billing address available.</p>
                      )}
                    </div>
                  </div>

                  {portalButton("Edit address")}
                </Panel>
              </div>

              <Panel title="Add or update a payment method">
                <div className="bill-payment-intro">
                  <div className="bill-icon large yellow">
                    <ShieldCheck size={31} />
                  </div>

                  <h3>Secure card management</h3>

                  <p>
                    Add Visa, Mastercard or another supported card
                    through Stripe’s secure payment form.
                  </p>

                  <p>
                    WorkforceOS displays the card brand, last four
                    digits and expiry date. Full card numbers and
                    CVC are not stored in this application.
                  </p>

                  {portalButton("Open secure payment form", true)}
                </div>
              </Panel>
            </div>
          )}

          {tab === "Usage" && (
            <>
              <div className="bill-two-columns">
                <Panel title="Current workspace plan">
                  <div className="bill-plan-summary">
                    <div className="bill-icon large yellow">
                      <Building2 size={29} />
                    </div>

                    <div>
                      <div className="bill-inline">
                        <h2>{currentName}</h2>
                        {subscription && (
                          <Badge value={subscription.status} />
                        )}
                      </div>

                      <p>
                        {formatDate(subscription?.current_period_start)}
                        {" – "}
                        {details?.billing_exempt ? "No expiry" : formatDate(subscription?.current_period_end)}
                      </p>
                    </div>
                  </div>
                </Panel>

                <Panel title="Current period usage">
                  {renderUsage()}
                </Panel>
              </div>

              <Panel title="Usage and access">
                <div className="bill-table-scroll">
                  <table className="bill-table">
                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th>Used</th>
                        <th>Included</th>
                        <th>Notes</th>
                      </tr>
                    </thead>

                    <tbody>
                      <tr>
                        <td>Registered devices</td>
                        <td>
                          {details?.usage.devices.used ?? "—"}
                        </td>
                        <td>
                          {details?.billing_exempt ? "Unlimited" : details?.usage.devices.limit ??
                            "Not configured"}
                        </td>
                        <td>
                          Device registration is enforced by the server.
                        </td>
                      </tr>

                      <tr>
                        <td>Workspaces</td>
                        <td>
                          {entitlements?.workspace_count ?? "—"}
                        </td>
                        <td>
                          {details?.billing_exempt ? "Unlimited" : entitlements?.workspace_limit ?? "—"}
                        </td>
                        <td>
                          Allowance belongs to the billing account.
                        </td>
                      </tr>

                      <tr>
                        <td>Data retention</td>
                        <td>—</td>
                        <td>
                          {currentPlan?.retention_days !== null &&
                          currentPlan?.retention_days !== undefined
                            ? `${currentPlan.retention_days} days`
                            : "Not configured"}
                        </td>
                        <td>
                          Retention and backup execution require
                          server-side jobs.
                        </td>
                      </tr>

                      <tr>
                        <td>Live screen monitoring</td>
                        <td>—</td>
                        <td>
                          {entitlements?.live_screen
                            ? "Enabled"
                            : "Unavailable"}
                        </td>
                        <td>
                          Requires a connected employee agent and
                          an authorized monitoring session.
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </Panel>

              <div className="bill-security-note">
                <Monitor size={20} />
                <p>
                  Monitoring must show its active status to the
                  employee. Capture stops when the authorized work
                  session ends. Device logout and disconnect handling
                  are implemented in the agent and backend.
                </p>
              </div>
            </>
          )}
        </>
      )}

      <dialog
        ref={invoiceDialog}
        className="bill-dialog invoice-dialog"
        aria-labelledby="invoice-title"
        onCancel={closeInvoice}
        onClose={() => setInvoice(null)}
      >
        {invoice && (
          <>
            <div className="bill-dialog-heading">
              <h2 id="invoice-title">Invoice preview</h2>

              <button
                type="button"
                className="bill-icon-button"
                aria-label="Close invoice preview"
                onClick={closeInvoice}
              >
                <X size={20} />
              </button>
            </div>

            <article className="bill-invoice-paper">
              <div className="bill-between">
                <div className="bill-invoice-brand">
                  {safeImageURL(details?.logo_url ?? null) ? (
                    <img
                      src={safeImageURL(details?.logo_url ?? null)}
                      alt={`${details?.seller_name ?? "WorkforceOS"} logo`}
                      width={46}
                      height={46}
                    />
                  ) : (
                    <div className="bill-icon yellow">
                      <Building2 size={28} />
                    </div>
                  )}

                  <div>
                    <strong>
                      {details?.seller_name ?? "WorkforceOS"}
                    </strong>

                    {details?.seller_address.map((line, index) => (
                      <p key={`${line}-${index}`}>{line}</p>
                    ))}
                  </div>
                </div>

                <div className="bill-right">
                  <h2>INVOICE</h2>
                  <p>{invoice.number}</p>
                  <Badge value={invoice.status} />
                </div>
              </div>

              <div className="bill-invoice-parties">
                <div>
                  <span>Bill to</span>
                  <strong>
                    {invoice.account_name ?? "Not available"}
                  </strong>
                  <p>{invoice.invoice_email}</p>

                  {invoice.billing_address.map((line, index) => (
                    <p key={`${line}-${index}`}>{line}</p>
                  ))}
                </div>

                <dl>
                  <div>
                    <dt>Issued</dt>
                    <dd>{formatDate(invoice.issued_at)}</dd>
                  </div>
                  <div>
                    <dt>Due</dt>
                    <dd>{formatDate(invoice.due_at)}</dd>
                  </div>
                  <div>
                    <dt>Paid</dt>
                    <dd>{formatDate(invoice.paid_at)}</dd>
                  </div>
                </dl>
              </div>

              {invoice.period_start && invoice.period_end && (
                <p className="bill-plan-note">
                  Service period: {formatDate(invoice.period_start)}
                  {" – "}
                  {formatDate(invoice.period_end)}
                </p>
              )}

              <div className="bill-table-scroll">
                <table className="bill-table">
                  <thead>
                    <tr>
                      <th>Description</th>
                      <th>Quantity</th>
                      <th className="bill-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoice.lines.map((line, index) => (
                      <tr key={`${line.description}-${index}`}>
                        <td>{line.description}</td>
                        <td>{line.quantity}</td>
                        <td className="bill-right">
                          {formatMoney(
                            line.amount_minor,
                            invoice.currency,
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <dl className="bill-invoice-totals">
                <div>
                  <dt>Subtotal</dt>
                  <dd>
                    {formatMoney(
                      invoice.subtotal_minor,
                      invoice.currency,
                    )}
                  </dd>
                </div>
                <div>
                  <dt>Tax</dt>
                  <dd>
                    {formatMoney(
                      invoice.tax_minor,
                      invoice.currency,
                    )}
                  </dd>
                </div>
                <div className="total">
                  <dt>Total</dt>
                  <dd>
                    {formatMoney(
                      invoice.total_minor,
                      invoice.currency,
                    )}
                  </dd>
                </div>
                <div>
                  <dt>Amount due</dt>
                  <dd>
                    {formatMoney(
                      invoice.amount_due_minor,
                      invoice.currency,
                    )}
                  </dd>
                </div>
              </dl>

              {details?.tax_id && (
                <p className="bill-muted">
                  Tax registration: {details.tax_id}
                </p>
              )}

              <p className="bill-invoice-footer">
                Thank you for using WorkforceOS.
              </p>
            </article>

            <div className="bill-dialog-actions">
              <button
                type="button"
                className="bill-button"
                onClick={closeInvoice}
              >
                Close
              </button>

              <button
                type="button"
                className="bill-button primary"
                disabled={busy !== null}
                onClick={() => {
                  void downloadInvoices([invoice]);
                }}
              >
                <Download size={16} />
                Download PDF
              </button>
            </div>
          </>
        )}
      </dialog>

      <dialog
        ref={checkoutDialog}
        className="bill-dialog checkout-dialog"
        aria-labelledby="checkout-title"
        onCancel={closeCheckout}
        onClose={() => setCheckoutPlan(null)}
      >
        {checkoutPlan && (
          <>
            <div className="bill-dialog-heading">
              <h2 id="checkout-title">
                Start {checkoutPlan.name}
              </h2>

              <button
                type="button"
                className="bill-icon-button"
                aria-label="Close checkout options"
                onClick={closeCheckout}
                disabled={busy === "checkout"}
              >
                <X size={20} />
              </button>
            </div>

            <div className="bill-checkout-body">
              {!trialCheckout && <div className="bill-checkout-price">
                <strong>
                  {formatMoney(
                    interval === "month"
                      ? checkoutPlan.monthly_amount_minor
                      : checkoutPlan.yearly_amount_minor,
                    checkoutPlan.currency,
                  )}
                </strong>
                <span>
                  per {interval === "month" ? "month" : "year"}
                </span>
              </div>}

              {trialCheckout && details?.trial_eligible && (
                <div className="bill-trial-box">
                  <h3>Try it free for 3 days</h3>
                  <p>
                    Add your card securely in Stripe. No subscription
                    charge today. Your trial lasts 72 hours after card
                    verification. After it ends, choose and pay for a
                    plan to restore access. No automatic trial-end
                    charge. Your bank may show a temporary verification hold.
                  </p>

                  <button
                    type="button"
                    className="bill-button primary"
                    disabled={busy !== null}
                    onClick={() => {
                      void beginCheckout(true);
                    }}
                  >
                    {busy === "checkout" && (
                      <Loader2 size={16} className="bill-spin" />
                    )}
                    Continue with 3-day trial
                  </button>
                </div>
              )}

              {!trialCheckout && <>
              <p>
                Start a paid subscription now. Access is granted
                after the server verifies payment.
              </p>

              <button
                type="button"
                className="bill-button"
                disabled={busy !== null}
                onClick={() => {
                  void beginCheckout(false);
                }}
              >
                Pay and subscribe now
                <ArrowRight size={16} />
              </button>
              </>}

              <div className="bill-security-note">
                <ShieldCheck size={18} />
                <p>Payment details are collected securely by Stripe.</p>
              </div>
            </div>
          </>
        )}
      </dialog>

      <style jsx global>{`
        .billing-page {
          --bill-ink: #13213b;
          --bill-muted: #526783;
          --bill-line: #e8e8e4;
          --bill-gold-line: #f1dfb7;
          --bill-yellow: #ffda38;
          --bill-surface: #fffefa;
          color: var(--bill-ink);
          background: #fffcf4;
          padding: 12px;
          min-width: 0;
          font-family: inherit;
          font-size: 13px;
          line-height: 1.5;
          color-scheme: light;
          font-variant-numeric: tabular-nums;
        }

        .billing-page *,
        .bill-dialog * {
          box-sizing: border-box;
        }

        .billing-page ::selection {
          background: #ffe77b;
          color: #13213b;
        }

        .billing-page h1,
        .billing-page h2,
        .billing-page h3,
        .billing-page p,
        .bill-dialog h2,
        .bill-dialog h3,
        .bill-dialog p {
          margin: 0;
        }

        .billing-page h1 {
          font-size: 30px;
          line-height: 1.2;
          font-weight: 750;
          letter-spacing: -0.025em;
        }

        .billing-page h2,
        .bill-dialog h2 {
          font-size: 18px;
          line-height: 1.3;
          font-weight: 700;
          letter-spacing: -0.015em;
        }

        .billing-page h3,
        .bill-dialog h3 {
          font-size: 16px;
          line-height: 1.4;
          font-weight: 700;
        }

        .billing-page p,
        .bill-dialog p {
          color: var(--bill-muted, #526783);
          overflow-wrap: anywhere;
        }

        .billing-page small {
          display: block;
          color: var(--bill-muted);
          margin-top: 6px;
          font-size: 11px;
        }

        .bill-header {
          padding: 16px 14px 0;
          background: var(--bill-surface);
          border: 1px solid var(--bill-gold-line);
          border-radius: 12px;
          margin-bottom: 12px;
        }

        .bill-heading-row {
          gap: 16px;
          padding-bottom: 16px;
        }

        .bill-heading-row p {
          font-size: 14px;
          margin-top: 3px;
        }

        .bill-between {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .bill-tabs {
          display: flex;
          gap: 7px;
          overflow-x: auto;
          padding: 6px 0;
          border-top: 1px solid var(--bill-line);
          scrollbar-width: thin;
          scrollbar-color: #cbbd96 #fffaf0;
        }

        .bill-tabs button {
          flex: 0 0 auto;
          border: 0;
          border-radius: 10px;
          background: transparent;
          padding: 8px 23px;
          min-height: 36px;
          color: #344f74;
          cursor: pointer;
          font: inherit;
          white-space: nowrap;
        }

        .bill-tabs button.active,
        .bill-cycle button.active,
        .bill-filters button.active {
          color: #152139;
          background: var(--bill-yellow);
        }

        .bill-panel {
          min-width: 0;
          padding: 16px;
          border: 1px solid var(--bill-gold-line);
          border-radius: 11px;
          background: var(--bill-surface);
          margin-bottom: 12px;
        }

        .bill-panel-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 16px;
        }

        .bill-panel-heading h2 {
          font-size: 15px;
          font-weight: 650;
        }

        .bill-highlight {
          background: linear-gradient(
            120deg,
            #fff9e5 0%,
            #fffcf0 100%
          );
          border-color: #f0d993;
        }

        .bill-overview-grid {
          display: grid;
          grid-template-columns: 1.65fr 0.9fr 0.95fr;
          gap: 12px;
        }

        .bill-main-grid {
          display: grid;
          grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr);
          gap: 12px;
        }

        .bill-two-columns {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }

        .bill-invoice-grid {
          display: grid;
          grid-template-columns: minmax(0, 2.6fr) minmax(230px, 1fr);
          gap: 12px;
        }

        .bill-plan-summary {
          display: flex;
          align-items: flex-start;
          gap: 16px;
          margin-bottom: 20px;
        }

        .bill-plan-summary h2 {
          font-size: 22px;
        }

        .bill-inline {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 10px;
          margin-bottom: 4px;
        }

        .bill-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 42px;
          height: 42px;
          flex-shrink: 0;
          border-radius: 11px;
          background: #f4f3ef;
          color: #13213b;
        }

        .bill-icon.large {
          width: 66px;
          height: 66px;
          border-radius: 12px;
        }

        .bill-icon.yellow {
          background: #ffe16a;
        }

        .bill-icon.green {
          background: #e5f6df;
          color: #137330;
        }

        .bill-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 12px 20px;
          margin-top: 14px;
          color: var(--bill-muted);
          font-size: 12px;
        }

        .bill-meta span,
        .bill-actions,
        .bill-row-actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .bill-actions {
          flex-wrap: wrap;
          margin-top: 14px;
        }

        .bill-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          min-height: 36px;
          border: 1px solid #73819a;
          border-radius: 8px;
          background: #fffefa;
          color: #13213b;
          padding: 8px 15px;
          font: inherit;
          font-size: 12px;
          line-height: 1.35;
          cursor: pointer;
          text-align: center;
          text-decoration: none;
          transition:
            background-color 140ms ease,
            border-color 140ms ease;
        }

        .bill-button.primary {
          background: #2d353f;
          color: #ffffff;
          border-color: #2d353f;
        }

        .bill-button:hover:not(:disabled) {
          background: #fff3c3;
          border-color: #b6a05e;
        }

        .bill-button.primary:hover:not(:disabled) {
          background: #414b58;
          border-color: #414b58;
        }

        .bill-button:disabled,
        .billing-page button:disabled,
        .bill-dialog button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .billing-page button:focus-visible,
        .billing-page input:focus-visible,
        .billing-page select:focus-visible,
        .bill-dialog button:focus-visible {
          outline: 3px solid #af8100;
          outline-offset: 3px;
        }

        .bill-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          border-radius: 8px;
          padding: 4px 10px;
          font-size: 11px;
          white-space: nowrap;
          line-height: 1.4;
        }

        .bill-badge > span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: currentColor;
        }

        .bill-badge.good {
          color: #176838;
          background: #e1f5e4;
        }

        .bill-badge.danger {
          color: #a12f2b;
          background: #fde9e6;
        }

        .bill-badge.neutral {
          color: #536075;
          background: #eeefef;
        }

        .bill-status-title {
          margin-top: 14px !important;
          margin-bottom: 4px !important;
        }

        .bill-link {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: none;
          border: 0;
          padding: 4px 0;
          color: #214f91;
          font: inherit;
          font-size: 12px;
          cursor: pointer;
          text-underline-offset: 3px;
        }

        .bill-link:hover:not(:disabled) {
          text-decoration: underline;
        }

        .bill-muted {
          color: var(--bill-muted, #526783);
          font-size: 11px;
        }

        .bill-top-gap {
          margin-top: 16px;
        }

        .bill-table-scroll {
          overflow-x: auto;
          scrollbar-width: thin;
          scrollbar-color: #cbbd96 #fffaf0;
        }

        .bill-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 11px;
          text-align: left;
        }

        .bill-table th {
          background: #f3f3f1;
          color: #52627a;
          font-size: 10px;
          font-weight: 600;
          padding: 10px 12px;
          white-space: nowrap;
        }

        .bill-table th:first-child {
          border-radius: 7px 0 0 7px;
        }

        .bill-table th:last-child {
          border-radius: 0 7px 7px 0;
        }

        .bill-table td {
          border-bottom: 1px solid #ecece8;
          padding: 14px 12px;
          vertical-align: middle;
        }

        .bill-table tbody tr:last-child td {
          border-bottom: 0;
        }

        .bill-table td:first-child strong {
          white-space: nowrap;
          font-weight: 600;
        }

        .bill-row-actions {
          justify-content: flex-end;
          white-space: nowrap;
          gap: 14px;
        }

        .bill-check-cell {
          width: 30px;
          padding-right: 0 !important;
        }

        .billing-page input[type="checkbox"] {
          width: 15px;
          height: 15px;
          accent-color: #b68900;
          cursor: pointer;
        }

        .bill-usage-list {
          display: grid;
          gap: 18px;
        }

        .bill-usage .bill-between {
          margin-bottom: 7px;
          gap: 10px;
          font-size: 12px;
        }

        .bill-usage strong {
          font-weight: 550;
        }

        .bill-usage .bill-between > span {
          color: #526783;
          text-align: right;
        }

        .bill-meter {
          height: 9px;
          background: #ecebe6;
          overflow: hidden;
          border-radius: 6px;
        }

        .bill-meter > span {
          display: block;
          height: 100%;
          border-radius: inherit;
          background: #ffd32d;
        }

        .bill-entitlement-row {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .bill-grow {
          flex: 1;
          min-width: 0;
        }

        .bill-small-tag {
          display: inline-flex;
          background: #eef0ec;
          color: #40533b;
          padding: 4px 9px;
          border-radius: 7px;
          font-size: 10px;
        }

        .bill-feature-strip {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 15px;
          margin-top: 20px;
          border-top: 1px solid #e9e6dc;
          padding-top: 15px;
        }

        .bill-feature-strip span {
          display: grid;
          gap: 5px;
          color: #526783;
          font-size: 11px;
        }

        .bill-feature-strip strong {
          color: #13213b;
          font-weight: 550;
          font-size: 12px;
        }

        .bill-detail-row {
          display: flex;
          gap: 14px;
          align-items: flex-start;
          padding: 13px 0;
        }

        .bill-detail-row + .bill-detail-row {
          border-top: 1px solid #ecece8;
        }

        .bill-detail-row > svg {
          flex-shrink: 0;
          margin-top: 2px;
        }

        .bill-detail-row strong {
          font-size: 12px;
          font-weight: 650;
        }

        .bill-detail-row p {
          font-size: 12px;
          margin-top: 3px;
        }

        .bill-section-intro {
          margin-bottom: 16px;
        }

        .bill-section-intro h2 {
          font-size: 21px;
        }

        .bill-section-intro p {
          margin-top: 3px;
          font-size: 12px;
        }

        .bill-cycle {
          display: flex;
          border: 1px solid #e2e2db;
          border-radius: 8px;
          padding: 3px;
          min-width: 182px;
          gap: 3px;
        }

        .bill-cycle button {
          flex: 1;
          border: 0;
          background: transparent;
          border-radius: 6px;
          padding: 6px 15px;
          font: inherit;
          font-size: 12px;
          cursor: pointer;
          color: #405576;
        }

        .bill-plan-note {
          font-size: 12px;
          color: #655827 !important;
          background: #fff8df;
          border-radius: 7px;
          padding: 10px 12px;
          margin-bottom: 14px !important;
        }

        .bill-plan-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
        }

        .bill-plan-card {
          padding: 16px;
          border: 1px solid #eddfbc;
          border-radius: 10px;
          background: #fffefa;
        }

        .bill-plan-card.featured {
          border-color: #efc639;
          background: #fff9e6;
        }

        .bill-plan-card h3 {
          margin-top: 12px;
          font-size: 20px;
        }

        .bill-plan-card > p {
          margin-top: 4px;
          min-height: 38px;
          font-size: 12px;
        }

        .bill-price {
          margin: 16px 0;
          min-height: 33px;
          display: flex;
          align-items: baseline;
          flex-wrap: wrap;
          gap: 5px;
        }

        .bill-price strong {
          font-size: 21px;
          line-height: 1.3;
          letter-spacing: -0.02em;
        }

        .bill-price span {
          color: #526783;
          font-size: 11px;
        }

        .bill-plan-card > .bill-button {
          width: 100%;
        }

        .bill-benefits {
          list-style: none;
          padding: 0;
          margin: 16px 0 0;
          display: grid;
          gap: 9px;
        }

        .bill-benefits li {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          color: #435b7b;
          font-size: 11px;
        }

        .bill-benefits li > span {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          width: 17px;
          height: 17px;
          border-radius: 50%;
          background: #fff0ad;
          color: #2d3a4f;
        }

        .comparison th:not(:first-child),
        .comparison td:not(:first-child) {
          text-align: center;
        }

        .comparison td {
          padding-top: 10px;
          padding-bottom: 10px;
        }

        .bill-security-note {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 15px 2px 2px;
        }

        .bill-security-note > svg {
          flex-shrink: 0;
          color: #6d622e;
        }

        .bill-security-note p {
          color: #57677f;
          font-size: 11px;
          max-width: 80ch;
        }

        .bill-date-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin: 18px 0;
        }

        .bill-date-grid > div {
          display: grid;
          gap: 5px;
          font-size: 11px;
        }

        .bill-date-grid span {
          color: #526783;
        }

        .bill-date-grid strong {
          font-weight: 550;
        }

        .bill-benefit-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 18px;
        }

        .bill-benefit-grid > div {
          display: grid;
          grid-template-columns: 28px 1fr;
          column-gap: 10px;
          align-content: start;
          font-size: 12px;
        }

        .bill-benefit-grid svg {
          grid-row: span 2;
        }

        .bill-benefit-grid strong {
          font-weight: 650;
        }

        .bill-benefit-grid p {
          margin-top: 4px;
          font-size: 11px;
        }

        .bill-invoice-toolbar {
          display: flex;
          gap: 10px;
          margin-bottom: 15px;
        }

        .bill-search {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 9px;
          border: 1px solid #d8dce3;
          border-radius: 7px;
          padding: 0 10px;
          min-width: 0;
          background: #ffffff;
        }

        .bill-search input {
          min-width: 0;
          width: 100%;
          min-height: 35px;
          border: 0;
          background: transparent;
          color: #13213b;
          font: inherit;
          font-size: 11px;
          caret-color: #996f00;
        }

        .bill-search input::placeholder {
          color: #64748b;
        }

        .bill-invoice-toolbar select {
          border: 1px solid #d8dce3;
          border-radius: 7px;
          background: #ffffff;
          color: #344e73;
          padding: 8px 10px;
          font: inherit;
          font-size: 11px;
          max-width: 100%;
        }

        .bill-filter-row {
          flex-wrap: wrap;
          margin-bottom: 16px;
        }

        .bill-filters {
          display: flex;
          gap: 8px;
        }

        .bill-filters button {
          border: 1px solid #dedfdc;
          border-radius: 18px;
          background: #fffefa;
          color: #344f74;
          padding: 6px 17px;
          min-height: 32px;
          font: inherit;
          font-size: 11px;
          cursor: pointer;
        }

        .bill-filters button.active {
          border-color: #ffda38;
        }

        .bill-table-footer {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin-top: 20px;
          font-size: 11px;
          color: #526783;
        }

        .bill-stack {
          min-width: 0;
        }

        .bill-card-row {
          display: flex;
          align-items: center;
          gap: 14px;
          border: 1px solid #e6e6df;
          border-radius: 9px;
          padding: 14px;
          margin-bottom: 10px;
        }

        .bill-card-row.default {
          background: #fffae9;
          border-color: #efdaa0;
        }

        .bill-card-row strong {
          display: block;
          font-size: 13px;
        }

        .bill-card-row p {
          margin-top: 3px;
          font-size: 12px;
        }

        .bill-default-label {
          display: inline-block;
          padding: 1px 8px;
          margin-top: 4px;
          border-radius: 5px;
          background: #ffe99a;
          color: #57450b;
          font-size: 10px;
        }

        .bill-payment-intro {
          display: grid;
          align-content: start;
          justify-items: start;
          gap: 17px;
          padding: 8px 0;
        }

        .bill-payment-intro p {
          max-width: 55ch;
        }

        .bill-payment-intro .bill-button {
          width: 100%;
          margin-top: 6px;
        }

        .bill-empty,
        .bill-loading {
          display: grid;
          justify-items: center;
          align-content: center;
          gap: 10px;
          text-align: center;
          padding: 34px 16px;
          min-height: 150px;
          color: #6b7890;
        }

        .bill-empty p {
          max-width: 48ch;
          font-size: 12px;
        }

        .bill-loading {
          min-height: 320px;
        }

        .bill-message {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          border: 1px solid #e6d5a5;
          background: #fff8e1;
          padding: 12px 14px;
          border-radius: 9px;
          margin-bottom: 12px;
          color: #665321;
          font-size: 12px;
        }

        .bill-message > svg {
          flex-shrink: 0;
          margin-top: 1px;
        }

        .bill-message > span,
        .bill-message > div {
          flex: 1;
        }

        .bill-message p {
          color: inherit;
          margin-top: 3px;
        }

        .bill-message.error {
          border-color: #e8b8b2;
          background: #fff0ed;
          color: #913a30;
        }

        .bill-right {
          text-align: right;
        }

        .bill-dialog {
          --bill-muted: #526783;
          --bill-yellow: #ffda38;
          width: min(760px, calc(100vw - 32px));
          max-height: calc(100dvh - 40px);
          overflow-y: auto;
          border: 1px solid #e4d7b6;
          border-radius: 13px;
          padding: 0;
          background: #fffefa;
          color: #13213b;
          font-family: inherit;
          font-size: 13px;
          line-height: 1.5;
          box-shadow: 0 18px 60px rgb(19 33 59 / 20%);
          scrollbar-width: thin;
          scrollbar-color: #cbbd96 #fffaf0;
        }

        .bill-dialog::backdrop {
          background: rgb(19 33 59 / 45%);
        }

        .bill-dialog-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          padding: 16px 20px;
          border-bottom: 1px solid #e8e5da;
        }

        .bill-icon-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 34px;
          height: 34px;
          border: 1px solid #dfdfd9;
          border-radius: 7px;
          background: #fffefa;
          color: #13213b;
          cursor: pointer;
        }

        .bill-invoice-paper {
          padding: 28px;
        }

        .bill-invoice-paper > .bill-between {
          align-items: flex-start;
          margin-bottom: 30px;
        }

        .bill-invoice-brand {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }

        .bill-invoice-brand img {
          object-fit: contain;
          flex-shrink: 0;
        }

        .bill-invoice-brand strong {
          font-size: 17px;
        }

        .bill-invoice-brand p {
          font-size: 11px;
          margin-top: 2px;
        }

        .bill-invoice-paper > .bill-between > .bill-right p {
          margin: 5px 0 7px;
          font-size: 12px;
        }

        .bill-invoice-parties {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 25px;
          margin-bottom: 24px;
        }

        .bill-invoice-parties > div > span {
          display: block;
          color: #526783;
          font-size: 11px;
          margin-bottom: 6px;
        }

        .bill-invoice-parties p {
          font-size: 12px;
          margin-top: 3px;
        }

        .bill-invoice-parties dl,
        .bill-invoice-totals {
          margin: 0;
        }

        .bill-invoice-parties dl > div,
        .bill-invoice-totals > div {
          display: flex;
          justify-content: space-between;
          gap: 20px;
          padding: 5px 0;
          font-size: 12px;
        }

        .bill-invoice-parties dt,
        .bill-invoice-totals dt {
          color: #526783;
        }

        .bill-invoice-parties dd,
        .bill-invoice-totals dd {
          margin: 0;
          text-align: right;
        }

        .bill-invoice-totals {
          width: min(290px, 100%);
          margin: 22px 0 22px auto;
        }

        .bill-invoice-totals .total {
          border-top: 1px solid #e6d8b5;
          border-bottom: 1px solid #e6d8b5;
          padding: 10px 0;
          margin: 5px 0;
          font-weight: 750;
        }

        .bill-invoice-totals .total dt {
          color: #13213b;
        }

        .bill-invoice-footer {
          border-top: 1px solid #e8e5da;
          padding-top: 16px;
          font-size: 11px;
        }

        .bill-dialog-actions {
          display: flex;
          justify-content: flex-end;
          gap: 9px;
          padding: 15px 20px;
          border-top: 1px solid #e8e5da;
        }

        .checkout-dialog {
          width: min(470px, calc(100vw - 32px));
        }

        .bill-checkout-body {
          display: grid;
          gap: 17px;
          padding: 22px;
        }

        .bill-checkout-price {
          display: flex;
          align-items: baseline;
          flex-wrap: wrap;
          gap: 8px;
        }

        .bill-checkout-price strong {
          font-size: 28px;
          letter-spacing: -0.02em;
        }

        .bill-checkout-price span {
          color: #526783;
          font-size: 12px;
        }

        .bill-trial-box {
          padding: 16px;
          background: #fff8df;
          border: 1px solid #edd58b;
          border-radius: 9px;
        }

        .bill-trial-box p {
          margin: 9px 0 15px;
          font-size: 12px;
        }

        .bill-trial-box .bill-button {
          width: 100%;
        }

        .bill-spin {
          animation: bill-spin 900ms linear infinite;
        }

        @keyframes bill-spin {
          to {
            transform: rotate(360deg);
          }
        }

        @media (min-width: 1450px) {
          .billing-page {
            padding: 16px;
          }

          .bill-panel {
            padding: 20px;
          }
        }

        @media (max-width: 1100px) {
          .bill-overview-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .bill-overview-grid > :first-child {
            grid-column: 1 / -1;
          }

          .bill-main-grid,
          .bill-invoice-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .bill-plan-card {
            padding: 13px;
          }

          .bill-price strong {
            font-size: 18px;
          }
        }

        @media (max-width: 760px) {
          .billing-page {
            padding: 8px;
          }

          .billing-page h1 {
            font-size: 25px;
          }

          .bill-heading-row {
            align-items: flex-start;
          }

          .bill-heading-row p {
            font-size: 12px;
            max-width: 35ch;
          }

          .bill-heading-row > .bill-button {
            padding: 8px 10px;
          }

          .bill-two-columns,
          .bill-plan-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .bill-plan-card > p {
            min-height: auto;
          }

          .bill-benefit-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 22px 15px;
          }

          .bill-section-intro {
            align-items: flex-start;
            flex-direction: column;
          }

          .bill-plan-summary {
            gap: 12px;
          }

          .bill-plan-summary h2 {
            font-size: 20px;
          }

          .bill-entitlement-row {
            flex-wrap: wrap;
          }

          .bill-tabs button {
            padding-left: 16px;
            padding-right: 16px;
            min-height: 40px;
          }

          .bill-message.warning {
            flex-wrap: wrap;
          }

          .bill-message.warning > .bill-button {
            margin-left: 30px;
          }

          .bill-table {
            min-width: 590px;
          }

          .bill-button {
            min-height: 40px;
          }

          .bill-invoice-paper {
            padding: 18px;
          }
        }

        @media (max-width: 480px) {
          .bill-overview-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .bill-heading-row {
            flex-direction: column;
          }

          .bill-header {
            padding-left: 12px;
            padding-right: 12px;
          }

          .bill-panel {
            padding: 13px;
          }

          .bill-plan-summary .bill-icon.large {
            width: 52px;
            height: 52px;
          }

          .bill-feature-strip {
            grid-template-columns: minmax(0, 1fr);
            gap: 10px;
          }

          .bill-feature-strip span {
            display: flex;
            justify-content: space-between;
          }

          .bill-date-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .bill-date-grid > div {
            display: flex;
            justify-content: space-between;
            gap: 12px;
          }

          .bill-invoice-toolbar {
            flex-direction: column;
          }

          .bill-card-row {
            flex-wrap: wrap;
          }

          .bill-invoice-parties {
            grid-template-columns: minmax(0, 1fr);
          }

          .bill-invoice-paper > .bill-between {
            flex-direction: column;
          }

          .bill-invoice-paper > .bill-between > .bill-right {
            text-align: left;
          }

          .bill-dialog-actions {
            flex-wrap: wrap;
          }

          .bill-benefit-grid {
            grid-template-columns: minmax(0, 1fr);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .bill-spin {
            animation: none;
          }

          .bill-button {
            transition: none;
          }
        }
      `}</style>
    </main>
  );
}
