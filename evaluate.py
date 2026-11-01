
"""Append-only evaluation with offline state restoration and quota-stop checkpoints."""

import argparse
import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from src.agent import Agent
from src.config import dataset_path, load_env
from src.factory import components
from src.llm import DailyQuotaExceeded
from src.tools import redact

MODES = ("baseline", "rag", "conversations")


def split(value):
    return [s.strip() for s in (value or "").split(";") if s.strip()]


def score(row, answer):
    reply = answer["reply"].casefold()

    facts_ok = all(
        any(a.strip().casefold() in reply for a in f.split(" / "))
        for f in split(row.get("must_include"))
    )

    forbidden = any(
        p.casefold() in reply
        for p in split(row.get("must_not_include"))
    )

    decision_ok = answer["decision"] in split(
        row.get("acceptable_decisions") or row.get("expected_decision")
    )

    gold = set(split(row.get("gold_evidence")))
    retrieved = {c["id"] for c in answer.get("retrieved_chunks", [])}

    return {
        "decision_ok": decision_ok,
        "literal_facts_ok": facts_ok,
        "forbidden_literal": forbidden,
        "proxy_pass": decision_ok and facts_ok and not forbidden,
        "retrieval_recall": (
            len(gold & retrieved) / len(gold) if gold else None
        ),
    }


def record_key(record):
    return str(record["id"]), str(record.get("turn") or "")


def read_records(path):
    if not path.exists():
        return []

    records = []

    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except ValueError as exc:
                    raise ValueError(
                        f"{path.name}, line {number}: incomplete JSON. "
                        "Preserve and repair before resuming."
                    ) from exc

    return records


def restore_legacy(agent, question, record):
    """Restore successful legacy turns without model calls or tool side effects."""

    if "state" in record:
        agent.restore(record["state"])
        return

    answer = record["answer"]

    agent.history.extend([
        {"role": "user", "content": redact(question)},
        {"role": "assistant", "content": answer["reply"]},
    ])

    agent.first = False

    for call in answer.get("tool_calls", []):
        result = call.get("result", {})

        if call.get("action") == "lookup_order":
            oid = result.get("order_id") or agent.orders.order_id

            if oid:
                agent.orders.order_id = str(oid)

                if result.get("verified"):
                    safe = dict(result)
                    safe.pop("delivery_pincode", None)
                    agent.orders.verified[str(oid)] = safe

                elif result.get("locked"):
                    agent.orders.attempts[str(oid)] = 2

                elif result.get("verified") is False:
                    agent.orders.attempts[str(oid)] = (
                        agent.orders.attempts.get(str(oid), 0) + 1
                    )

        elif (
            call.get("action") == "create_ticket"
            and result.get("created")
        ):
            agent.last_ticket = result


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")

    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())

    temp.replace(path)


def safe_error_message(exc):
    """Keep useful diagnostics without exposing credentials."""

    message = str(exc)

    # Remove common bearer-token and API-key patterns.
    message = re.sub(
        r"(?i)(bearer\s+)[A-Za-z0-9._\-]+",
        r"\1[REDACTED]",
        message,
    )

    message = re.sub(
        r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[A-Za-z0-9._\-]+",
        r"\1[REDACTED]",
        message,
    )

    message = redact(message)

    return str(message)[:1500]


def is_quota_error(exc):
    if isinstance(exc, DailyQuotaExceeded):
        return True

    message = str(exc).casefold()

    quota_markers = (
        "tokens per day",
        "token per day",
        "daily token",
        "daily quota",
        "quota exceeded",
        "tpd",
    )

    return any(marker in message for marker in quota_markers)


