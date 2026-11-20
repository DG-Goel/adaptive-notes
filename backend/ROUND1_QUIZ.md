# Round 1 chunk quizzes

New frontend video workflows enable `compact_field_rows_quiz_v1`. Each successful
Round 1 response includes the existing note fields plus exactly four short-answer
questions. The questions include an answer, explanation, Bloom level and excerpt
references. No separate quiz API calls are made. The output reserve is 3000 tokens
instead of 2000 to accommodate the quiz; existing budget checks still apply.

Levels: Remember, Understand, Apply, Analyze, Evaluate, Create. Levels may repeat.
The model must stay within the supplied teaching material, and must not invent
content just to fill four questions. Invalid counts, duplicate questions, unknown
references and context-only questions fail validation. Exact evidence linkage is
checked; semantic correctness and Bloom-level correctness are not independently
verified. Quiz records explicitly retain `semantic_verified: false`.

Each successful work item saves an atomic JSON file under
`round1_combined/quizzes/<request-id>.json`. After workers finish, `quiz.json` and
`quiz.md` assemble questions in source order. Stable question IDs prevent retries
or resume from adding duplicates. Saved responses rebuild missing quiz exports
without another model call. Failed chunks produce an explicitly incomplete quiz.
Recovery children are separate chunks: each successful leaf contributes four;
failed attempts and retries do not count toward the total.

Original source provenance (including available timestamps) and exact evidence
quotes are stored in JSON. The AI Notes panel offers a quiz Markdown download;
JSON is available at `/api/video-notes/<job-id>/quiz-json`.
This does not replace or wire up the separate interactive Quiz Studio.

Restart the video-notes backend to load this change. Existing manifests and
completed runs are preserved and are not automatically upgraded or regenerated.
New workflows create quiz-enabled manifests; resuming an old manifest retains its
original format. Historical authorization and quota records are not rewritten.

Offline checks: `python -m pytest tests/test_round1_quiz.py
tests/test_authorized_runner.py` and frontend `tsc -b`.
