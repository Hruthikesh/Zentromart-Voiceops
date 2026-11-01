# Set up your two keys

An API key is a private access code. The app uses one service for speech and another for its text answers.

1. Open https://app.gnani.ai/voice and sign in or create your own account. Find the API-key section and generate a key. Account labels may change. Copy the key privately.
2. Open https://console.groq.com/keys and sign in. Create an API key for this project. Check available model access and any account limits. Groq is used for text only.
3. In the project folder, copy `.env.example` to `.env` only if it does not already exist. Keep existing keys intact. Open `.env` in Notepad or your editor. Paste the Gnani key after `GNANI_API_KEY=` and the Groq key after `LLM_API_KEY=`. Save the file. Do not add spaces around the key.
4. Keep the supplied Groq base URL and LLM_MODEL=openai/gpt-oss-120b, the model used in the saved run. The model setting is configurable; if the default model is unavailable in your account, select an available chat model supporting JSON-object responses and put its ID in `LLM_MODEL`.
5. Set `DATASET_DIR` to your extracted official dataset folder. Windows paths can use forward slashes, for example `C:/Projects/voiceops/dataset/Capstone_Project_Dataset_FTTT_2026`.
6. Run the commands in README. Ask a general policy question first. Then record the same question and listen to the reply.

Do not paste keys into chat, screenshots, README, GitHub or the report. `.env` is ignored by Git. Check quotas and charges in both accounts before running the full evaluation. You do not need to share your account password with the assistant.

## If something fails

- Missing key: check that the file is named exactly `.env`, not `.env.txt`, and run from the project folder.
- HTTP 401/403: confirm the key and account access privately.
- HTTP 429: check quota; wait before trying again.
- Model download failure: check internet access and available storage, then restart.
- Speech failure: verify your Gnani account, language and voice combination. Defaults use English and Kaveri. For Hindi, use `LANGUAGE=hi-IN` and `VOICE=Nalini`.
- No audio files: use supported extensions and keep the output folder outside the input folder.

## Repository and quota

Repository: https://github.com/Hruthikesh/Zentromart-Voiceops

Keep .env, .venv, dataset copies, model caches, raw recordings and private checkpoints out of Git. The saved conversation run exhausted the daily quota. Wait for your account reset before using README's --seed/--resume commands. Do not rerun the full evaluation. Quota exhaustion does not require replacing keys.
