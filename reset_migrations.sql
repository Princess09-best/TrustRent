-- Drop and recreate django_migrations table
DROP TABLE IF EXISTS django_migrations;
CREATE TABLE django_migrations (
    id SERIAL PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
); 