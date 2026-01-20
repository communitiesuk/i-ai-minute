
'use client'
import { AudioSpeedUpPlayer } from "./components/audio-player";
import { speedUpAndDownload } from "./components/audioSpeedUp";

export default function Home() {

const handleDownload = async () => {
    await speedUpAndDownload("/audio/brandon.mp3", 1.5);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <div style={{ color: 'black', fontSize: '20px' }}>Sped up Transcriptions</div>
        
        <button 
          onClick={handleDownload}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          Download 1.5x Speed Audio
        </button>

        <AudioSpeedUpPlayer audioUrl="/audio/brandon.mp3" speedFactor={2} />
      </main>
    </div>
  );
}
