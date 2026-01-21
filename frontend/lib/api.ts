const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function submitJob(story: string) {
    const res = await fetch(`${API_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story }),
    });
    if (!res.ok) throw new Error("Failed to submit job");
    return res.json();
}

export async function getJobStatus(jobId: string) {
    const res = await fetch(`${API_URL}/status/${jobId}`);
    if (!res.ok) throw new Error("Failed to get status");
    return res.json();
}

export function getDownloadUrl(jobId: string) {
    return `${API_URL}/download/${jobId}`;
}
