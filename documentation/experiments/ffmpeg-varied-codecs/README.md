## Usage

- Copy `.env.example` to `.env`, fill in required variables.
- `poetry install`.
- Manually move audio files with associated transcripts into `/data/raw`.
  - You can optionally run `config.py` to initialise the `/data` directory.
  - AMI data can be downloaded using the `evals/transcription` code of Minute.
- Run the `codec_exploration.ipynb` notebook.

## Notes

- Transcription time grows massively with the number of codecs added. Therefore, use a few, short samples when testing transcription quality. You can manually swap this out when testing non-transcription metrics.
