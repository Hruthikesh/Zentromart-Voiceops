"""Create a source-only submission ZIP; never package local settings or datasets."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parent
TOP = {'README.md', 'REPORT.md', 'report.pdf', 'SETUP.md', 'DEMO.md', '.env.example', '.gitattributes',
       '.gitignore', 'requirements.txt', 'requirements-lock.txt', 'app.py', 'run.py',
       'evaluate.py', 'start_app.cmd', 'package_submission.py', 'demo.mp4', 'SUBMISSION_STATUS.md'}
DIRECTORIES = {'src', 'tests', '.github', 'sample_outputs'}


def files_to_package():
    candidates = [ROOT / name for name in TOP if (ROOT / name).is_file()]
    for folder in DIRECTORIES:
        if (ROOT / folder).is_dir():
            candidates.extend((ROOT / folder).rglob('*'))
    for file in sorted(candidates):
        rel = file.relative_to(ROOT)
        if any(p in {'.venv', '.git', '.cache', '__pycache__', 'runs', 'dataset'} for p in rel.parts):
            continue
        if file.is_file() and (str(rel) in TOP or rel.parts[0] in DIRECTORIES):
            if file.suffix not in {'.pyc', '.tmp', '.log'} and file.name != '.env':
                yield file


def check_secrets(files):
    # Compare actual locally configured keys without ever printing values.
    keys = []
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            name, sep, value = line.partition('=')
            if sep and ('KEY' in name.upper() or 'TOKEN' in name.upper()):
                value = value.strip().strip('"\'')
                if len(value) >= 12:
                    keys.append(value.encode())
    patterns = [rb'gsk_[A-Za-z0-9]{20,}', rb'gh[pousr]_[A-Za-z0-9]{25,}',
                rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    for file in files:
        data = file.read_bytes()
        if any(key in data for key in keys) or any(re.search(p, data) for p in patterns):
            raise ValueError('Possible secret in ' + file.relative_to(ROOT).as_posix())


def main():
    files = list(files_to_package())
    check_secrets(files)
    names = {p.relative_to(ROOT).as_posix() for p in files}
    required = {'README.md', '.env.example', 'requirements.txt', 'run.py', 'report.pdf',
                'src/agent.py', 'sample_outputs/evaluation_summary.json'}
    if required - names:
        raise ValueError('Missing required files: ' + ', '.join(sorted(required - names)))
    destination = ROOT.parent / 'team_name_voiceops.zip'
    temp = destination.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, file.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(temp) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
        assert set(archive.namelist()) == names
        assert not any(n == '.env' or n.startswith(('.venv/', 'dataset/', 'runs/', '.cache/')) for n in names)
    temp.replace(destination)
    print(f'ZIP integrity and secret checks passed: {len(files)} files')
    print(f'Archive: {destination}')
    print('SHA256: ' + hashlib.sha256(destination.read_bytes()).hexdigest())
    print('Demo: present' if 'demo.mp4' in names else 'Demo: MISSING - record using DEMO.md before final submission')


if __name__ == '__main__':
    main()
