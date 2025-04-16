SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname IN ('trustrent_core_db', 'trustrent_ops_db')
AND pid <> pg_backend_pid(); 