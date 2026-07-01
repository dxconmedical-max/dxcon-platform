import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_seed_module():
    path = ROOT / "scripts" / "seed_standards_demo.py"
    spec = importlib.util.spec_from_file_location("seed_standards_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_demo_data():
    return load_seed_module().seed_all()
