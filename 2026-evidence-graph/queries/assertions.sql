-- Every assertion with the number of nodes on each side, and the questions it belongs to.
SELECT x.id, x.short,
  SUM(e.relation = 'states') AS states, SUM(e.relation = 'supports') AS supports,
  SUM(e.relation = 'undercuts') AS undercuts, SUM(e.relation = 'bears_on') AS bears_on,
  (SELECT group_concat(q.question, ' ') FROM question_nodes q WHERE q.node = x.id) AS questions
FROM nodes x LEFT JOIN edges e ON e."to" = x.id AND e.relation IN ('states', 'supports', 'undercuts', 'bears_on')
WHERE x.type = 'assertion'
GROUP BY x.id ORDER BY x.id;
