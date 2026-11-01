# ZentroMart VoiceOps
### An AI-Powered Voice Customer Support Assistant

**VoiceOps 2026 | Capstone Project**

**Developed by:** Thalla Hruthikesh  
**Source Code:** [GitHub Repository](https://github.com/Hruthikesh/Zentromart-Voiceops)

---

## Overview

Customer support is not always about answering a single question. Customers may want to understand return policies, check an order, ask about a refund, or follow up on an existing issue.

**ZentroMart VoiceOps** is an AI-powered customer support assistant developed for a fictional e-commerce store. It combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), conversation memory, Python-based tools and speech processing to handle customer interactions through both text and voice.

The objective was to build a system that does more than generate conversational responses. It should retrieve relevant information, maintain context, verify customers before accessing private order details, and perform supported support operations.

## Key Features

- **Knowledge-based responses:** Answers questions using the supplied store policies and product information.
- **Multilingual retrieval:** Uses multilingual sentence embeddings to find relevant information from the knowledge base.
- **Conversation memory:** Maintains context across multiple turns within a customer session.
- **Order verification:** Checks customer identity before accessing private order information, with a maximum of two verification attempts.
- **Order lookup:** Retrieves synthetic order details through the supplied tools after successful verification.
- **Support ticket creation:** Records issues that require further assistance.
- **Voice interaction:** Accepts spoken questions and generates spoken responses using Gnani STT and TTS.
- **Source inspection:** Provides visibility into retrieved information and supporting references.

## System Architecture

The project was developed in four stages.

### 1. LLM Baseline

The initial version uses Groq with the `openai/gpt-oss-120b` model.

It receives a customer question and generates a response using system instructions, without document retrieval or order-related tools.

This version serves as the baseline for evaluating the impact of retrieval.

### 2. Retrieval-Augmented Generation (RAG)

A retrieval pipeline was introduced to ground responses in the supplied store information.

The implementation includes:

- Section-based document chunking with document IDs and metadata.
- Multilingual embeddings using a MiniLM sentence-transformer model.
- NumPy-based cosine similarity for semantic retrieval.
- Keyword matching to improve retrieval of exact terms and product identifiers.
- Product information retrieval alongside policy documents.
- Policy version and date handling to give precedence to current documents.

Retrieved information is passed to the language model as context before generating the response.

### 3. Conversation Memory and Support Tools

The assistant was extended to handle multi-turn customer interactions.

It maintains recent conversation history and relevant order context within a session.

Python-controlled tools handle:
- Order lookup after successful identity verification.
- Verification attempt limits.
- Sensitive information handling, including removal of delivery pincodes before order details reach the language model.
- Support ticket creation for unresolved customer issues.

The assistant does not directly execute refunds or cancellations. Its available actions are limited to the supplied lookup and ticket tools.

### 4. Voice Integration

Gnani STT and TTS were integrated to support voice-based customer interactions.

The workflow is:

**Customer Speech → Speech-to-Text → AI Agent → Response Generation → Text-to-Speech → Spoken Reply**

The application supports microphone input and audio playback. A separate batch runner processes recorded audio files and stores generated responses and execution details.

Long PCM WAV recordings are divided into clips of up to 25 seconds before transcription.

The complete microphone-to-spoken-response workflow was manually tested.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| LLM | Groq – `openai/gpt-oss-120b` |
| Embeddings | Multilingual MiniLM |
| Retrieval | NumPy, Cosine Similarity, Keyword Matching |
| Speech-to-Text | Gnani STT |
| Text-to-Speech | Gnani TTS |
| Testing | Python unittest |

## Evaluation Results

The system was evaluated using the supplied practice questions and multi-turn conversation dataset.

| Evaluation Mode | Total | Completed | Proxy Passes | Decision Correct |
|---|---:|---:|---:|---:|
| LLM Baseline | 52 | 52 | 4 | 7 |
| RAG | 52 | 52 | 13 | 24 |
| Conversations | 96 | 96 | 47 | 50 |

