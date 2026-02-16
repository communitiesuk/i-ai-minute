
# ElevenLabs

## Native Multi-Speaker Support

Text can assigned to a wide variety of voices across different personas 

## Voice Variety

Over 3000+ community shared voices. Voices can also be created either by providing a prompt or an audio file for approximation (cloning) for plans outside the free tier. Within the constraint of the free tier, voices can be created on the platform and experimented with on the platform. Generated voices are given a unique id which may be used during api calls.

## Realism of Speaker Transitions

Multi-speaker transcripts must be processed in chunks as context isn't retained between requests. The resulting voices sound natural, but emotional continuity across chunks may vary. Transcripts would need to be formatted so that each segment is assigned an appropriate voice whether user‑generated, from elevenLabs' diary, or cloned. Upstream considerations such as the speaker’s gender, age, and nationality help maintain consistency in the final output. For simplicity, using generic premade voices (e.g. young male, young female) may be the most convenient starting point.

## Cost 
### ElevenLabs Pricing Plans (Monthly Overview)
[Total cost: $0.47 for 5mins 50secs of generated audio across sessions ≈ $4.84/hr]

| Plan       | Price        | Characters (TTS)               | Overages            | Voice Cloning      | Audio Quality | Seats | Concurrency |
|------------|--------------|--------------------------------|----------------------|---------------------|---------------|-------|-------------|
| Free       | $0           | 10k (Multilingual) / 20k (Flash) | N/A                  | ❌                  | 128 kbps      | 1     | 2           |
| Starter    | $5           | 30k / 60k                      | N/A                  | Instant Clone       | 128 kbps      | 1     | 3           |
| Creator    | $11 (50% off month 1) | 100k / 200k          | $0.30 / 1k chars     | 1 Pro Clone         | 192 kbps      | 1     | 5           |
| Pro        | $99          | 500k / 1M                      | $0.24 / 1k chars     | 1 Pro Clone         | 192 kbps      | 1     | 10          |
| Scale      | $330         | 2M / 4M                        | $0.18 / 1k chars     | 1 Pro Clone         | 192 kbps      | 3     | 15          |
| Business   | $1,320       | 11M / 22M                      | $0.12 / 1k chars     | 3 PVCs              | 192 kbps + SLAs | 15+  | 15          |
| Enterprise | Custom       | Custom                         | Negotiated           | Custom              | Custom        | Custom| Custom      |


## Data Handling

Data is stored in the US by default, enterprise subscribers have the option to nominate other jurisdictions (EU & India). A Zero Retention Mode is also offered. 
Private deployment is possible via AWS Marketplace & Amazon SageMaker allowing enterprise customers to run Text to Speech models within their own secure cloud infrastructure.

- GDPR Compliant 
- SOC2 Certified
- E2E Encryption
- Zero Retention Mode


## Limitations

Diarised transcripts can’t be directly processed by ElevenLabs in a way that automatically detects speaker gender, age, or accent and assigns voices without [prior formatting](#realism-of-speaker-transitions). In addition, the T2S service doesn’t handle translation; it generates speech in the same language as the input. Any transcribed text would therefore need to be translated into the desired language before being passed to the api.


## Audio Transformation

ElevenLabs offers a SoundEffects api that can be used to distort text derived audio. The text-to-sound-effects api generates sfx from a given prompt. This can't be done concurrently with the text-to-speech service so the workflow becomes a multistep process involving:

- using the text to speech service
- using the text to sound effect service
- layering both outputs with tools such as pydub or ffmpeg

It's a relatively simple process that enables the creation of diverse audio data for testing & evaluation. 
