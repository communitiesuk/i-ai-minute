'use client'

import { useState, useRef, useEffect } from 'react';
import { speedUpAudioToBlob } from './audioSpeedUp';

interface AudioSpeedUpPlayerProps {
  audioUrl: string;
  speedFactor: number;
  autoPlay?: boolean;
}

export function AudioSpeedUpPlayer({ 
  audioUrl, 
  speedFactor,
  autoPlay = false 
}: AudioSpeedUpPlayerProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);

  const cleanup = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setIsPlaying(false);
  };

  const processAndPlay = async () => {
    setIsProcessing(true);
    setError(null);
    cleanup();

    try {
      // Speed up audio
      const blob = await speedUpAudioToBlob(audioUrl, speedFactor);
      
      // Create playable URL
      const audioUrlBlob = URL.createObjectURL(blob);
      urlRef.current = audioUrlBlob;
      
      // Create and play audio
      const audio = new Audio(audioUrlBlob);
      audioRef.current = audio;
      
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrlBlob);
      };
      
      audio.onerror = (err) => {
        console.error('Audio playback error:', err);
        setError('Failed to play audio');
        setIsPlaying(false);
      };
      
      await audio.play();
      setIsPlaying(true);
    } catch (err) {
      console.error('Error processing audio:', err);
      setError('Failed to process audio');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStop = () => {
    cleanup();
  };

  // Auto-play on mount if enabled
  useEffect(() => {
    if (autoPlay) {
      processAndPlay();
    }
    
    // Cleanup on unmount
    return () => {
      cleanup();
    };
  }, [audioUrl, speedFactor]); // Re-process if URL or speed changes

  return (
    <div style={{color:'black', width:'200px', height:'200px'}}>
      <h3>Audio Player ({speedFactor}x speed)</h3>
      
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      {!isPlaying ? (
        <button
          onClick={processAndPlay}
          disabled={isProcessing}
          style={{color:'black', width:'50px', height:'50px', borderRadius:'10px'}}
        >
          {isProcessing ? 'Processing...' : `Play at ${speedFactor}x`}
        </button>
      ) : (
        <button onClick={handleStop} 
         style={{color:'black', width:'50px', height:'50px'}}
        >
          Stop
        </button>
      )}
      
      {isProcessing && <p>Processing audio...</p>}
      {isPlaying && <p>Now playing at {speedFactor}x speed</p>}
    </div>
  );
}