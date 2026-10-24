-- Statements by agent and date (agent= an agent id or part of its short name; empty = every agent).
SELECT a.short AS agent, s.date, s.time, s.lang, s.id, s.short, s.url
FROM nodes s
JOIN edges e ON e."from" = s.id AND e.relation = 'attributed_to'
JOIN nodes a ON a.id = e."to"
WHERE s.type = 'statement'
  AND (:agent IS NULL OR a.id = :agent OR a.short LIKE '%' || :agent || '%')
ORDER BY a.short, s.date, s.time_s, s.id;
