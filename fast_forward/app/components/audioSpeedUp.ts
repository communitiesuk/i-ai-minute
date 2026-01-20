/**
 * Speeds up an audio file and returns the rendered buffer
 * @param audioUrl - URL or path to the audio file
 * @param speedFactor - Speed multiplier (e.g., 1.5 for 1.5x speed, 2.0 for 2x speed)
 * @returns Promise<AudioBuffer> - The rendered audio buffer at the new speed
 */
export async function speedUpAudio(
  audioUrl: string,
  speedFactor: number
): Promise<AudioBuffer> {
  // Fetch and decode the audio file
  const response = await fetch(audioUrl);
  const arrayBuffer = await response.arrayBuffer();
  
  const audioContext = new AudioContext();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

  // Calculate new duration
  const newDuration = audioBuffer.duration / speedFactor;

  // Create offline context with new duration
  const offlineContext = new OfflineAudioContext(
    audioBuffer.numberOfChannels,
    audioBuffer.sampleRate * newDuration,
    audioBuffer.sampleRate
  );

  // Create source in offline context
  const source = offlineContext.createBufferSource();
  source.buffer = audioBuffer;
  source.playbackRate.value = speedFactor;
  source.connect(offlineContext.destination);
  source.start();

  // Render to new buffer
  const renderedBuffer = await offlineContext.startRendering();
  
  // Clean up
  await audioContext.close();
  
  return renderedBuffer;
}

/**
 * Converts an AudioBuffer to a WAV Blob
 * @param buffer - The AudioBuffer to convert
 * @returns Blob - WAV file as a Blob
 */
export function audioBufferToWav(buffer: AudioBuffer): Blob {
  const numberOfChannels = buffer.numberOfChannels;
  const length = buffer.length * numberOfChannels * 2;
  const arrayBuffer = new ArrayBuffer(44 + length);
  const view = new DataView(arrayBuffer);

  // Helper to write strings to DataView
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  // WAV header
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + length, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, 1, true); // PCM format
  view.setUint16(22, numberOfChannels, true);
  view.setUint32(24, buffer.sampleRate, true);
  view.setUint32(28, buffer.sampleRate * numberOfChannels * 2, true);
  view.setUint16(32, numberOfChannels * 2, true);
  view.setUint16(34, 16, true); // bits per sample
  writeString(36, 'data');
  view.setUint32(40, length, true);

  // Audio data
  const channels = [];
  for (let i = 0; i < numberOfChannels; i++) {
    channels.push(buffer.getChannelData(i));
  }

  let offset = 44;
  for (let i = 0; i < buffer.length; i++) {
    for (let channel = 0; channel < numberOfChannels; channel++) {
      const sample = Math.max(-1, Math.min(1, channels[channel][i]));
      view.setInt16(
        offset,
        sample < 0 ? sample * 0x8000 : sample * 0x7fff,
        true
      );
      offset += 2;
    }
  }

  return new Blob([arrayBuffer], { type: 'audio/wav' });
}

/**
 * Speeds up an audio file and downloads it as a WAV file
 * @param audioUrl - URL or path to the audio file
 * @param speedFactor - Speed multiplier (e.g., 1.5 for 1.5x speed)
 * @param outputFilename - Optional filename for the download (defaults to 'audio-{speed}x.wav')
 */
export async function speedUpAndDownload(
  audioUrl: string,
  speedFactor: number,
  outputFilename?: string
): Promise<void> {
  // Render the sped-up audio
  const renderedBuffer = await speedUpAudio(audioUrl, speedFactor);

  // Convert to WAV
  const wavBlob = audioBufferToWav(renderedBuffer);
  const url = URL.createObjectURL(wavBlob);

  // Download
  const a = document.createElement('a');
  a.href = url;
  a.download = outputFilename || `audio-${speedFactor}x.wav`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Clean up
  URL.revokeObjectURL(url);
}

/**
 * Speeds up an audio file and returns it as a WAV Blob (for uploading or further processing)
 * @param audioUrl - URL or path to the audio file
 * @param speedFactor - Speed multiplier (e.g., 1.5 for 1.5x speed)
 * @returns Promise<Blob> - WAV file as a Blob
 */
export async function speedUpAudioToBlob(
  audioUrl: string,
  speedFactor: number
): Promise<Blob> {
  const renderedBuffer = await speedUpAudio(audioUrl, speedFactor);
  return audioBufferToWav(renderedBuffer);
}

export async function speedUpAndPlay(
  audioUrl: string,
  speedFactor: number
): Promise<HTMLAudioElement> {
  const blob = await speedUpAudioToBlob(audioUrl, speedFactor);
  const url = URL.createObjectURL(blob);
  
  const audio = new Audio(url);
  await audio.play();
  
  // Clean up when audio ends
  audio.onended = () => URL.revokeObjectURL(url);
  
  return audio; // Return for further control (pause, stop, etc.)
}