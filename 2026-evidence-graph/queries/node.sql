-- One node and all its relations, both directions (id= a node id).
SELECT CASE WHEN e."from" = :id THEN '→' ELSE '←' END AS dir, e.relation, o.type, o.id, o.short, e.note
FROM edges e JOIN nodes o ON o.id = CASE WHEN e."from" = :id THEN e."to" ELSE e."from" END
WHERE e."from" = :id OR e."to" = :id
ORDER BY dir DESC, e.relation, o.date, o.id;
