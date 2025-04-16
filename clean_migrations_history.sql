-- First, delete all migration records for our apps
DELETE FROM django_migrations WHERE app IN ('core', 'ops');

-- Then delete the problematic merge migration record
DELETE FROM django_migrations WHERE name = '0005_merge_20250416_1225'; 