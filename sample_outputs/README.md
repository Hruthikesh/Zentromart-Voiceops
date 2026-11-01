# Genuine saved outputs

evaluation_summary.json exactly copies the existing full_questions summary. Example JSONL files preserve selected API-response records, answers and metrics unedited. A successful API response can still fail the proxy; examples include such failures.

Baseline and RAG files contain their first three answer records. The conversation file contains completed records for the first conversation ID. Corresponding questions are in the official practice dataset.

original_results_sha256.json records hashes of the four originals, which remain unchanged locally. Raw provider errors and full dataset copies are not published. The model was openai/gpt-oss-120b according to the user's run configuration.

Conversation evaluation is incomplete: 24/96 completed, 72 errors after quota exhaustion. Proxy counts are not official accuracy. Final prompt/resume changes were not evaluated with paid APIs.

No reply WAV or demo video was saved in the available project. User-reported manual speech success is not a packaged audio artifact. Add genuine output from a later permitted run; do not fabricate evidence.

offline-tests.txt is the earlier ten-test log. final-validation.txt records final offline checks.