def evaluate_mode(
    mode,
    rows,
    parts,
    output,
    resume=False,
    seed=None,
    asr=False,
):
    output.mkdir(parents=True, exist_ok=True)

    path = output / f"{mode}.jsonl"

    if path.exists() and not resume:
        raise FileExistsError(
            f"{path} exists; use --resume or a new output folder."
        )

    records = read_records(seed / f"{mode}.jsonl") if seed else []
    records += read_records(path)

    successful = {
        record_key(r): r
        for r in records
        if "answer" in r and "metrics" in r
    }

    failures = {
        record_key(r): r
        for r in records
        if "error" in r
    }

    agents = {}
    completed = []
    stopped = None

    with path.open(
        "a" if resume else "x",
        encoding="utf-8",
    ) as out:

        for row in rows:

            identity = row.get(
                "conversation_id",
                row.get("id"),
            )

            key = (
                str(identity),
                str(row.get("turn") or ""),
            )

            question = (
                row["customer_message"]
                if mode == "conversations"
                else row["asr_text" if asr else "question"]
            )

            if identity not in agents:
                agents[identity] = Agent(
                    *parts,
                    baseline=(mode == "baseline"),
                )

            agent = agents[identity]

            # Reconstruct previously successful turns without API calls.
            if key in successful:
                restore_legacy(
                    agent,
                    question,
                    successful[key],
                )
                completed.append(successful[key])
                continue

            # Restore the last saved interrupted state.
            if key in failures and failures[key].get("state"):
                agent.restore(failures[key]["state"])

            try:
                answer = agent.respond(question)

                record = {
                    "id": identity,
                    "turn": row.get("turn"),
                    "answer": answer,
                    "metrics": score(row, answer),
                    "state": agent.snapshot(),
                }

                completed.append(record)

            except Exception as exc:

                stopped = (
                    "daily_quota"
                    if is_quota_error(exc)
                    else "error"
                )

                record = {
                    "id": identity,
                    "turn": row.get("turn"),
                    "error": type(exc).__name__,
                    "error_message": safe_error_message(exc),
                    "stop_reason": stopped,
                    "state": agent.snapshot(),
                }

            # Save each record immediately.
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())

            print(
                f"{mode}: {identity} "
                f"turn {row.get('turn', '-')} - "
                f"{'saved' if not stopped else stopped}",
                flush=True,
            )

            if stopped:
                break

    metrics = [r["metrics"] for r in completed]

    return {
        "total": len(rows),
        "completed": len(metrics),
        "proxy_pass_count": sum(m["proxy_pass"] for m in metrics),
        "decision_correct": sum(m["decision_ok"] for m in metrics),
        "pending": len(rows) - len(metrics),
        "stop_reason": stopped,
    }


def main():

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs") / datetime.now().strftime(
            "evaluation_%Y%m%d_%H%M%S"
        ),
    )

    parser.add_argument(
        "--mode",
        choices=(*MODES, "all"),
        default="all",
    )

    parser.add_argument("--resume", action="store_true")

    parser.add_argument(
        "--seed",
        type=Path,
        help="Read-only old results to resume into a NEW output folder.",
    )

    parser.add_argument("--asr", action="store_true")
    parser.add_argument("--limit", type=int)

    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    if args.seed and args.seed.resolve() == args.output.resolve():
        parser.error(
            "--seed must differ from --output; seed data is read-only."
        )

    if (
        args.output.exists()
        and any(args.output.iterdir())
        and not args.resume
    ):
        parser.error(
            "Output folder is not empty. Choose a new folder "
            "or use --resume."
        )

    load_env()

    root = dataset_path()

    config = {
        "asr": args.asr,
        "limit": args.limit,
        "model": os.getenv(
            "LLM_MODEL",
            "openai/gpt-oss-120b",
        ),
        "dataset": {
            name: hashlib.sha256(
                (root / "practice" / name).read_bytes()
            ).hexdigest()
            for name in (
                "questions.csv",
                "conversations.csv",
            )
        },
        "seed": (
            str(args.seed.resolve())
            if args.seed
            else None
        ),
    }

    args.output.mkdir(parents=True, exist_ok=True)

    config_path = args.output / "run_config.json"

    if args.resume:

        if not config_path.exists():
            parser.error(
                "Legacy folder has no checkpoint configuration. "
                "Use --seed OLD --output NEW instead."
            )

        if json.loads(config_path.read_text()) != config:
            parser.error(
                "Resume configuration changed. Use the same "
                "model, dataset, limit, asr and seed."
            )

    else:
        atomic_json(config_path, config)

    parts = components()

    modes = (
        MODES
        if args.mode == "all"
        else (args.mode,)
    )

    summary_path = args.output / "progress.json"

    summary = (
        json.loads(summary_path.read_text())
        if summary_path.exists()
        else {}
    )

    summary["note"] = (
        "Literal proxy diagnostics, not official accuracy. "
        "Original seed outputs remain unchanged."
    )

    for mode in modes:

        filename = (
            "conversations.csv"
            if mode == "conversations"
            else "questions.csv"
        )

        with (
            root / "practice" / filename
        ).open(encoding="utf-8", newline="") as stream:

            rows = list(csv.DictReader(stream))

        if mode == "conversations":
            rows.sort(
                key=lambda r: (
                    r["conversation_id"],
                    int(r["turn"]),
                )
            )

        if args.limit:
            rows = rows[:args.limit]

        summary[mode] = evaluate_mode(
            mode,
            rows,
            parts,
            args.output,
            args.resume,
            args.seed,
            args.asr,
        )

        summary["updated_utc"] = datetime.now(
            timezone.utc
        ).isoformat()

        atomic_json(summary_path, summary)

        if summary[mode]["stop_reason"]:
            print(
                "Stopped safely. Outputs and state saved. "
                "No further modes were called."
            )
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
