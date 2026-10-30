import {
  api,
} from "@/lib/api/client";

import type {
  AccountEntitlementsPublic,
  BillingPlansResponse,
  CurrentSubscriptionPublic,
  WorkspaceCreationAccessResponse,
} from "@/types/billing";


async function getPlans():
  Promise<BillingPlansResponse> {
  return api.get<BillingPlansResponse>(
    "/billing/plans",
  );
}


async function getSubscription():
  Promise<CurrentSubscriptionPublic> {
  return api.get<CurrentSubscriptionPublic>(
    "/billing/subscription",
  );
}


async function getEntitlements():
  Promise<AccountEntitlementsPublic> {
  return api.get<AccountEntitlementsPublic>(
    "/billing/entitlements",
  );
}


async function getWorkspaceAccess():
  Promise<WorkspaceCreationAccessResponse> {
  return api.get<WorkspaceCreationAccessResponse>(
    "/billing/workspace-access",
  );
}


export const billingService = {
  getPlans,
  getSubscription,
  getEntitlements,
  getWorkspaceAccess,
};