'use client';

import { useState, useEffect } from 'react';
import { submitJob, getJobStatus, getDownloadUrl, submitCharacterGen } from '@/lib/api';

export default function Home() {
    // Workflow State
    const [step, setStep] = useState<'character' | 'story'>('character');

    // Character Step State
    const [charPrompt, setCharPrompt] = useState('');
    const [charJobId, setCharJobId] = useState<string | null>(null);
    const [charStatus, setCharStatus] = useState<any>(null);
    const [charImage, setCharImage] = useState<string | null>(null);

    // Story Step State
    const [story, setStory] = useState('');
    const [jobId, setJobId] = useState<string | null>(null);
    const [status, setStatus] = useState<any>(null);

    // UI Loading States
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // --- STEP 1: Character Generation ---
    const handleCharSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setCharImage(null);
        try {
            const res = await submitCharacterGen(charPrompt);
            setCharJobId(res.job_id);
        } catch (err: any) {
            setError(err.message);
            setLoading(false);
        }
    };

    // Poll for Character Status
    useEffect(() => {
        if (!charJobId) return;

        const interval = setInterval(async () => {
            try {
                const res = await getJobStatus(charJobId);
                setCharStatus(res);

                // Check if image is ready in artifacts
                if (res.artifacts?.character_image) {
                    setCharImage(res.artifacts.character_image);
                    setLoading(false);
                    clearInterval(interval);
                } else if (res.status === 'failed') {
                    setError("Character generation failed. Please try again.");
                    setLoading(false);
                    clearInterval(interval);
                }
            } catch (err) {
                console.error(err);
            }
        }, 1500);

        return () => clearInterval(interval);
    }, [charJobId]);

    // --- STEP 2: Story Generation ---
    const handleStorySubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await submitJob(story, charJobId); // Pass linked character ID
            setJobId(res.job_id);
        } catch (err: any) {
            setError(err.message);
            setLoading(false);
        }
    };

    // Poll for Video Status
    useEffect(() => {
        if (!jobId) return;

        const interval = setInterval(async () => {
            try {
                const res = await getJobStatus(jobId);
                setStatus(res);
                if (["completed", "failed"].includes(res.status)) {
                    clearInterval(interval);
                    setLoading(false);
                }
            } catch (err) {
                console.error(err);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [jobId]);

    return (
        <main className="min-h-screen bg-neutral-900 text-white flex flex-col items-center justify-center p-8 font-sans">
            <div className="max-w-3xl w-full bg-neutral-800 p-8 rounded-2xl shadow-2xl border border-neutral-700">
                <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    {step === 'character' ? 'Step 1: Create Character' : 'Step 2: Create Story'}
                </h1>

                {/* Progress Indicators */}
                <div className="flex gap-2 mb-8">
                    <div className={`h-2 flex-1 rounded-full ${step === 'character' ? 'bg-blue-500' : 'bg-green-500'}`}></div>
                    <div className={`h-2 flex-1 rounded-full ${step === 'story' ? 'bg-blue-500' : 'bg-neutral-700'}`}></div>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-xl text-red-200">
                        {error}
                    </div>
                )}

                {/* --- VIEW 1: CHARACTER CREATION --- */}
                {step === 'character' && (
                    <div className="space-y-6">
                        {!charImage ? (
                            <form onSubmit={handleCharSubmit} className="space-y-4">
                                <label className="block text-neutral-300 text-sm uppercase font-bold tracking-wider">Describe your Character</label>
                                <textarea
                                    className="w-full h-32 bg-neutral-900 border border-neutral-700 rounded-xl p-4 text-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder-neutral-600"
                                    placeholder="e.g. A rusty robot with glowing blue eyes, wearing a tattered red scarf..."
                                    value={charPrompt}
                                    onChange={(e) => setCharPrompt(e.target.value)}
                                    required
                                    disabled={loading}
                                />
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-lg transition-all disabled:opacity-50"
                                >
                                    {loading ? 'Designing Character...' : 'Generate Character'}
                                </button>
                            </form>
                        ) : (
                            <div className="animate-in fade-in slide-in-from-bottom-4">
                                <div className="bg-black/20 p-4 rounded-xl border border-neutral-700 flex flex-col items-center">
                                    <img
                                        src={charImage}
                                        alt="Generated Character"
                                        className="max-h-80 rounded-lg shadow-2xl border border-neutral-600 mb-6"
                                    />
                                    <div className="flex gap-4 w-full">
                                        <button
                                            onClick={() => { setCharImage(null); setCharJobId(null); }}
                                            className="flex-1 py-3 bg-neutral-700 hover:bg-neutral-600 rounded-lg font-semibold transition-colors"
                                        >
                                            Try Again
                                        </button>
                                        <button
                                            onClick={() => setStep('story')}
                                            className="flex-1 py-3 bg-green-600 hover:bg-green-500 rounded-lg font-bold shadow-lg transition-colors"
                                        >
                                            Use This Character →
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* --- VIEW 2: STORY GENERATION --- */}
                {step === 'story' && !jobId && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-right-8">
                        <div className="flex items-center gap-4 bg-neutral-900/50 p-4 rounded-xl border border-neutral-700">
                            <img src={charImage!} className="w-16 h-16 rounded object-cover border border-neutral-600" />
                            <div>
                                <p className="text-sm text-neutral-400 uppercase font-bold">Locked Character</p>
                                <p className="text-neutral-200 text-sm line-clamp-1">{charPrompt}</p>
                            </div>
                            <button onClick={() => setStep('character')} className="ml-auto text-sm text-blue-400 hover:underline">Change</button>
                        </div>

                        <form onSubmit={handleStorySubmit} className="space-y-4">
                            <label className="block text-neutral-300 text-sm uppercase font-bold tracking-wider">Write your Story</label>
                            <textarea
                                className="w-full h-40 bg-neutral-900 border border-neutral-700 rounded-xl p-4 text-lg focus:ring-2 focus:ring-green-500 outline-none transition-all placeholder-neutral-600"
                                placeholder={`Write a story featuring your character...\nFor example: The robot walks down the street and finds a flower.`}
                                value={story}
                                onChange={(e) => setStory(e.target.value)}
                                required
                                disabled={loading}
                            />
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg transition-all disabled:opacity-50"
                            >
                                {loading ? 'Starting Production...' : 'Target Action! (Generate Video)'}
                            </button>
                        </form>
                    </div>
                )}

                {/* --- VIDEO PROGRESS VIEW (Optimized from original) --- */}
                {jobId && status && (
                    <div className="mt-8 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex justify-between items-center bg-neutral-900/50 p-4 rounded-xl border border-neutral-700">
                            <div>
                                <span className={`text-xl font-bold capitalize ${status.status === 'failed' ? 'text-red-400' : 'text-blue-400'}`}>
                                    {status.status}
                                </span>
                                <p className="text-sm text-neutral-500 font-mono mt-1">ID: {status.job_id.slice(0, 8)}</p>
                            </div>
                            <div className="text-right">
                                <span className="text-2xl font-bold text-white">{status.progress_current}%</span>
                            </div>
                        </div>

                        <div className="w-full bg-neutral-700 h-2 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all duration-500 ease-out ${status.status === 'failed' ? 'bg-red-500' : 'bg-gradient-to-r from-blue-500 to-purple-500'}`}
                                style={{ width: `${Math.max(5, status.progress_current)}%` }}
                            />
                        </div>

                        <p className="text-neutral-400 text-center text-sm font-mono bg-black/20 p-2 rounded">
                            "{status.message}"
                        </p>


                        {/* Agent Outputs - Restored for transparency */}
                        {status.artifacts && (
                            <div className="space-y-4">
                                {status.artifacts.script && (
                                    <div className="bg-neutral-900/50 rounded-xl p-4 border border-neutral-700">
                                        <h3 className="text-sm font-bold text-neutral-400 uppercase mb-2">📜 Generated Script</h3>
                                        <div className="max-h-40 overflow-y-auto text-xs font-mono text-neutral-300 whitespace-pre-wrap bg-black/20 p-2 rounded">
                                            {status.artifacts.script}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {status.status === 'completed' && (
                            <div className="mt-8 p-4 bg-green-900/30 border border-green-500/50 rounded-xl flex flex-col items-center animate-in zoom-in duration-300">
                                <p className="mb-4 text-green-300 font-bold">🎉 Your video is ready!</p>
                                <video
                                    controls
                                    className="w-full rounded-lg shadow-lg mb-4 border border-neutral-700"
                                    src={getDownloadUrl(jobId)}
                                />
                                <a
                                    href={getDownloadUrl(jobId)}
                                    download
                                    className="px-8 py-3 bg-green-600 hover:bg-green-500 rounded-lg font-bold shadow-lg transition-colors flex items-center gap-2"
                                >
                                    Download MP4
                                </a>
                            </div>
                        )}

                        <div className="text-center">
                            <button onClick={() => window.location.reload()} className="text-neutral-500 hover:text-white transition-colors text-sm">Create New Video</button>
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
