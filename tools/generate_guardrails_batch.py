#!/usr/bin/env python3
"""
Safety Readiness Level for Children - LLM-based Evaluation
Translating Design Principles into Automated guardrails and replay alignement for child safety.
Author: Gregory Renard (with GenAI: Claude, Gemini, Codex)
Organization: Everyone.AI | Year: 2025
For the well-being and safety of our children
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def find_record_files(base_dir: Path, recursive: bool) -> List[Path]:
  pattern = "**/record_*.json" if recursive else "record_*.json"
  return sorted(base_dir.glob(pattern))


def compute_guardrail_path(record_path: Path) -> Path:
  guardrails_dir = record_path.parent / "guardrails"
  guardrail_name = record_path.name.replace("record_", "guardrails_", 1)
  return guardrails_dir / guardrail_name


def main() -> None:
  parser = argparse.ArgumentParser(description="Batch guardrail generation")
  parser.add_argument(
      "--records-dir",
      default="outputs",
      help="Directory containing record_*.json files (default: %(default)s)",
  )
  parser.add_argument(
      "--recursive",
      action="store_true",
      help="Search for records recursively within --records-dir",
  )
  parser.add_argument(
      "--force",
      action="store_true",
      help="Re-generate guardrails even if the guardrails file already exists",
  )
  parser.add_argument(
      "--dry-run",
      action="store_true",
      help="List the records that would be processed without running generation",
  )
  args, passthrough = parser.parse_known_args()

  base_dir = Path(args.records_dir).resolve()
  if not base_dir.exists():
    parser.error(f"records directory not found: {base_dir}")

  records = find_record_files(base_dir, args.recursive)
  if not records:
    print(f"[info] No record_*.json files found under {base_dir}")
    return

  generator_script = Path(__file__).resolve().with_name("generate_guardrails.py")
  if not generator_script.exists():
    parser.error(f"generate_guardrails.py not found next to this script: {generator_script}")

  processed = 0
  skipped = 0
  failed = 0

  for record in records:
    guardrail_path = compute_guardrail_path(record)
    if guardrail_path.exists() and not args.force:
      skipped += 1
      continue

    if args.dry_run:
      print(f"[dry-run] Would generate guardrails for {record}")
      processed += 1
      continue

    guardrail_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(generator_script), "--record", str(record), *passthrough]
    print(f"[info] Generating guardrails for {record}")
    try:
      subprocess.run(cmd, check=True)
      processed += 1
    except subprocess.CalledProcessError as exc:
      failed += 1
      print(f"[error] Generation failed for {record} (exit code {exc.returncode})", file=sys.stderr)

  print(
      f"[summary] processed={processed} skipped={skipped} failed={failed} "
      f"(directory: {base_dir})"
  )


if __name__ == "__main__":
  main()
