from whisper_transcribe.transcriber import transcriber

from pathlib import Path
from typing import Dict, Any
from compare import compare_transcripts  

def test_whisper_transcribe():

    base = Path(__file__).parent.parent
    #audio_path = base / "audio" / "and_we_were.mp3"
    expected_path = base / "audio" / "audio_text_files" / "and_we_were.txt"


    expected = expected_path.read_text().replace("\n", " ").strip()
    predicted = transcriber("and_we_were.mp3") 

    result = compare_transcripts(expected, predicted) 

    print(f"Similarity: {result['similarity']}%")

    # Assert similarity above threshold
    assert result["similarity"] > 85


