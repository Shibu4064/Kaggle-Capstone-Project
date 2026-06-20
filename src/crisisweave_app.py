from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from tools import crisis_pipeline, pretty_json

def main():
    parser = argparse.ArgumentParser(description="Run CrisisWeave capstone workflow.")
    parser.add_argument("--scenario-file", default="data/sample_scenarios.json", help="JSON file with scenario list")
    parser.add_argument("--case-index", type=int, default=0, help="Scenario index to run")
    parser.add_argument("--output", default="outputs/demo_output.json", help="Output JSON path")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    scenario_path = root / args.scenario_file
    scenarios = json.loads(scenario_path.read_text(encoding="utf-8"))
    scenario = scenarios[args.case_index]
    result = crisis_pipeline(scenario)

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(pretty_json(result), encoding="utf-8")
    print(pretty_json(result))
    print(f"\nSaved output to {out_path}")

if __name__ == "__main__":
    main()
