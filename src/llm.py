
"""A small, rate-limit-aware client for a configured chat-completions endpoint."""

import json
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests


class DailyQuotaExceeded(RuntimeError):
    """The evaluation must checkpoint and stop, not retry the next row."""


class LLM:
    def __init__(self):
        self.key = os.getenv('LLM_API_KEY')
        self.model = os.getenv(
            'LLM_MODEL',
            'openai/gpt-oss-120b'
        )
        self.url = (
            os.getenv(
                'LLM_BASE_URL',
                'https://api.groq.com/openai/v1'
            ).rstrip('/') + '/chat/completions'
        )

        if not self.key:
            raise ValueError(
                'Add LLM_API_KEY to your local .env file. Never commit it.'
            )

        self.max_attempts = 5
        self.min_request_interval = 2.1
        self.last_request_time = 0

    def _retry_delay(self, response, attempt):
        """Determine how long to wait before retrying."""

        retry_after = response.headers.get('Retry-After')

        if retry_after:
            try:
                return max(1, float(retry_after))
            except ValueError:
                try:
                    retry_date = parsedate_to_datetime(retry_after)
                    if retry_date.tzinfo is None:
                        retry_date = retry_date.replace(
                            tzinfo=timezone.utc
                        )
                    return max(
                        1,
                        (retry_date - datetime.now(timezone.utc)).total_seconds()
                    )
                except (TypeError, ValueError):
                    pass

        return min(60, 5 * (2 ** attempt))

    def complete(self, messages):
        for attempt in range(self.max_attempts):

            # Avoid sending requests too quickly.
            elapsed = time.monotonic() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)

            self.last_request_time = time.monotonic()

            try:
                response = requests.post(
                    self.url,
                    headers={
                        'Authorization': 'Bearer ' + self.key
                    },
                    json={
                        'model': self.model,
                        'messages': messages,
                        'temperature': 0.1,
                        'response_format': {
                            'type': 'json_object'
                        }
                    },
                    timeout=60
                )

            except requests.RequestException as exc:
                if attempt == self.max_attempts - 1:
                    raise RuntimeError(
                        'LLM connection failed. Check network access.'
                    ) from exc

                delay = min(60, 5 * (2 ** attempt))
                print(
                    f'LLM connection error. Retrying in {delay}s...',
                    flush=True
                )
                time.sleep(delay)
                continue

            if response.status_code == 429:
                try:
                    error_body = response.json()
                except ValueError:
                    error_body = response.text[:500]

                error_text = str(error_body).lower()

                # Daily quota exhaustion cannot be fixed by short retries.
                if any(term in error_text for term in (
                    'daily', 'per day', 'quota exceeded', 'tokens per day', 'tpd', 'rpd'
                )):
                    raise DailyQuotaExceeded(
                        'Daily API quota exhausted. Resume after quota resets.'
                    )

                if attempt == self.max_attempts - 1:
                    raise RuntimeError(
                        f'Groq rate limit persisted after '
                        f'{self.max_attempts} attempts.'
                    )

                delay = self._retry_delay(response, attempt)

                print(
                    f'Groq rate limit (429). '
                    f'Retrying in {delay:.1f} seconds '
                    f'({attempt + 1}/{self.max_attempts - 1})...',
                    flush=True
                )

                time.sleep(delay)
                continue

            if response.status_code in (500, 502, 503, 504):
                if attempt == self.max_attempts - 1:
                    raise RuntimeError(
                        f'Groq server error HTTP '
                        f'{response.status_code}.'
                    )

                delay = min(60, 5 * (2 ** attempt))
                time.sleep(delay)
                continue

            if not response.ok:
                raise RuntimeError(
                    f'LLM request failed (HTTP {response.status_code}). Check account and model settings.'
                )

            try:
                content = response.json()['choices'][0]['message']['content']
                return json.loads(content)
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise RuntimeError(
                    'Invalid JSON response from the LLM.'
                ) from exc

        raise RuntimeError('LLM request failed after all retry attempts.')
