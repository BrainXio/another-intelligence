"""QLoRA-compatible preference-pair dataset export from telemetry."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from another_intelligence.rpe.telemetry import TelemetryRecorder


class PreferencePairExporter:
    """Generate QLoRA-compatible preference-pair datasets from telemetry.

    Each record becomes a prompt/chosen/rejected triple with the RPE signal
    attached as metadata.  The output format matches the standard expected
    by HuggingFace TRL's DPOTrainer and similar QLoRA fine-tuning scripts.
    """

    def __init__(self, recorder: TelemetryRecorder) -> None:
        self._recorder = recorder

    def export(
        self,
        output_dir: str | Path = "memory/qlora-pairs",
        min_abs_rpe: float = 0.1,
        since: str | None = None,
        limit: int = 10_000,
    ) -> dict[str, Any]:
        """Export filtered preference pairs from telemetry.

        Args:
            output_dir: Directory to write the dataset files.
            min_abs_rpe: Minimum absolute RPE required to include a pair.
            since: Earliest date (``YYYY-MM-DD``) to include.
            limit: Maximum number of pairs to export.

        Returns:
            A summary dict with ``exported`` count, ``skipped`` count,
            ``output_dir``, and the list of written file paths.
        """
        days = self._recorder.list_days()
        if since is not None:
            days = [d for d in days if d >= since]

        records: list[Any] = []
        for day in days:
            records.extend(self._recorder.read_day(day))

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        exported = 0
        skipped = 0
        files: list[str] = []

        for record in records:
            if exported >= limit:
                break
            if abs(record.rpe) < min_abs_rpe:
                skipped += 1
                continue

            rejected = [opt for opt in record.options if opt != record.chosen_action]
            if not rejected:
                skipped += 1
                continue

            pair = {
                "prompt": record.query,
                "chosen": record.chosen_action,
                "rejected": rejected,
                "rpe": record.rpe,
                "decision_id": record.decision_id,
                "timestamp": record.timestamp.isoformat(),
            }

            ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{ts}_{record.decision_id[:8]}.json"
            path = out / filename
            path.write_text(json.dumps(pair, indent=2), encoding="utf-8")
            files.append(str(path))
            exported += 1

        # Write the full dataset as a JSONL file for batch loading
        if exported > 0:
            dataset_path = out / "dataset.jsonl"
            with dataset_path.open("w", encoding="utf-8") as f:
                for path_str in files:
                    f.write(json.dumps(json.loads(Path(path_str).read_text())) + "\n")

        return {
            "exported": exported,
            "skipped": skipped,
            "output_dir": str(out),
            "files": files,
        }
