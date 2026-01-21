'use client';

import { useState, useEffect } from 'react';
import { submitJob, getJobStatus, getDownloadUrl } from '@/lib/api';

export default function Home() {
    const [story, setStory] = useState('');
    const [jobId, setJobId] = useState<string | null>(null);
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await submitJob(story);
            setJobId(res.job_id);
        } catch (err: any) {
            setError(err.message);
            setLoading(false);
        }
    };

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
                    Story-to-Cartoon
                </h1>
                <p className="text-neutral-400 mb-8">
                    Turn your stories into 5-minute animated videos instantly.
                </p>

                {!jobId && (
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <textarea
                            className="w-full h-40 bg-neutral-900 border border-neutral-700 rounded-xl p-4 text-lg focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all placeholder-neutral-600"
                            placeholder="Write your story here... A robot finds a flower..."
                            value={story}
                            onChange={(e) => setStory(e.target.value)}
                            required
                        />
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg transition-all transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Starting...' : 'Generate Cartoon'}
                        </button>
                    </form>
                )}

                {error && (
                    <div className="mt-4 p-4 bg-red-900/50 border border-red-500 rounded-xl text-red-200">
                        {error}
                    </div>
                )}

                {status && (
                    <div className="mt-8 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex justify-between items-center">
                            <span className="text-2xl font-bold capitalize text-neutral-200">{status.status}</span>
                            <span className="text-neutral-500 font-mono">{status.job_id.slice(0, 8)}</span>
                        </div>

                        <div className="w-full bg-neutral-700 h-4 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500 ease-out"
                                style={{ width: `${Math.max(5, status.progress_current)}%` }}
                            />
                        </div>

                        <p className="text-neutral-400 text-center animate-pulse">
                            {status.message}
                        </p>

                        {status.status === 'completed' && (
                            <div className="mt-8 p-4 bg-green-900/30 border border-green-500/50 rounded-xl flex flex-col items-center">
                                <p className="mb-4 text-green-300">Your video is ready!</p>
                                <video
                                    controls
                                    className="w-full rounded-lg shadow-lg mb-4 border border-neutral-700"
                                    src={getDownloadUrl(jobId!)}
                                />
                                <a
                                    href={getDownloadUrl(jobId!)}
                                    download
                                    className="px-8 py-3 bg-green-600 hover:bg-green-500 rounded-lg font-bold shadow-lg transition-colors"
                                >
                                    Download MP4
                                </a>
                            </div>
                        )}
                        {status.status === 'failed' && (
                            <div className="mt-8 p-4 bg-red-900/30 border border-red-500/50 rounded-xl">
                                <p className="text-red-300">Generation failed. Please try again.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </main>
    );
}
