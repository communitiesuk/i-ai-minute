# High-Level Design : Exploring Fast Forwarding

1. ## Purpose
    Testing the quality of transcribed audio when given sped up inputs

    Key Goals:
      - Identify and implement the best approach for speeding up files
      - Test approach against public audio data with known transcript
      - Review transcripts vs 1x output
      - Implement within working version of Minute based on APIM


2. ## Workflow

    1. Implement a variety of audio manipulation techniques
    2. Create a collection of audio files with them at different speeds (1.5x- 5x)
    3. Compare and contrast the transcriptions against their text contents
    4. Highlight discrepencies
    5. Implement as part of minute


3. ## Challenges
    1. Access to a working version of minute 
    2. Access to APIM
    3. Limitations on hardware (restricted to the medium models as is)
    4. Sourcing substantial public audio with known transcripts






