# WorkforceOS Live Screen — Milestone 2C: Direct video receiver

This package installs a reusable React `<video>` renderer that accepts a real `MediaStream` and cleans up element event handlers and bindings when switching streams. It is designed for the original `/monitoring/live-screen` page and replaces the Milestone 2B pending placeholder (the earlier nested iframe is removed by 2B).

## Prerequisites

Install Milestone 2B first; its exact marker is required by this fail-closed patch. Keep an original backup.

## Install

Run `INSTALL.ps1` from the extracted package. It backs up the existing page, adds `apps/web/components/monitoring/native-live-video.tsx`, and swaps the 2B placeholder for the component.

## Scope / non-goals

**This DOES NOT transmit desktop frames to the owner.** The original page deliberately passes `stream={null}` until a secure, authenticated native transport is built. It does not change permissions, the agent, or FastAPI. Do not mark remote viewing as implemented based on this step. It does not enable capture on login or bypass per-session employee authorization.

## Rollback

Run `ROLLBACK.ps1` to restore the most recent 2C page backup.
