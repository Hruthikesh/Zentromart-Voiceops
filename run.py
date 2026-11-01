"""Batch audio runner. Each subfolder is a separate conversation."""
import argparse
import json
from pathlib import Path
from src.agent import Agent
from src.factory import components
from src.tools import redact
from src.voice import Voice

EXTENSIONS = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac'}


def run_folder(input_dir, output_dir, parts, voice, shared=False):
    files = sorted(p for p in input_dir.rglob('*') if p.is_file() and p.suffix.lower() in EXTENSIONS)
    if not files:
        raise ValueError('No supported audio files found.')
    sessions, results = {}, []
    for path in files:
        relative = path.relative_to(input_dir)
        # Top-level files are independent by default. A subfolder groups ordered turns.
        key = 'shared' if shared else (str(relative.parent) if relative.parent != Path('.') else str(relative))
        if key not in sessions:
            sessions[key] = Agent(*parts)
        target = output_dir / relative.parent / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        record = {'input': str(relative), 'conversation': key, 'status': 'error'}
        try:
            transcript = voice.transcribe(path)
            answer = sessions[key].respond(transcript)
            record.update(answer)
            record['transcript'] = redact(transcript)
            target.with_suffix(target.suffix + '.txt').write_text(answer['reply'], encoding='utf-8')
            voice.speak(answer['reply'], target.with_suffix(target.suffix + '.reply.wav'))
            record['status'] = 'ok'
        except Exception as exc:
            # Exception text can contain credentials or private server responses; log only its type.
            record['error'] = type(exc).__name__
        target.with_suffix(target.suffix + '.json').write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding='utf-8')
        results.append({'input': str(relative), 'status': record['status']})
    (output_dir / 'manifest.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('runs/batch'))
    parser.add_argument('--conversation', action='store_true', help='Treat all files as turns in one conversation.')
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.input.resolve() in args.output.resolve().parents:
        parser.error('Output must be outside the input folder.')
    results = run_folder(args.input, args.output, components(), Voice(), args.conversation)
    failed = sum(r['status'] != 'ok' for r in results)
    print(f'Processed {len(results)} audio files; {failed} failed. See {args.output}/manifest.json')
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
