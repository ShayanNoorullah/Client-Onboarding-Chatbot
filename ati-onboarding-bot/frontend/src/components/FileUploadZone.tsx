import { useRef, useState } from "react";
import type { UploadedAsset } from "../types/chat";

interface Props {
  sessionId: string;
  enabled: boolean;
  onUploaded: (asset: UploadedAsset, notify: string) => void;
  onNotify: (msg: string) => void;
  assets: UploadedAsset[];
}

const ACCEPT = ".jpg,.jpeg,.png,.gif,.webp,.pdf,.docx,.xlsx,.txt,.csv";

export default function FileUploadZone({ sessionId, enabled, onUploaded, onNotify, assets }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleFiles = async (files: FileList | null) => {
    if (!files?.length || !enabled) return;
    const file = files[0];
    setUploading(true);
    onNotify(`Uploading: ${file.name}...`);

    try {
      const { uploadFile } = await import("../lib/api");
      const data = await uploadFile(sessionId, file);
      const preview = file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined;
      onUploaded({ filename: data.filename, preview }, `I uploaded a file: ${data.filename}`);
      onNotify(`Saved: ${data.filename}`);
    } catch (e) {
      onNotify(`Upload failed: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setUploading(false);
    }
  };

  if (!enabled) return null;

  return (
    <div className="px-4 py-2">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
          dragging ? "border-ati-gold bg-amber-50" : "border-slate-300 hover:border-ati-navy/40"
        } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <p className="text-sm text-slate-600">
          {uploading ? "Uploading..." : "Drag & drop a file here, or click to browse"}
        </p>
        <p className="text-xs text-slate-400 mt-1">JPG, PNG, PDF, DOCX, XLSX, TXT, CSV</p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {assets.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {assets.map((a) => (
            <div key={a.filename} className="flex items-center gap-2 bg-ati-light rounded-lg px-3 py-1.5 text-xs text-ati-navy">
              {a.preview && <img src={a.preview} alt="" className="w-8 h-8 rounded object-cover" />}
              <span>{a.filename}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
