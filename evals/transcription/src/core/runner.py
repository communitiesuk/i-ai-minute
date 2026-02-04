import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import numpy as np
from jiwer import wer
from tqdm import tqdm

from .metrics import (
    TimingAccumulator,
    compute_all_diarization_metrics,
    compute_wer_pct,
    normalise_text,
    token_ops,
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

        per_wer = 100.0 * wer([ref_n], [hyp_n])
        ops = token_ops(ref_n, hyp_n)

        diarization = dbg.get("diarization", []) if isinstance(dbg, dict) else []
        
        row = {
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
            "diarization": diarization,
        }
        rows.append(row)

    overall_wer = compute_wer_pct([r["ref_raw"] for r in rows], [r["hyp_raw"] for r in rows])
    per_wers = [r["wer_pct"] for r in rows]

    total_speakers = sum(len(set(seg["speaker"] for seg in r.get("diarization", []))) for r in rows if r.get("diarization"))
    total_segments = sum(len(r.get("diarization", [])) for r in rows)
    samples_with_diarization = sum(1 for r in rows if r.get("diarization"))

    diarization_summary = {
        "total_speakers": total_speakers,
        "total_segments": total_segments,
        "samples_with_diarization": samples_with_diarization,
        "avg_speakers_per_sample": total_speakers / samples_with_diarization if samples_with_diarization > 0 else 0,
        "avg_segments_per_sample": total_segments / samples_with_diarization if samples_with_diarization > 0 else 0,
    }
    
    if samples_with_diarization > 0:
        unique_speakers_per_sample = [
            len(set(seg["speaker"] for seg in r.get("diarization", []))) 
            for r in rows if r.get("diarization")
        ]
        segments_per_sample = [
            len(r.get("diarization", [])) 
            for r in rows if r.get("diarization")
        ]
        
        diarization_summary.update({
            "speakers_per_sample_min": int(np.min(unique_speakers_per_sample)),
            "speakers_per_sample_max": int(np.max(unique_speakers_per_sample)),
            "speakers_per_sample_mean": float(np.mean(unique_speakers_per_sample)),
            "speakers_per_sample_std": float(np.std(unique_speakers_per_sample)),
            "segments_per_sample_min": int(np.min(segments_per_sample)),
            "segments_per_sample_max": int(np.max(segments_per_sample)),
            "segments_per_sample_mean": float(np.mean(segments_per_sample)),
            "segments_per_sample_std": float(np.std(segments_per_sample)),
        })

    summary = {
        "engine": label,
        "num_samples": len(indices),
        "overall_wer_pct": float(overall_wer),
        "rtf": float(timing.rtf),
        "process_sec": float(timing.process_sec),
        "audio_sec": float(timing.audio_sec),
        "per_sample_wer_min": float(np.min(per_wers)) if per_wers else None,
        "per_sample_wer_max": float(np.max(per_wers)) if per_wers else None,
        "per_sample_wer_mean": float(np.mean(per_wers)) if per_wers else None,
        "per_sample_wer_std": float(np.std(per_wers)) if per_wers else None,
        "diarization": diarization_summary,
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
        per_wer = 100.0 * wer([ref_n], [hyp_n])
        ops = token_ops(ref_n, hyp_n)

        diarization = dbg.get("diarization", []) if isinstance(dbg, dict) else []
        
        row = {
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
            "diarization": diarization,
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
        per_wers = [r["wer_pct"] for r in rows]

        total_speakers = sum(len(set(seg["speaker"] for seg in r.get("diarization", []))) for r in rows if r.get("diarization"))
        total_segments = sum(len(r.get("diarization", [])) for r in rows)
        samples_with_diarization = sum(1 for r in rows if r.get("diarization"))

        summary = {
            "engine": label,
            "num_samples": len(indices),
            "overall_wer_pct": float(overall_wer),
            "rtf": float(timing.rtf),
            "process_sec": float(timing.process_sec),
            "audio_sec": float(timing.audio_sec),
            "per_sample_wer_min": float(np.min(per_wers)) if per_wers else None,
            "per_sample_wer_max": float(np.max(per_wers)) if per_wers else None,
            "per_sample_wer_mean": float(np.mean(per_wers)) if per_wers else None,
            "diarization_stats": {
                "total_speakers": total_speakers,
                "total_segments": total_segments,
                "samples_with_diarization": samples_with_diarization,
                "avg_speakers_per_sample": total_speakers / samples_with_diarization if samples_with_diarization > 0 else 0,
                "avg_segments_per_sample": total_segments / samples_with_diarization if samples_with_diarization > 0 else 0,
            },
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
            
            per_sample_metrics.append({
                "dataset_index": ref_sample["dataset_index"],
                "metrics": metrics,
            })
            
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

    adapters = []
    for r in results:
        summary = r["summary"]
        samples = r["samples"]
        
        entries = []
        for sample in samples:
            entry = {
                "dataset_index": sample["dataset_index"],
                "results": {
                    "wav_path": sample["wav_path"],
                    "audio_sec": sample["audio_sec"],
                    "process_sec": sample["process_sec"],
                    "rtf": sample["rtf"],
                    "wer_pct": sample["wer_pct"],
                    "diff_ops": sample["diff_ops"],
                },
                "debug": {
                    "ref_raw": sample["ref_raw"],
                    "hyp_raw": sample["hyp_raw"],
                    "ref_norm": sample["ref_norm"],
                    "hyp_norm": sample["hyp_norm"],
                    "diarization": sample.get("diarization", []),
                    "engine_debug": sample.get("engine_debug", {}),
                }
            }
            entries.append(entry)
        
        adapter_result = {
            "name": summary["engine"],
            "overall_results": {
                "num_samples": summary["num_samples"],
                "overall_wer_pct": summary["overall_wer_pct"],
                "per_sample_wer_min": summary["per_sample_wer_min"],
                "per_sample_wer_max": summary["per_sample_wer_max"],
                "per_sample_wer_mean": summary["per_sample_wer_mean"],
                "per_sample_wer_std": summary.get("per_sample_wer_std"),
                "rtf": summary["rtf"],
                "process_sec": summary["process_sec"],
                "audio_sec": summary["audio_sec"],
                "diarization": summary.get("diarization", {}),
            },
            "entries": entries,
        }
        adapters.append(adapter_result)

    combined = {
        "adapters": adapters,
        "diarization_comparison": diarization_comparison,
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
                logger.info("    - Miss: %.2f%% (±%.2f)", summary["miss"]["mean"], summary["miss"]["std"])
                logger.info("    - False Alarm: %.2f%% (±%.2f)", summary["false_alarm"]["mean"], summary["false_alarm"]["std"])
                logger.info("    - Confusion: %.2f%% (±%.2f)", summary["confusion"]["mean"], summary["confusion"]["std"])
            if "jer" in summary:
                logger.info("  JER: %.2f%% (±%.2f)", summary["jer"]["mean"], summary["jer"]["std"])
            if "speaker_count_error" in summary:
                logger.info("  Speaker Count Error: %.2f (±%.2f)", 
                          summary["speaker_count_error"]["mean"], 
                          summary["speaker_count_error"]["std"])
