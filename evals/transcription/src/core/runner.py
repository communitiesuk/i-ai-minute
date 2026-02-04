import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import numpy as np
from tqdm import tqdm

from .metrics import (
    TimingAccumulator,
    compute_all_diarization_metrics,
    compute_wer_metrics,
    compute_wer_pct,
    normalise_text,
)

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

        ref_n = normalise_text(ref_raw)
        hyp_n = normalise_text(hyp_raw)
        per_wer, ops = compute_wer_pct([ref_n], [hyp_n], return_ops=True)

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
            "ref_norm": ref_n,
            "hyp_norm": hyp_n,
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
        ref_n = normalise_text(ref_raw)
        hyp_n = normalise_text(hyp_raw)
        per_wer, ops = compute_wer_pct([ref_n], [hyp_n], return_ops=True)

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
            "ref_norm": ref_n,
            "hyp_norm": hyp_n,
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


def compute_diarization_comparison(results: list) -> dict:
    """
    Compute comprehensive diarization metrics comparing engines.
    Uses the first engine as reference and compares others against it.
    """
    if len(results) < 2:
        return {}

    ref_engine = results[0]["summary"]["engine"]
    ref_samples = results[0]["samples"]

    comparisons = {}

    for i in range(1, len(results)):
        hyp_engine = results[i]["summary"]["engine"]
        hyp_samples = results[i]["samples"]

        per_sample_metrics = []
        aggregated_metrics = {
            "der": [],
            "jer": [],
            "miss": [],
            "false_alarm": [],
            "confusion": [],
            "speaker_count_error": [],
        }

        for ref_sample, hyp_sample in zip(ref_samples, hyp_samples):
            ref_diar = ref_sample.get("diarization", [])
            hyp_diar = hyp_sample.get("diarization", [])

            if not ref_diar or not hyp_diar:
                continue

            metrics = compute_all_diarization_metrics(ref_diar, hyp_diar)

            per_sample_metrics.append(
                {
                    "dataset_index": ref_sample["dataset_index"],
                    "metrics": metrics,
                }
            )

            aggregated_metrics["der"].append(metrics["der"]["der"])
            aggregated_metrics["jer"].append(metrics["jer"]["jer"])
            aggregated_metrics["miss"].append(metrics["component_breakdown"]["miss"])
            aggregated_metrics["false_alarm"].append(metrics["component_breakdown"]["false_alarm"])
            aggregated_metrics["confusion"].append(metrics["component_breakdown"]["confusion"])
            aggregated_metrics["speaker_count_error"].append(
                metrics["speaker_count"]["absolute_error"]
            )

        summary_metrics = {}
        for metric_name, values in aggregated_metrics.items():
            if values:
                summary_metrics[metric_name] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                }

        comparisons[f"{ref_engine}_vs_{hyp_engine}"] = {
            "reference_engine": ref_engine,
            "hypothesis_engine": hyp_engine,
            "num_samples_compared": len(per_sample_metrics),
            "summary_metrics": summary_metrics,
            "per_sample_metrics": per_sample_metrics,
        }

    return comparisons


