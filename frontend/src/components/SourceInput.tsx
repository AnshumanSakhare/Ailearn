"use client";

import { useState, useRef } from "react";
import { Link2, Upload, Loader2, Youtube, FileText } from "lucide-react";
import toast from "react-hot-toast";
import { processVideo, processPDF, ProcessResponse } from "@/lib/api";

interface Props {
  onProcessed: (res: ProcessResponse) => void;
  loading: boolean;
  setLoading: (v: boolean) => void;
}

export default function SourceInput({ onProcessed, loading, setLoading }: Props) {
  const [mode, setMode] = useState<"video" | "pdf">("video");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      let res: ProcessResponse;
      if (mode === "video") {
        if (!url.trim()) { toast.error("Please enter a YouTube URL"); return; }
        res = await processVideo(url.trim());
        toast.success("Video processed!");
      } else {
        if (!file) { toast.error("Please select a PDF file"); return; }
        res = await processPDF(file);
        toast.success("PDF processed!");
      }
      onProcessed(res);
    } catch (err: any) {
      toast.error(err.message ?? "Processing failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card p-6 animate-fade-in">
      <h2 className="text-lg font-semibold text-slate-200 mb-4">
        Add Learning Material
      </h2>

      {/* Mode toggle */}
      <div className="flex gap-2 mb-5">
        <button
          type="button"
          onClick={() => setMode("video")}
          className={`tab-btn flex items-center gap-2 ${mode === "video" ? "tab-active" : "tab-inactive"}`}
        >
          <Youtube className="w-4 h-4" /> YouTube Video
        </button>
        <button
          type="button"
          onClick={() => setMode("pdf")}
          className={`tab-btn flex items-center gap-2 ${mode === "pdf" ? "tab-active" : "tab-inactive"}`}
        >
          <FileText className="w-4 h-4" /> PDF Document
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === "video" ? (
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                className="input pl-10"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
        ) : (
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-slate-600 hover:border-brand-500
                       rounded-xl p-8 text-center cursor-pointer transition-colors group"
          >
            <Upload className="w-8 h-8 mx-auto text-slate-500 group-hover:text-brand-400 mb-2 transition-colors" />
            <p className="text-slate-400 text-sm">
              {file ? (
                <span className="text-brand-400 font-medium">{file.name}</span>
              ) : (
                <>Click to upload PDF <span className="text-slate-600">(max 20 MB)</span></>
              )}
            </p>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
        )}

        <button className="btn-primary w-full justify-center" disabled={loading}>
          {loading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Processing…</>
          ) : (
            "Process & Extract"
          )}
        </button>
      </form>
    </div>
  );
}
