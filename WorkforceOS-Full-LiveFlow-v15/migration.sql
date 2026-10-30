-- V15 tenant migration. Run AFTER verified V13 migration, ON A TENANT DATABASE ONLY.
-- Must be registered using your existing tenant Alembic chain for production.
BEGIN;
ALTER TABLE live_screen_login_lifecycle
  ADD COLUMN IF NOT EXISTS last_ping_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_live_screen_login_lifecycle_ping
  ON live_screen_login_lifecycle (state, last_ping_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_live_screen_login_lifecycle_session
  ON live_screen_login_lifecycle (live_session_id);
CREATE TABLE IF NOT EXISTS live_screen_saved_approvals (
  user_id UUID NOT NULL,
  employee_id UUID NOT NULL,
  granted BOOLEAN NOT NULL DEFAULT FALSE,
  granted_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  PRIMARY KEY (user_id, employee_id),
  CONSTRAINT ck_screen_approval_revoked CHECK (
    (granted = TRUE AND revoked_at IS NULL) OR (granted = FALSE AND revoked_at IS NOT NULL)
  )
);
COMMIT;
