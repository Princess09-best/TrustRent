DELETE FROM django_migrations 
WHERE id IN (
    SELECT id 
    FROM (
        SELECT id,
        ROW_NUMBER() OVER (
            PARTITION BY app, name 
            ORDER BY id
        ) as rnum
        FROM django_migrations
    ) t
    WHERE t.rnum > 1
); 