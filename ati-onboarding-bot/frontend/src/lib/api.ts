export async function uploadFile(sessionId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`/upload/${sessionId}`, { method: "POST", body: form });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || "Upload failed");
  return data as {
    status: string;
    filename: string;
    description_preview: string;
  };
}

export async function checkHealth() {
  const resp = await fetch("/health");
  return resp.json();
}
