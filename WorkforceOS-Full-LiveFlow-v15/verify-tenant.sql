-- Run against the verified tenant DB only, using psql or your SQL tooling.
SELECT current_database() AS database_name,
       to_regclass('public.live_screen_login_lifecycle') AS lifecycle_table,
       to_regclass('public.live_screen_saved_approvals') AS saved_approval_table;
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='live_screen_login_lifecycle' AND column_name='last_ping_at';