def save_results(results: list, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    diarization_comparison = compute_diarization_comparison(results)

    # Compute per-adapter diarization metrics against ground truth reference
    adapter_diarization_metrics = {}
    for result in results:
        engine_name = result["summary"]["engine"]
        samples = result["samples"]

        # Compute metrics against ground truth reference
        per_sample_metrics = []
        for sample in samples:
            ref_diar = sample.get("reference_diarization", [])
            hyp_diar = sample.get("diarization", [])

            if ref_diar and hyp_diar:
                metrics = compute_all_diarization_metrics(ref_diar, hyp_diar)
                per_sample_metrics.append(
                    {
                        "der": metrics["der"]["der"],
                        "jer": metrics["jer"]["jer"],
                        "miss": metrics["component_breakdown"]["miss"],
                        "false_alarm": metrics["component_breakdown"]["false_alarm"],
                        "confusion": metrics["component_breakdown"]["confusion"],
                        "speaker_count_error": metrics["speaker_count"]["absolute_error"],
                    }
                )

        if per_sample_metrics:
            adapter_diarization_metrics[engine_name] = {
                "der": float(np.mean([m["der"] for m in per_sample_metrics])),
                "jer": float(np.mean([m["jer"] for m in per_sample_metrics])),
                "miss": float(np.mean([m["miss"] for m in per_sample_metrics])),
                "false_alarm": float(np.mean([m["false_alarm"] for m in per_sample_metrics])),
                "confusion": float(np.mean([m["confusion"] for m in per_sample_metrics])),
                "speaker_count_error": float(
                    np.mean([m["speaker_count_error"] for m in per_sample_metrics])
                ),
            }
        else:
            adapter_diarization_metrics[engine_name] = None

    adapters = []
    for r in results:
        summary = r["summary"]
        samples = r["samples"]

        entries = []
        for sample in samples:
            # Compute per-entry diarization metrics
            ref_diar = sample.get("reference_diarization", [])
            hyp_diar = sample.get("diarization", [])
            entry_diarization_metrics = None

            if ref_diar and hyp_diar:
                metrics = compute_all_diarization_metrics(ref_diar, hyp_diar)
                entry_diarization_metrics = {
                    "der": metrics["der"]["der"],
                    "jer": metrics["jer"]["jer"],
                    "miss": metrics["component_breakdown"]["miss"],
                    "false_alarm": metrics["component_breakdown"]["false_alarm"],
                    "confusion": metrics["component_breakdown"]["confusion"],
                    "speaker_count_error": metrics["speaker_count"]["absolute_error"],
                }

            results_section = {
                "wav_path": sample["wav_path"],
                "audio_sec": sample["audio_sec"],
                "process_sec": sample["process_sec"],
                "rtf": sample["rtf"],
                "wer_pct": sample["wer_pct"],
                "wer_metrics": sample.get("wer_metrics", {}),
                "diff_ops": sample["diff_ops"],
            }

            if entry_diarization_metrics:
                results_section["diarization"] = entry_diarization_metrics

            entry = {
                "dataset_index": sample["dataset_index"],
                "results": results_section,
                "debug": {
                    "ref_raw": sample["ref_raw"],
                    "hyp_raw": sample["hyp_raw"],
                    "ref_norm": sample["ref_norm"],
                    "hyp_norm": sample["hyp_norm"],
                    "diarization": sample.get("diarization", []),
                    "engine_debug": sample.get("engine_debug", {}),
                },
            }
            entries.append(entry)

        overall_results = {
            "num_samples": summary["num_samples"],
            "overall_wer_pct": summary["overall_wer_pct"],
            "overall_wer_metrics": summary.get("overall_wer_metrics", {}),
            "per_sample_wer_min": summary["per_sample_wer_min"],
            "per_sample_wer_max": summary["per_sample_wer_max"],
            "per_sample_wer_mean": summary["per_sample_wer_mean"],
            "per_sample_wer_std": summary.get("per_sample_wer_std"),
            "rtf": summary["rtf"],
            "process_sec": summary["process_sec"],
            "audio_sec": summary["audio_sec"],
        }

        # Add diarization metrics if available (only evaluation metrics, no statistics)
        engine_name = summary["engine"]
        if (
            engine_name in adapter_diarization_metrics
            and adapter_diarization_metrics[engine_name] is not None
        ):
            overall_results["diarization"] = adapter_diarization_metrics[engine_name]

        adapter_result = {
            "name": engine_name,
            "overall_results": overall_results,
            "entries": entries,
        }
        adapters.append(adapter_result)

    combined = {
        "adapters": adapters,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    logger.info("Results saved to %s", output_path)

    if diarization_comparison:
        logger.info("\n=== Diarization Comparison Metrics ===")
        for comparison_name, comparison_data in diarization_comparison.items():
            logger.info("\n%s:", comparison_name)
            summary = comparison_data["summary_metrics"]
            if "der" in summary:
                logger.info("  DER: %.2f%% (±%.2f)", summary["der"]["mean"], summary["der"]["std"])
                logger.info(
                    "    - Miss: %.2f%% (±%.2f)", summary["miss"]["mean"], summary["miss"]["std"]
                )
                logger.info(
                    "    - False Alarm: %.2f%% (±%.2f)",
                    summary["false_alarm"]["mean"],
                    summary["false_alarm"]["std"],
                )
                logger.info(
                    "    - Confusion: %.2f%% (±%.2f)",
                    summary["confusion"]["mean"],
                    summary["confusion"]["std"],
                )
            if "jer" in summary:
                logger.info("  JER: %.2f%% (±%.2f)", summary["jer"]["mean"], summary["jer"]["std"])
            if "speaker_count_error" in summary:
                logger.info(
                    "  Speaker Count Error: %.2f (±%.2f)",
                    summary["speaker_count_error"]["mean"],
                    summary["speaker_count_error"]["std"],
                )
