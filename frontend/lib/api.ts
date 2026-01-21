// Since we are using Next.js rewrites, we can simply call the relative path.
// This works because the Next.js server (frontend) will proxy the request to the backend.

export async function submitJob(story: string) {
    const res = await fetch(`/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story }),
    });
    if (!res.ok) throw new Error("Failed to submit job");
    return res.json();
}

export async function getJobStatus(jobId: string) {
    const res = await fetch(`/status/${jobId}`);
    if (!res.ok) throw new Error("Failed to get status");
    return res.json();
}

export function getDownloadUrl(jobId: string) {
    return `/download/${jobId}`;
}
