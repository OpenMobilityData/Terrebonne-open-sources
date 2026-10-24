-- Statements made at one sitting, interview or meeting, in recording order (event= an event id, e.g. e_oct6, e_sept8, e_agglo_oct22, e_daybreak).
SELECT s.time, s.lang, a.short AS speaker, s.id, s.short, s.url
FROM edges m
JOIN nodes s ON s.id = m."from" AND s.type = 'statement'
LEFT JOIN edges at ON at."from" = s.id AND at.relation = 'attributed_to'
LEFT JOIN nodes a ON a.id = at."to"
WHERE m.relation = 'made_at' AND m."to" = :event
ORDER BY s.time_s IS NULL, s.time_s, s.id;
