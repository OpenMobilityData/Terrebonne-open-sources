-- Everything that states, supports, undercuts or bears on one assertion (assertion= its id, e.g. x_done_deal, x_decided, x_reopen).
SELECT e.relation, n.type, n.date, n.time, n.id, n.short, e.note, COALESCE(NULLIF(e.url, ''), n.url) AS url
FROM edges e JOIN nodes n ON n.id = e."from"
WHERE e."to" = :assertion AND e.relation IN ('states', 'supports', 'undercuts', 'bears_on')
ORDER BY CASE e.relation WHEN 'states' THEN 1 WHEN 'supports' THEN 2 WHEN 'undercuts' THEN 3 ELSE 4 END, n.date, n.time_s, n.id;
