import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import numpy as np
from tqdm import tqdm

from evals.transcription.src.core.metrics import (
    TimingAccumulator,
    compute_wer_metrics,
    normalise_text,
)
from evals.transcription.src.core.types import (
    AdapterConfig,
    DatasetProtocol,
    DiffOps,
    DurationFn,
    EngineOutput,
    EngineResults,
    SampleRow,
    Summary,
    WavWriteFn,
)

logger = logging.getLogger(__name__)


def run_engines_parallel(
    adapters_config: list[AdapterConfig],
    indices: list[int],
    *,
    dataset: DatasetProtocol,
    wav_write_fn: WavWriteFn,
    duration_fn: DurationFn,
    max_workers: int | None = None,
) -> list[EngineOutput]:
    """
    Run multiple transcription adapters in parallel on dataset samples and compute WER metrics.
    """
    total_tasks = len(indices) * len(adapters_config)
    pbar = tqdm(total=total_tasks, desc="Processing all engines", unit="task")
    pbar_lock = Lock()

    results: dict[str, EngineResults] = {}

    def process_sample(
        adapter_cfg: AdapterConfig,
        idx: int,
    ) -> tuple[str, int, SampleRow, float, float]:
        """
        Transcribe a single sample and compute WER metrics.
        """
        adapter = adapter_cfg["adapter"]
        label = adapter_cfg["label"]

        example = dataset[int(idx)]
        wav_path = wav_write_fn(example, int(idx))
        ref_raw = example["text"]
        aud_sec = float(duration_fn(wav_path))

        hyp_raw, proc_sec, dbg = adapter.transcribe(wav_path)

        proc_sec = float(proc_sec)
        ref_n = normalise_text(ref_raw)
        hyp_n = normalise_text(hyp_raw)
        per_metrics = compute_wer_metrics([ref_n], [hyp_n])
        per_wer = per_metrics["wer"] * 100.0
        ops: DiffOps = {
            "equal": per_metrics["hits"],
            "replace": per_metrics["substitutions"],
            "delete": per_metrics["deletions"],
            "insert": per_metrics["insertions"],
        }

        row: SampleRow = {
            "engine": label,
            "dataset_index": int(idx),
            "wav_path": wav_path,
            "audio_sec": aud_sec,
            "process_sec": proc_sec,
            "rtf": (proc_sec / aud_sec) if aud_sec else None,
            "wer_pct": float(per_wer),
            "diff_ops": ops,
            "ref_raw": ref_raw,
            "hyp_raw": hyp_raw,
            "ref_norm": ref_n,
            "hyp_norm": hyp_n,
            "engine_debug": dbg,
        }

        with pbar_lock:
            pbar.update(1)
            pbar.set_postfix({"engine": label, "sample": idx})

        return label, idx, row, aud_sec, proc_sec

    for adapter_cfg in adapters_config:
        results[adapter_cfg["label"]] = EngineResults({"rows": [], "timing": TimingAccumulator()})

    workers = max_workers if max_workers is not None else len(adapters_config)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for adapter_cfg in adapters_config:
            for idx in indices:
                future = executor.submit(process_sample, adapter_cfg, idx)
                futures.append(future)

        for future in as_completed(futures):
            label, idx, row, aud_sec, proc_sec = future.result()
            results[label]["rows"].append(row)
            results[label]["timing"].add(aud_sec, proc_sec)

    pbar.close()

    output_results: list[EngineOutput] = []
    for adapter_cfg in adapters_config:
        label = adapter_cfg["label"]
        rows = sorted(results[label]["rows"], key=lambda row: row["dataset_index"])
        timing = results[label]["timing"]

        overall_metrics = compute_wer_metrics(
            [row["ref_raw"] for row in rows],
            [row["hyp_raw"] for row in rows],
        )
        overall_wer = overall_metrics["wer"] * 100.0
        per_wers = [row["wer_pct"] for row in rows]

        summary: Summary = {
            "engine": label,
            "num_samples": len(indices),
            "overall_wer_pct": float(overall_wer),
            "rtf": float(timing.rtf),
            "process_sec": float(timing.process_sec),
            "audio_sec": float(timing.audio_sec),
            "per_sample_wer_min": float(np.min(per_wers)) if per_wers else None,
            "per_sample_wer_max": float(np.max(per_wers)) if per_wers else None,
            "per_sample_wer_mean": float(np.mean(per_wers)) if per_wers else None,
        }

        output_results.append({"summary": summary, "samples": rows})

    return output_results


def save_results(results: list[EngineOutput], output_path: Path) -> None:
    """
    Save evaluation results to JSON file with summaries and per-sample details.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    combined = {
        "summaries": [result["summary"] for result in results],
        "engines": {result["summary"]["engine"]: result["samples"] for result in results},
    }

    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(combined, file_handle, indent=2, ensure_ascii=False)

    logger.info("Results saved to %s", output_path)
