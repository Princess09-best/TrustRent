-- First, let's identify any duplicates
WITH duplicates AS (
    SELECT title, location, COUNT(*) as count
    FROM core_property
    GROUP BY title, location
    HAVING COUNT(*) > 1
)
SELECT cp.* 
FROM core_property cp
JOIN duplicates d ON cp.title = d.title AND cp.location = d.location
ORDER BY cp.title, cp.location, cp.created_at;

-- For each duplicate, append a unique identifier to the title
UPDATE core_property cp1
SET title = cp1.title || ' #' || ROW_NUMBER() OVER (PARTITION BY cp1.title, cp1.location ORDER BY cp1.created_at)
WHERE EXISTS (
    SELECT 1
    FROM (
        SELECT title, location
        FROM core_property
        GROUP BY title, location
        HAVING COUNT(*) > 1
    ) dups
    WHERE cp1.title = dups.title AND cp1.location = dups.location
);

-- Now add the unique constraint
ALTER TABLE core_property
ADD CONSTRAINT unique_property_title_location UNIQUE (title, location); 