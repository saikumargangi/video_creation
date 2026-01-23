// Since we are using Next.js rewrites, we can simply call the relative path.
// This works because the Next.js server (frontend) will proxy the request to the backend.

export async function submitJob(story: string, characterJobId?: string | null) {
    const body: any = { story };
    if (characterJobId) body.character_job_id = characterJobId;

    const res = await fetch(`/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("Failed to submit job");
    return res.json();
}

export async function submitCharacterGen(prompt: string) {
    const res = await fetch(`/generate_character`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
    });
    if (!res.ok) throw new Error("Failed to submit character generation");
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