### Observations

**Baseline vs RAG**

On the same 52-question evaluation set, RAG recorded 13 proxy passes compared with 4 for the baseline. This represents 9 additional proxy passes under the same scoring rules.

The result suggests that retrieving relevant store information improved performance on the supplied practice questions.

**Conversation Evaluation**

The final conversation evaluation completed all **96 out of 96 turns**, covering the supplied multi-turn conversation cases.

- Completed turns: 96
- Pending turns: 0
- Proxy passes: 47
- Decision-correct flags: 50

**Understanding the Metrics**

Proxy passes and decision-correct flags are diagnostic metrics generated by the evaluation script. They are not official accuracy scores. Literal matching can miss valid answers expressed differently, and passing a check does not guarantee that a response is completely correct.

The results should therefore be interpreted as evaluation signals rather than claims of production-level performance.

## Testing

The project includes automated offline tests for important application behaviours.

**18 offline tests passed**, covering:

- Customer verification and retry limits.
- Conversation session handling.
- Business-day calculations.
- Document metadata and retrieval behaviour.
- Sensitive information redaction.
- Support ticket creation.
- Citation filtering.
- Empty audio transcript handling.
- Evaluation checkpoint and resume behaviour.

The voice pipeline was also manually tested from microphone input through speech recognition, response generation and audio playback.

## Running the Project

### Requirements

- Python 3.11
- Internet connection for model downloads and API access.
- Groq API key.
- Gnani API credentials.
- Official VoiceOps 2026 dataset.

### 1. Clone the repository

```bash
git clone https://github.com/Hruthikesh/Zentromart-Voiceops.git
cd Zentromart-Voiceops
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Add the required API credentials and configure `DATASET_DIR` to point to the extracted official dataset directory.

Do not commit your `.env` file or API keys to GitHub.

### 5. Validate the dataset

After extracting the official dataset, run:

```powershell
.\.venv\Scripts\python.exe dataset/Capstone_Project_Dataset_FTTT_2026/validate_dataset.py
```

### 6. Launch the application

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The first launch downloads the multilingual embedding model. This may take a few minutes.

## Batch Audio Processing

The project also includes a batch runner for processing recorded customer conversations.

```powershell
.\.venv\Scripts\python.exe run.py --input audio_inputs --output runs/batch
```

For multi-turn conversations, place the audio files in a separate folder and name them in the order they should be processed.

The runner generates response text, speech audio and JSON execution details for each input.

Supported formats include WAV, MP3, FLAC, OGG, M4A and AAC.

Refer to `SETUP.md` and `DEMO.md` for additional instructions.

## Limitations and Future Scope

There are still areas where the system can be improved.

- Some responses ask for unnecessary clarification, particularly when a general product or policy question does not require order verification.
- Retrieving relevant information does not always guarantee that the language model interprets it correctly.
- The evaluation is based on a limited synthetic dataset and diagnostic scoring rules.
- Order verification is an educational simulation using synthetic records, not production-grade authentication.
- Speech recognition has not been formally evaluated across different accents and noisy environments.

Future improvements include better retrieval and response evaluation, more accurate intent routing, reduced unnecessary clarification, and broader voice testing.

## Project Resources

- **Source Code:** [ZentroMart VoiceOps – GitHub](https://github.com/Hruthikesh/Zentromart-Voiceops)
- **Project Report:** `report.pdf`
- **Setup Instructions:** `SETUP.md`
- **Demonstration Guide:** `DEMO.md`

## Acknowledgements

This project was developed as part of the VoiceOps 2026 Capstone using the dataset and mock tools provided by the organizers and C&A / Gnani.ai.

AI assistance was used during parts of development, debugging and documentation. The implementation and evaluation results presented here are based on the project code, saved outputs and tests.

---

**ZentroMart VoiceOps**  
*Making customer support more conversational, contextual and accessible through voice.*