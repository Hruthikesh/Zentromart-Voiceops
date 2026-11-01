# ZentroMart VoiceOps
VoiceOps 2026 capstone | Thalla Hruthikesh 

## 1. What the project does
ZentroMart is the fictional store in the supplied dataset. This project answers policy questions, remembers follow-ups, checks synthetic orders after verification and creates support tickets. Customers type or record questions in Streamlit. Gnani transcribes recordings and speaks answers. The same agent accepts a folder of audio files.

## 2. Four implementation steps
**Step 1 - Prompted LLM.** The baseline uses Groq's openai/gpt-oss-120b with the assistant role and limits, without retrieval or business tools. It introduces itself as AI. This cautious baseline often asks for clarification instead of supplying unsupported policy details.

**Step 2 - Retrieval.** Markdown documents are split at section IDs. Chunks retain document type, status and effective date. Multilingual MiniLM embeddings, a NumPy cosine index and a small keyword score select evidence. Product rows are indexed too. Retrieving an older policy also includes its current successor. The prompt prioritizes current policy over guides, help, FAQs and marketing. Retrieved chunks and cited IDs are saved with answers.

**Step 3 - Conversation and tools.** Recent messages, the active order and verified order records stay in the conversation. Python enforces two verification attempts per order. The supplied lookup tool withholds order details until verification succeeds; the delivery pincode is removed before the result reaches the model. The supplied ticket tool writes an actual local synthetic ticket. The agent cannot issue refunds or cancel orders. Business-day calculations exclude Sundays and supplied holidays; the dataset reference date is 20 October 2026.

**Step 4 - Speech.** Only Gnani is used for STT and TTS. Defaults are English, Kaveri and timbre-v2.5. Long PCM WAV inputs are split into 25-second clips. The batch runner saves text, speech and JSON evidence, including per-file failures. The user reports successful manual testing of the complete voice pipeline. Final preparation did not repeat paid API calls or independently measure speech quality.

<!-- pagebreak -->

## 3. Actual evaluation results
Counts were verified against runs/full_questions/summary.json and its JSONL outputs. All original files remain unchanged. The saved run predates the final prompt and resume fixes; it is not a new measurement of the updated code.

| Mode | Total | Completed | Proxy passes | Decision correct | Errors |
|---|---:|---:|---:|---:|---:|
| Baseline | 52 | 52 | 4 | 7 | 0 |
| RAG | 52 | 52 | 13 | 24 | 0 |
| Conversations | 96 | 24 | 12 | 12 | 72 |

The proxy requires an acceptable decision, literal required facts and no literal forbidden phrase. It does not reliably recognize paraphrases, native-language equivalents or all unsafe claims. These are diagnostics, not official accuracy. RAG achieved nine more proxy passes on the same 52 questions: 4/52 versus 13/52, under the same scoring limitations.

Conversation evaluation is incomplete. The user identified the cause as Groq's 200,000-token daily limit. The old evaluator continued recording errors after exhaustion. Only 24 turns produced scored answers; the remaining 72 error rows must not be presented as assessed conversation quality.

Mean retrieved-evidence recall, calculated offline from saved per-question metrics, is 0.518 for RAG across questions with gold evidence. This measures coverage of gold section IDs, not whether the answer used them correctly. Baseline has no retrieval by design.

## 4. What the results showed
On PQ0002, RAG identified the Assured badge but asked for order verification instead of giving all required public warranty information. Baseline also requested an order ID. The assistant sometimes applies private-order verification requirements to general product questions.

Saved RAG decisions include 29 clarifications and 22 answers; baseline has 39 clarifications and two answers. Retrieval helped the proxy, but excessive clarification remains a weakness. An early conversation answer also asked again for a full order ID. The incomplete run does not establish reliable multi-turn performance.

These observations support targeted work on public-policy versus private-order requests, retrieval coverage and follow-up interpretation. They do not support a claim of high overall accuracy.

<!-- pagebreak -->

## 5. Final fixes and offline verification
Evaluation now supports individual modes, append-only results and checkpoint/resume. It stops on recognized daily quota exhaustion and other errors instead of skipping a failed conversation turn. Completed turns are restored without model calls. New checkpoints retain interrupted tool-loop state so retrying does not repeat a completed ticket. Legacy successful turns are reconstructed from messages and tool results; old failed rows cannot recover intermediate state that was never saved.

The prompt now distinguishes Plus refunds being initiated at pickup from being processed or settled at pickup. This change has not been evaluated against the paid API. Raw provider error bodies are no longer shown in the interface. Empty transcripts reach the existing repeat-request response.

Eighteen offline unit tests passed: the original ten plus eight resume/quota regression checks. They use scripted responses and mocked HTTP calls, not live model evaluation. Compilation, dependency checks, imports and official dataset validation are documented in the packaged validation log.

## 6. Limitations and submission status
Grounding and policy precedence still rely partly on prompting. Verification is an educational simulation, not production authentication. Literal scoring can reject valid multilingual answers and miss paraphrased errors. Audio splitting can cut words; broad accent and noise testing is unmeasured. No full evaluation or large audio batch was rerun during preparation.

A real two-minute demo recording remains required. DEMO.md provides the script. No video or speech evidence was fabricated. The package contains genuine saved text answers and evaluation evidence; recorded speech examples should come from an actual run. Resume conversation evaluation only when quota is available and report new results separately.

## 7. References and assistance
VoiceOps 2026 capstone brief and official synthetic ZentroMart dataset; Gnani Python STT/TTS documentation; Groq API documentation. Links and installation instructions are in README.md.

AI assistance was used for implementation, debugging and document preparation. The student should understand and review the code and follow course disclosure rules. Metrics come from saved agent outputs; test answers were not manually rewritten.
