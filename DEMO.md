# Two-minute demo recording script

Status: no demo.mp4 is present. The user reports successful manual voice testing, but no recording was available to package. This script is the fallback, not proof of a completed demo. No new paid API calls were made during preparation.

## Prepare
Use your own voice and synthetic data. Hide keys and account pages. Start with start_app.cmd. Wait for quota to reset if needed. Record the app window, microphone and computer playback. Verify that both voices are audible.

## Three customer questions
1. "What is ZentroMart's return policy for electronics?"
2. "Is that counted in calendar days or business days?"
3. "What will ZentroMart's return policy be in the year twenty thirty?"

Wait for each actual answer. Keep the same conversation for the follow-up. Question three should show uncertainty because the documents do not establish future policy. If the agent invents an answer, treat it as a failure and fix it before recording. A genuine successful handover can replace this uncertainty example.

## Five presentation steps
- 0:00-0:10: Say: "This is my ZentroMart VoiceOps project. It uses the supplied documents, Groq for responses and Gnani for listening and speaking."
- 0:10-0:45: Record question one, play its answer and briefly show Sources used.
- 0:45-1:15: Record question two and play the follow-up answer.
- 1:15-1:45: Record question three and play the actual uncertainty response.
- 1:45-2:00: Say: "RAG passed thirteen of fifty-two literal proxy checks, compared with four for baseline. Conversation evaluation is incomplete because the daily quota ran out."

Three questions and five presentation steps are suggested, not a fixed assignment requirement. Keep the whole video within two minutes. Do not edit answers to appear correct.

## Finish
Review duration and sound. Save the real recording here as demo.mp4. Run python package_submission.py to rebuild the ZIP, then add the video to Git and push. The packager flags missing video rather than creating a fake one.
