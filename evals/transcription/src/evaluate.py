import argparse
import logging
from datetime import datetime

from adapters import AzureSTTAdapter
from core.config import (
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_REGION,
    WORKDIR,
)
from core.dataset import audio_duration_seconds, load_benchmark_dataset, to_wav_16k_mono
from core.result_formatter import save_results
from core.runner import run_engines_parallel

logger = logging.getLogger(__name__)


def run_evaluation(
    num_samples: int | None = None,
    sample_duration_fraction: float | None = None,
    prepare_only: bool = False,
):
    output_dir = WORKDIR / "results"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"evaluation_results_{timestamp}.json"

    logger.info("Loading dataset...")
    ds = load_benchmark_dataset(
        num_samples=num_samples,
        sample_duration_fraction=sample_duration_fraction,
    )

    indices = list(range(len(ds)))
    logger.info("Loaded %d samples from AMI dataset", len(indices))

    if prepare_only:
        logger.info("=== Dataset Preparation Complete ===")
        logger.info("Prepared %d meetings", len(indices))
        logger.info("Audio files cached in: %s", WORKDIR / "cache" / "processed")
        return

    azure_adapter = AzureSTTAdapter(
        speech_key=AZURE_SPEECH_KEY,
        speech_region=AZURE_SPEECH_REGION,
        language="en-GB",
    )

    adapters_config = [
        {"adapter": azure_adapter, "label": "Azure Speech-to-Text"},
    ]

    logger.info(
        "Running %d adapters in parallel on %d samples...",
        len(adapters_config),
        len(indices),
    )
    results = run_engines_parallel(
        adapters_config=adapters_config,
        indices=indices,
        dataset=ds,
        wav_write_fn=to_wav_16k_mono,
        duration_fn=audio_duration_seconds,
    )

    save_results(results, output_path)

    logger.info("=== Evaluation Complete ===")
    for result in results:
        engine = result["summary"]["engine"]
        m = result["summary"]["aggregated_metrics"]

        logger.info("%s:", engine)
        if "wer_wer" in m:
            logger.info("  WER:  %.4f", m["wer_wer"]["mean"])
        if "jaccard_wer_jaccard_wer" in m:
            logger.info("  Jaccard WER: %.4f", m["jaccard_wer_jaccard_wer"]["mean"])
        if "wder_wder" in m:
            logger.info("  WDER: %.4f", m["wder_wder"]["mean"])
        if "speaker_count_speaker_count_accuracy" in m:
            logger.info(
                "  Speaker Count Accuracy: %.4f",
                m["speaker_count_speaker_count_accuracy"]["mean"],
            )

    logger.info("Results saved to: %s", output_path)


def main():
    parser = argparse.ArgumentParser(description="Run transcription evaluation")
    parser.add_argument(
        "--num-samples",
        type=int,
        default=None,
        help="Number of meetings to evaluate from AMI dataset. "
        "If not specified, evaluates all available meetings.",
    )
    parser.add_argument(
        "--sample-duration-fraction",
        type=float,
        default=None,
        help="Fraction of each meeting to use (e.g., 0.1 = use first 10%% of each meeting). "
        "When set, --num-samples must be >= 1.0 and specifies the number of meetings.",
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Only prepare and cache the dataset without running transcription",
    )
    args = parser.parse_args()

    run_evaluation(
        num_samples=args.num_samples,
        sample_duration_fraction=args.sample_duration_fraction,
        prepare_only=args.prepare_only,
    )


if __name__ == "__main__":
    main()
