# Submission status

Source, setup instructions, report and genuine saved text evaluation samples are prepared. The original full_questions results were preserved. No paid API calls were made during final preparation.

## Required user action
- Record the actual maximum two-minute demo and save it here as demo.mp4. Follow DEMO.md. It is missing from this package; no fake video was made.
- Add genuine spoken reply samples if available. The project currently has saved text answers and retrieval evidence, but no saved reply WAV files.
- Run python package_submission.py after adding video/audio. Commit and push those artifacts.
- Review the report, retain the incomplete-conversation disclosure, and submit through the organizer's submission channel. No portal submission has been performed.

## Evaluation limitation
Baseline: 52/52 completed, 4 proxy passes, 7 correct decisions. RAG: 52/52 completed, 13 proxy passes, 24 correct decisions. Conversations: 24/96 completed, 12 proxy passes, 12 correct decisions, 72 quota-related errors. These are diagnostic counts, not official accuracy. The final code changes have not been re-evaluated with paid APIs.

Resuming after quota reset is optional if the deadline prevents it; do not describe the partial conversation run as complete. Legacy failed turns lack intermediate tool state. New snapshots support handled interruptions such as quota exhaustion; a hard process kill during a tool side effect is not a transactional guarantee.
