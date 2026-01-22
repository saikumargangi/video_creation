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

                        {/* Progress Bar */}
                        <div className="w-full bg-neutral-700 h-2 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all duration-500 ease-out ${status.status === 'failed' ? 'bg-red-500' : 'bg-gradient-to-r from-blue-500 to-purple-500'}`}
                                style={{ width: `${Math.max(5, status.progress_current)}%` }}
                            />
                        </div>

                        {/* Detailed Steps Verification List */}
                        <div className="bg-neutral-900/30 rounded-xl p-4 border border-neutral-700/50 space-y-3">
                            <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-4">Production Pipeline</h3>
                            {[
                                { label: "Story Analysis & Script", threshold: 10 },
                                { label: "World Building (Series Bible)", threshold: 20 },
                                { label: "Scene Planning & Layout", threshold: 30 },
                                { label: "Continuity Check", threshold: 50 },
                                { label: "Animation & Rendering", threshold: 60 }, // Inferred
                                { label: "Final Assembly", threshold: 90 },
                            ].map((step, idx) => {
                                // Logic: 
                                // Completed: progress >= next_step_threshold (or 100 if last)
                                // Active: progress >= step.threshold && progress < next_check
                                // Pending: progress < step.threshold

                                // Simplified for linear progression:
                                let state = 'pending';
                                if (status.status === 'failed' && status.progress_current >= step.threshold && status.progress_current < (step.threshold + 10)) {
                                    state = 'failed';
                                } else if (status.progress_current >= step.threshold) {
                                    // If we are significantly past this step, it's done. 
                                    // "Rendering" (60) is tricky because 50->90 jump.
                                    // If we are at 50, Planning(30) is done. 
                                    const isCurrentStep = status.progress_current >= step.threshold &&
                                        (idx === 5 ? status.progress_current < 100 : status.progress_current < [10, 20, 30, 50, 60, 90][idx + 1]!);

                                    // Hacky override for the 50->90 gap
                                    if (step.threshold === 50 && status.progress_current === 50) state = 'active'; // Continuity checking
                                    else if (step.threshold === 60 && status.progress_current === 50) state = 'pending'; // Rendering hasn't started implied
                                    // Wait, tasks.py updates to 50 THEN renders. So at 50, we are rendering.
                                    // So actually: 
                                    // State is 'completed' if progress > step.threshold
                                    // State is 'active' if progress == step.threshold

                                    if (status.progress_current > step.threshold) state = 'completed';
                                    else if (status.progress_current === step.threshold) state = 'active';

                                    // Fix for the 60 threshold which doesn't exist in backend
                                    if (step.threshold === 60 && status.progress_current === 50) state = 'active'; // Rendering
                                    if (step.threshold === 50 && status.progress_current === 50) state = 'completed'; // Continuity done instantly basically

                                    if (status.status === 'completed') state = 'completed';
                                }

                                return (
                                    <div key={idx} className="flex items-center gap-3">
                                        <div className="w-6 h-6 flex items-center justify-center shrink-0">
                                            {state === 'completed' && (
                                                <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                                            )}
                                            {state === 'active' && (
                                                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                                            )}
                                            {state === 'pending' && (
                                                <div className="w-2 h-2 bg-neutral-700 rounded-full" />
                                            )}
                                            {state === 'failed' && (
                                                <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                                            )}
                                        </div>
                                        <span className={`text-sm ${state === 'active' ? 'text-blue-200 font-medium' : state === 'completed' ? 'text-neutral-500 line-through' : state === 'failed' ? 'text-red-400' : 'text-neutral-600'}`}>
                                            {step.label}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>

                        <p className="text-neutral-400 text-center text-sm font-mono bg-black/20 p-2 rounded">
                            "{status.message}"
                        </p>

                        {/* Agent Outputs */}
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
                                {status.artifacts.bible && (
                                    <div className="bg-neutral-900/50 rounded-xl p-4 border border-neutral-700">
                                        <h3 className="text-sm font-bold text-neutral-400 uppercase mb-2">📖 Series Bible</h3>
                                        <div className="max-h-40 overflow-y-auto text-xs font-mono text-neutral-300 whitespace-pre-wrap bg-black/20 p-2 rounded">
                                            {JSON.stringify(status.artifacts.bible, null, 2)}
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
                                    src={getDownloadUrl(jobId!)}
                                />
                                <a
                                    href={getDownloadUrl(jobId!)}
                                    download
                                    className="px-8 py-3 bg-green-600 hover:bg-green-500 rounded-lg font-bold shadow-lg transition-colors flex items-center gap-2"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                                    Download MP4
                                </a>
                            </div>
                        )}
                        {status.status === 'failed' && (
                            <div className="mt-8 p-4 bg-red-900/30 border border-red-500/50 rounded-xl">
                                <p className="text-red-300 font-bold mb-2">Generation Failed</p>
                                <p className="text-red-200 text-sm opacity-80">{status.message}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </main>
    );
}
