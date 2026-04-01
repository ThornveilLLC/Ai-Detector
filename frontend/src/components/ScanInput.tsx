import { useState, useRef } from "react";
import type { ScanResult } from "../types";
import styles from "./ScanInput.module.css";

type Tab = "text" | "image" | "video" | "audio";

interface Props {
  onResult: (result: ScanResult) => void;
  onLoading: (loading: boolean) => void;
  loading: boolean;
}

export function ScanInput({ onResult, onLoading, loading }: Props) {
  const [tab, setTab] = useState<Tab>("text");
  const [text, setText] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [imageDragOver, setImageDragOver] = useState(false);
  const [audioDragOver, setAudioDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const imageFileRef = useRef<HTMLInputElement>(null);
  const audioFileRef = useRef<HTMLInputElement>(null);

  async function submit(formData: FormData) {
    setError(null);
    onLoading(true);
    try {
      const res = await fetch("/api/scan", { method: "POST", body: formData });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Server error ${res.status}`);
      }
      const result: ScanResult = await res.json();
      onResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      onLoading(false);
    }
  }

  function handleTextSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    const fd = new FormData();
    fd.append("text", text);
    submit(fd);
  }

  function handleImageUrlSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!imageUrl.trim()) return;
    const fd = new FormData();
    fd.append("image_url", imageUrl);
    submit(fd);
  }

  function handleVideoUrlSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!videoUrl.trim()) return;
    const fd = new FormData();
    fd.append("video_url", videoUrl);
    submit(fd);
  }

  function handleImageFile(file: File) {
    const fd = new FormData();
    fd.append("image", file);
    submit(fd);
  }

  function handleAudioFile(file: File) {
    const fd = new FormData();
    fd.append("audio", file);
    submit(fd);
  }

  function handleImageDrop(e: React.DragEvent) {
    e.preventDefault();
    setImageDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleImageFile(file);
  }

  function handleAudioDrop(e: React.DragEvent) {
    e.preventDefault();
    setAudioDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleAudioFile(file);
  }

  const TABS: { id: Tab; label: string }[] = [
    { id: "text",  label: "Text"  },
    { id: "image", label: "Image" },
    { id: "video", label: "Video" },
    { id: "audio", label: "Audio" },
  ];

  return (
    <div className={styles.container}>
      {/* Tabs */}
      <div className={styles.tabs}>
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            className={`${styles.tab} ${tab === id ? styles.active : ""}`}
            onClick={() => { setTab(id); setError(null); }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── Text ── */}
      {tab === "text" && (
        <form onSubmit={handleTextSubmit} className={styles.form}>
          <div className={styles.textareaWrap}>
            <textarea
              className={styles.textarea}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste text, a social media caption, article excerpt, or any content you want analyzed…"
              rows={8}
            />
            <div className={styles.textareaFooter}>
              <span className={styles.charCount}>
                <span className={styles.monoVal}>{text.length.toLocaleString()}</span> chars
              </span>
              <button className={styles.button} disabled={loading || !text.trim()}>
                {loading ? "Analyzing…" : "Analyze Text →"}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* ── Image ── */}
      {tab === "image" && (
        <div className={styles.form}>
          <div
            className={`${styles.dropzone} ${imageDragOver ? styles.dragOver : ""}`}
            onDragOver={(e) => { e.preventDefault(); setImageDragOver(true); }}
            onDragLeave={() => setImageDragOver(false)}
            onDrop={handleImageDrop}
            onClick={() => imageFileRef.current?.click()}
          >
            <div className={styles.dropIconWrap}>
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden>
                <rect x="4" y="6" width="24" height="20" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                <circle cx="12" cy="14" r="2.5" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M4 24l7-7 4 4 4-6 9 9" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              </svg>
            </div>
            <p className={styles.dropText}>Drop an image or <span className={styles.link}>browse</span></p>
            <p className={styles.dropHint}>JPG · PNG · WebP · GIF</p>
            <input
              ref={imageFileRef}
              type="file"
              accept="image/*"
              hidden
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleImageFile(f); }}
            />
          </div>

          <div className={styles.divider}>
            <span className={styles.dividerText}>or paste a URL</span>
          </div>

          <form onSubmit={handleImageUrlSubmit} className={styles.urlRow}>
            <input
              className={styles.input}
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://example.com/photo.jpg"
              type="url"
            />
            <button className={styles.button} disabled={loading || !imageUrl.trim()}>
              {loading ? "…" : "Scan"}
            </button>
          </form>
        </div>
      )}

      {/* ── Video ── */}
      {tab === "video" && (
        <form onSubmit={handleVideoUrlSubmit} className={styles.form}>
          <div className={styles.videoInfo}>
            <div className={styles.videoIconWrap}>
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden>
                <rect x="2" y="5" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M20 10l6-4v16l-6-4V10z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <p className={styles.infoTitle}>Video URL Analysis</p>
              <p className={styles.dropHint}>MP4 · MOV · WebM · direct video links</p>
            </div>
          </div>
          <div className={styles.urlRow}>
            <input
              className={styles.input}
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://example.com/video.mp4"
              type="url"
            />
            <button className={styles.button} disabled={loading || !videoUrl.trim()}>
              {loading ? "…" : "Scan"}
            </button>
          </div>
        </form>
      )}

      {/* ── Audio ── */}
      {tab === "audio" && (
        <div className={styles.form}>
          <div
            className={`${styles.dropzone} ${audioDragOver ? styles.dragOver : ""}`}
            onDragOver={(e) => { e.preventDefault(); setAudioDragOver(true); }}
            onDragLeave={() => setAudioDragOver(false)}
            onDrop={handleAudioDrop}
            onClick={() => audioFileRef.current?.click()}
          >
            <div className={styles.dropIconWrap}>
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden>
                <path d="M16 4v24" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                <path d="M8 10v12M12 7v18M20 7v18M24 10v12M4 16v0M28 16v0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <p className={styles.dropText}>Drop audio or <span className={styles.link}>browse</span></p>
            <p className={styles.dropHint}>MP3 · WAV · OGG · M4A</p>
            <input
              ref={audioFileRef}
              type="file"
              accept="audio/*"
              hidden
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleAudioFile(f); }}
            />
          </div>
          <p className={styles.audioNote}>
            Audio is analyzed for AI-generated speech and synthetic voice patterns via the Hive API.
          </p>
        </div>
      )}

      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}
