-- Every differs_from pair with its note (relation= another difference relation instead: unsupported_by, does_not_include, same_data_other_denominator).
SELECT a.date AS from_date, a.id AS from_id, a.short AS from_short, b.date AS to_date, b.id AS to_id, b.short AS to_short, e.note
FROM edges e JOIN nodes a ON a.id = e."from" JOIN nodes b ON b.id = e."to"
WHERE e.relation = COALESCE(:relation, 'differs_from')
ORDER BY a.date, a.time_s, e.row;
