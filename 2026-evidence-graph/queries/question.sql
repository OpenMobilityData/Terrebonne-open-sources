-- The nodes of each question in questions.csv, in the order listed (question= one number, e.g. 3.2; empty = all).
SELECT q.question, q.title, n.type, n.date, n.id, n.short
FROM questions q JOIN question_nodes qn ON qn.question = q.question LEFT JOIN nodes n ON n.id = qn.node
WHERE (:question IS NULL OR q.question = :question)
ORDER BY CAST(substr(q.question, 1, instr(q.question, '.') - 1) AS INTEGER), CAST(substr(q.question, instr(q.question, '.') + 1) AS INTEGER), qn.pos;
