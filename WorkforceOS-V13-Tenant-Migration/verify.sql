-- Run only on the same explicitly identified tenant database.
SELECT current_database() AS current_database, current_schema() AS current_schema;
SELECT to_regclass('live_screen_login_lifecycle') AS lifecycle_table;
SELECT column_name, data_type, is_nullable FROM information_schema.columns
 WHERE table_schema=current_schema() AND table_name='live_screen_login_lifecycle' ORDER BY ordinal_position;
SELECT indexname FROM pg_indexes WHERE schemaname=current_schema()
 AND tablename='live_screen_login_lifecycle' ORDER BY indexname;
