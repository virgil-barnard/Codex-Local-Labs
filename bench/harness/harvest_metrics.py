"""Utilities for harvesting benchmark run metrics into CSV dashboards."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, List

from .schemas import RunSummary
from .trace import merge_trace_metrics

RESULTS_ROOT = Path("results")
RUNS_DIR = RESULTS_ROOT / "runs"
OUTPUT_PATH = RESULTS_ROOT / "dashboards" / "metrics.csv"


def discover_runs(root: Path = RUNS_DIR) -> Iterable[Path]:
    """Return run directories under the configured results root."""
    if not root.exists():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir())


def load_summaries(run_dirs: Iterable[Path]) -> List[RunSummary]:
    """Load :class:`RunSummary` objects from run directories."""
    summaries: List[RunSummary] = []
    for run_dir in run_dirs:
        metrics_path = run_dir / "metrics.json"
        if not metrics_path.exists():
            continue
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
            events_path = run_dir / "trace" / "events.jsonl"
            if events_path.exists():
                payload = merge_trace_metrics(payload, events_path)
                metrics_path.write_text(
                    json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            summaries.append(RunSummary.from_json(payload, run_dir))
        except Exception as exc:  # pragma: no cover - defensive guard
            print(f"[harvest] Skipping {run_dir}: {exc}")
    summaries.sort(key=lambda item: item.timestamp)
    return summaries


def write_csv(summaries: List[RunSummary], output_path: Path = OUTPUT_PATH) -> None:
    """Write harvested summaries to the dashboard CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(RunSummary.CSV_FIELDS))
        writer.writeheader()
        for summary in summaries:
            writer.writerow(summary.to_csv_row())


def harvest(root: Path = RUNS_DIR, output_path: Path = OUTPUT_PATH) -> Path:
    """Harvest metrics from ``root`` and write them to ``output_path``."""
    summaries = load_summaries(discover_runs(root))
    write_csv(summaries, output_path)
    print(f"[harvest] Wrote {len(summaries)} rows to {output_path}")
    return output_path


def main() -> None:
    """CLI entrypoint for ``python -m bench.harness.harvest_metrics``."""
    harvest()


if __name__ == "__main__":
    main()
