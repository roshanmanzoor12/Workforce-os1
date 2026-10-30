-- V13: execute ONLY against an explicitly verified WorkforceOS tenant PostgreSQL database.
-- This migration must not run against the control-plane database.
BEGIN;
CREATE TABLE IF NOT EXISTS live_screen_login_lifecycle (
    login_id UUID NOT NULL,
    desktop_device_id UUID NOT NULL,
    employee_id UUID NOT NULL,
    owner_user_id UUID NOT NULL,
    live_session_id UUID NOT NULL,
    state VARCHAR(20) NOT NULL CHECK (state IN ('requested','ended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    PRIMARY KEY (login_id, desktop_device_id),
    CONSTRAINT ck_live_screen_login_lifecycle_end CHECK (
        (state='requested' AND ended_at IS NULL) OR
        (state='ended' AND ended_at IS NOT NULL)
    )
);
CREATE INDEX IF NOT EXISTS ix_live_screen_login_lifecycle_employee
    ON live_screen_login_lifecycle(employee_id, login_id);
CREATE INDEX IF NOT EXISTS ix_live_screen_login_lifecycle_session
    ON live_screen_login_lifecycle(live_session_id);
COMMIT;
