import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import numpy as np
from tqdm import tqdm

from .metrics import TimingAccumulator, compute_wer_metrics, compute_wer_pct
from .result_formatter import save_results

logger = logging.getLogger(__name__)


def run_engine(adapter, indices, label, *, dataset, wav_write_fn, duration_fn):
    rows = []
    timing = TimingAccumulator()

    for idx in tqdm(indices, desc=f"{label}", unit="sample"):
        ex = dataset[int(idx)]
        wav_path = wav_write_fn(ex, int(idx))
        ref_raw = ex["text"]
        aud_sec = float(duration_fn(wav_path))

        hyp_raw, proc_sec, dbg = adapter.transcribe_with_debug(wav_path)

        proc_sec = float(proc_sec)
        timing.add(aud_sec, proc_sec)

        per_wer, ops = compute_wer_pct([ref_raw], [hyp_raw], return_ops=True)
        wer_metrics = compute_wer_metrics([ref_raw], [hyp_raw])

        diarization = dbg.get("diarization", []) if isinstance(dbg, dict) else []
        reference_diarization = ex.get("reference_diarization", [])

        row = {
            "engine": label,
            "dataset_index": int(idx),
            "wav_path": wav_path,
            "audio_sec": aud_sec,
            "process_sec": proc_sec,
            "rtf": (proc_sec / aud_sec) if aud_sec else None,
            "wer_pct": float(per_wer),
            "wer_metrics": wer_metrics,
            "diff_ops": ops,
            "ref_raw": ref_raw,
            "hyp_raw": hyp_raw,
            "engine_debug": dbg,
            "diarization": diarization,
            "reference_diarization": reference_diarization,
        }
        rows.append(row)

    overall_wer = compute_wer_pct([r["ref_raw"] for r in rows], [r["hyp_raw"] for r in rows])
    overall_metrics = compute_wer_metrics(
        [r["ref_raw"] for r in rows], [r["hyp_raw"] for r in rows]
    )
    per_wers = [r["wer_pct"] for r in rows]

    summary = {
        "engine": label,
        "num_samples": len(indices),
        "overall_wer_pct": float(overall_wer),
        "overall_wer_metrics": overall_metrics,
        "rtf": float(timing.rtf),
        "process_sec": float(timing.process_sec),
        "audio_sec": float(timing.audio_sec),
        "per_sample_wer_min": float(np.min(per_wers)) if per_wers else None,
        "per_sample_wer_max": float(np.max(per_wers)) if per_wers else None,
        "per_sample_wer_mean": float(np.mean(per_wers)) if per_wers else None,
        "per_sample_wer_std": float(np.std(per_wers)) if per_wers else None,
    }

    return {"summary": summary, "samples": rows}


def run_engines_parallel(adapters_config, indices, *, dataset, wav_write_fn, duration_fn):
    total_tasks = len(indices) * len(adapters_config)
    pbar = tqdm(total=total_tasks, desc="Processing all engines", unit="task")
    pbar_lock = Lock()

    results = {}

    def process_sample(adapter_cfg, idx):
        adapter = adapter_cfg["adapter"]
        label = adapter_cfg["label"]

        ex = dataset[int(idx)]
        wav_path = wav_write_fn(ex, int(idx))
        ref_raw = ex["text"]
        aud_sec = float(duration_fn(wav_path))

        hyp_raw, proc_sec, dbg = adapter.transcribe_with_debug(wav_path)

        proc_sec = float(proc_sec)
        per_wer, ops = compute_wer_pct([ref_raw], [hyp_raw], return_ops=True)
        wer_metrics = compute_wer_metrics([ref_raw], [hyp_raw])

        diarization = dbg.get("diarization", []) if isinstance(dbg, dict) else []
        reference_diarization = ex.get("reference_diarization", [])

        row = {
            "engine": label,
            "dataset_index": int(idx),
            "wav_path": wav_path,
            "audio_sec": aud_sec,
            "process_sec": proc_sec,
            "rtf": (proc_sec / aud_sec) if aud_sec else None,
            "wer_pct": float(per_wer),
            "wer_metrics": wer_metrics,
            "diff_ops": ops,
            "ref_raw": ref_raw,
            "hyp_raw": hyp_raw,
            "engine_debug": dbg,
            "diarization": diarization,
            "reference_diarization": reference_diarization,
        }

        with pbar_lock:
            pbar.update(1)
            pbar.set_postfix({"engine": label, "sample": idx})

        return label, idx, row, aud_sec, proc_sec

    for adapter_cfg in adapters_config:
        results[adapter_cfg["label"]] = {"rows": [], "timing": TimingAccumulator()}

    with ThreadPoolExecutor(max_workers=len(adapters_config)) as executor:
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

    output_results = []
    for adapter_cfg in adapters_config:
        label = adapter_cfg["label"]
        rows = sorted(results[label]["rows"], key=lambda x: x["dataset_index"])
        timing = results[label]["timing"]

        overall_wer = compute_wer_pct([r["ref_raw"] for r in rows], [r["hyp_raw"] for r in rows])
        overall_metrics = compute_wer_metrics(
            [r["ref_raw"] for r in rows], [r["hyp_raw"] for r in rows]
        )
        per_wers = [r["wer_pct"] for r in rows]

        summary = {
            "engine": label,
            "num_samples": len(indices),
            "overall_wer_pct": float(overall_wer),
            "overall_wer_metrics": overall_metrics,
            "rtf": float(timing.rtf),
            "process_sec": float(timing.process_sec),
            "audio_sec": float(timing.audio_sec),
            "per_sample_wer_min": float(np.min(per_wers)) if per_wers else None,
            "per_sample_wer_max": float(np.max(per_wers)) if per_wers else None,
            "per_sample_wer_mean": float(np.mean(per_wers)) if per_wers else None,
            "per_sample_wer_std": float(np.std(per_wers)) if per_wers else None,
        }

        output_results.append({"summary": summary, "samples": rows})

    return output_results


