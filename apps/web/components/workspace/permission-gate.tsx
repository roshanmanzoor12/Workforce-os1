"use client";

import type {
  ReactNode,
} from "react";

import {
  hasAllPermissions,
  hasAnyPermission,
} from "@/lib/workspace/access";

import {
  useWorkspace,
} from "@/contexts/workspace-context";


interface PermissionGateProps {
  children:
    ReactNode;

  permission?:
    string;

  anyPermissions?:
    readonly string[];

  allPermissions?:
    readonly string[];

  fallback?:
    ReactNode;

  showFallbackForOwnerPreview?:
    boolean;
}


export function PermissionGate({
  children,

  permission,

  anyPermissions = [],

  allPermissions = [],

  fallback = null,

  showFallbackForOwnerPreview = false,
}: PermissionGateProps) {
  const {
    effectivePermissions,

    effectiveNavigationView,

    previewNavigationView,

    navigationView,
  } =
    useWorkspace();


  const requiredAny =
    permission
      ? [
          permission,
          ...anyPermissions,
        ]
      : anyPermissions;


  /*
   * If no "any" permissions were supplied,
   * the any-permission requirement is automatically satisfied.
   *
   * This prevents an empty permission list from
   * accidentally denying access.
   */
  const anyAllowed =
    requiredAny.length === 0
      ? true
      : hasAnyPermission(
          effectivePermissions,
          requiredAny,
          effectiveNavigationView,
        );


  /*
   * If no "all" permissions were supplied,
   * the all-permission requirement is automatically satisfied.
   */
  const allAllowed =
    allPermissions.length === 0
      ? true
      : hasAllPermissions(
          effectivePermissions,
          allPermissions,
          effectiveNavigationView,
        );


  const allowed =
    anyAllowed &&
    allAllowed;


  /*
   * Owner preview:
   *
   * The owner can preview another navigation role.
   *
   * By default, permission failures during the preview
   * should behave like the previewed role and therefore
   * show the fallback.
   *
   * If explicitly requested, the caller can suppress
   * the fallback while the owner is previewing.
   */
  const isOwnerPreview =
    Boolean(
      previewNavigationView &&
      navigationView === "owner",
    );


  if (!allowed) {
    if (
      isOwnerPreview &&
      !showFallbackForOwnerPreview
    ) {
      return null;
    }

    return (
      <>
        {fallback}
      </>
    );
  }


  return (
    <>
      {children}
    </>
  );
}


export default PermissionGate;