import os
from pathlib import Path
HF_TOKEN = os.getenv("HF_TOKEN")

def dataset_path():
    path = Path(os.getenv('DATASET_DIR', 'dataset/Capstone_Project_Dataset_FTTT_2026'))
    if not (path / 'kb').is_dir() or not (path / 'tools/tools.py').is_file():
        raise ValueError('Set DATASET_DIR to the extracted official dataset folder containing kb, data and tools.')
    return path


def load_env():
    from dotenv import load_dotenv
    load_dotenv()
