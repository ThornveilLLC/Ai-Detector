export type Verdict = "likely_human" | "uncertain" | "likely_ai";
export type Confidence = "low" | "medium" | "high";
export type ContentType = "text" | "image" | "video" | "audio" | "mixed";

export interface SentenceHighlight {
  sentence: string;
  ai_probability: number;
}

export interface ScanResult {
  content_type: ContentType;
  verdict: Verdict;
  ai_probability: number;
  confidence: Confidence;
  explanation: string;
  suspected_source: string | null;
  sentence_highlights: SentenceHighlight[] | null;
}
