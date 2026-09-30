import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def load_config():
    cfg = {}
    p = ROOT / "config.env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    cfg.update({k: v for k, v in os.environ.items() if k in cfg})
    return cfg
