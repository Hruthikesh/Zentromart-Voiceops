# ZentroMart VoiceOps

A Python capstone project for a fictional store's customer support. It reads the supplied policies, looks up synthetic orders after verification, and uses Gnani to listen and speak.

**Repository:** https://github.com/Hruthikesh/Zentromart-Voiceops

**Status:** voice pipeline manually tested successfully by the user; 18 offline tests passed. Baseline and RAG evaluation completed. Conversation evaluation is incomplete due to daily quota. A real demo remains to be recorded. Final preparation made no paid API calls.

## Start here

Use Python 3.11. Open a terminal in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Download the [official dataset](https://drive.google.com/file/d/1jeGjWgZJ4vdfmbB71kghovcCUYNeSHOY/view) and extract it under `dataset/`. Set `DATASET_DIR` in `.env` to the folder containing `kb`, `data`, `practice` and `tools`. An absolute path works too. The dataset is deliberately excluded from this repository and submission ZIP.

```powershell
.\.venv\Scripts\python.exe dataset/Capstone_Project_Dataset_FTTT_2026/validate_dataset.py
```

Read [SETUP.md](SETUP.md) to configure the two private API keys. Then launch:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The first run downloads a multilingual embedding model. It requires internet access and may take a few minutes. Later runs reuse model files and the local vector index. The interface supports typed questions, microphone recording, spoken replies and source inspection.

## Required batch run

```powershell
.\.venv\Scripts\python.exe run.py --input audio_inputs --output runs/batch
```

Top-level audio files are independent questions. Put a conversation's turns in its own subfolder, named `01.wav`, `02.wav`, etc. Files are processed in filename order. Use `--conversation` only when all input files belong to one caller. Each output includes reply text, Gnani WAV speech, and JSON with retrieved chunks, cited IDs, tool results and status. A manifest lists failures; the process exits nonzero if any file fails. Do not put outputs inside the input directory.

Supported formats: WAV, MP3, FLAC, OGG, M4A and AAC. Use PCM WAV for longer recordings: the runner splits WAV files into 25-second clips. Keep compressed files below 30 seconds. Clip boundaries may reduce transcription accuracy. No alternative speech service is used.

## Four steps

1. **Prompt-only baseline:** same LLM, without documents or tools.
2. **RAG:** section chunks retain document IDs, versions and dates. Multilingual sentence embeddings are stored in a NumPy cosine index. A small keyword score helps IDs and exact terms. Retrieved older policies bring their current successor into context.
3. **Conversation:** recent turns and verified orders remain in the current session. The supplied tools perform lookups and write tickets. Python enforces the two-attempt verification limit. It strips delivery pincodes from successful lookup results.
4. **Voice:** Gnani STT feeds the same agent; Gnani TTS writes its answer as speech. Empty transcripts receive a repeat request.

The reference date is **20 October 2026**. Business-day calculations skip Sundays and dataset holidays. The model is instructed to use calendar days for return windows and apply document precedence. These prompt-level decisions still need end-to-end evaluation.

## Saved evaluation

| Mode | Total | Completed | Proxy passes | Decision correct | Errors |
|---|---:|---:|---:|---:|---:|
| Baseline | 52 | 52 | 4 | 7 | 0 |
| RAG | 52 | 52 | 13 | 24 | 0 |
| Conversations | 96 | 24 | 12 | 12 | 72 |

These are real saved diagnostics, not official accuracy. Conversation evaluation exhausted the 200,000-token daily quota. Originals remain under runs/full_questions locally; portable evidence is in sample_outputs. Results predate final fixes and must not be described as a rerun.

## Evaluation controls

Do not rerun the full evaluation just to check installation. These commands make API calls; use them only after quota is available.

Resume the incomplete legacy run into a NEW folder:

```powershell
.\.venv\Scripts\python.exe evaluate.py --mode conversations --seed runs/full_questions --output runs/conversations_resume
```

Resume that new run after a later interruption, keeping the same seed and options:

```powershell
.\.venv\Scripts\python.exe evaluate.py --mode conversations --seed runs/full_questions --output runs/conversations_resume --resume
```

For a small separate experiment use --mode rag --limit 3 --output runs/rag_small. Modes: baseline, rag, conversations, all. Use --asr for a separate ASR-text experiment. New runs reject non-empty output folders. Resumes append; the latest successful record per ID/turn counts once. Failures stop immediately. Configuration checks prevent changing model or practice inputs during resume.

Legacy successful turns restore history, verified orders and tool results without LLM calls or ticket creation. Legacy failed rows lack intermediate state and retry from the turn boundary. New runs save interrupted tool-loop state. Run only one evaluator per output folder. A partial JSONL line causes a safe refusal rather than silently discarding evidence.

Gold labels are used only after generation. Literal scoring needs manual review for multilingual equivalents. New checkpoints contain synthetic conversation state and stay under ignored runs/.

## Offline checks

```powershell
.\.venv\Scripts\python.exe -c "from src.config import load_env; import unittest; load_env(); r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests')); raise SystemExit(not r.wasSuccessful())"
.\.venv\Scripts\python.exe -m compileall -q src tests app.py run.py evaluate.py
.\.venv\Scripts\python.exe -m pip check
```

## Marking-scheme map

| Criterion | Marks | Implementation/evidence |
|---|---:|---|
| Grounded answers | 25 | `src/agent.py`, evidence restrictions and abstention |
| Retrieval | 15 | `src/retrieval.py`, section IDs and vector index |
| Conversation | 20 | session history, verification and supplied tools |
| Own evaluation | 10 | `evaluate.py`; saved baseline/RAG and partial conversation results |
| End-to-end voice | 10 | `src/voice.py`, `run.py`; user-reported manual success |
| Voice experience | 10 | recording UI, concise replies, repeat request; listen and assess |
| Report and demo | 10 | updated report and demo script; actual video required |

## Before submission

- Record the real maximum two-minute demo using DEMO.md and save it as demo.mp4.
- Add genuine reply-audio examples if available; none are fabricated here.
- Conversation evaluation can remain explicitly incomplete if quota prevents finishing. Never invent results.
- Run python package_submission.py to recreate ../team_name_voiceops.zip after adding the demo. Missing video is flagged.
- Submit the ZIP and repository URL through the organizer's submission channel. No portal submission has been performed.

Never use real customer data. Verification is only an educational simulation. The model can still make mistakes or follow malicious input; this is not a production support service. Do not claim a refund or cancellation has been executed: the only actions available are lookup and ticket creation.

## Credits and assistance

Dataset and mock tools: VoiceOps 2026 organizers, C&A / Gnani.ai. The dataset remains external. Code and documentation in this starter were prepared with AI assistance; review, understand and adapt them before submission, and follow your course's disclosure rules. No evaluation scores or demo outcomes are fabricated.

API references: [Gnani STT](https://docs.gnani.ai/python-sdk/speech-to-text), [Gnani TTS](https://docs.gnani.ai/python-sdk/text-to-speech), [Groq compatibility](https://console.groq.com/docs/openai).
