import json
from pathlib import Path

try:
    with open(Path(__file__).parent.parent / "tealish.json") as f:
        config = json.load(f)
        build_path: Path = Path(__file__).parent.parent / config["directories"]["build"]
except OSError:
    print("Could not find tealish.json config file.")