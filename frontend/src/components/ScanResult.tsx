import { useEffect, useState } from "react";
import type { ScanResult, Verdict } from "../types";
import styles from "./ScanResult.module.css";

interface Props {
  result: ScanResult;
  onReset: () => void;
}

const VERDICT_CONFIG: Record<Verdict, {
  label: string;
  description: string;
  verdictClass: string;
}> = {
  likely_human: {
    label: "LIKELY HUMAN",
    description: "Content shows strong indicators of human authorship.",
    verdictClass: "human",
  },
  uncertain: {
    label: "UNCERTAIN",
    description: "Mixed signals — could be human, AI, or heavily edited content.",
    verdictClass: "uncertain",
  },
  likely_ai: {
    label: "LIKELY AI",
    description: "Content shows strong indicators of AI generation.",
    verdictClass: "ai",
  },
};

const CONFIDENCE_LABEL: Record<string, string> = {
  low:    "Low confidence",
  medium: "Moderate confidence",
  high:   "High confidence",
};

export function ScanResultView({ result, onReset }: Props) {
  const [barFilled, setBarFilled] = useState(false);
  const pct = Math.round(result.ai_probability * 100);
  const cfg = VERDICT_CONFIG[result.verdict];
  const vc = cfg.verdictClass as keyof typeof styles;

  useEffect(() => {
    const t = setTimeout(() => setBarFilled(true), 80);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className={styles.container}>

      {/* ── Verdict block ── */}
      <div className={`${styles.verdict} ${styles[vc]}`}>
        <div className={styles.verdictTop}>
          <div className={styles.verdictLabel}>{cfg.label}</div>
          <div className={styles.verdictPct}>
            {pct}<span className={styles.pctSign}>%</span>
          </div>
        </div>
        <div className={styles.verdictMeta}>
          <span className={styles.metaTag}>{CONFIDENCE_LABEL[result.confidence]}</span>
          <span className={styles.metaSep}>·</span>
          <span className={styles.metaTag}>{result.content_type.toUpperCase()} SCAN</span>
        </div>
        <p className={styles.verdictDescription}>{cfg.description}</p>
      </div>

      {/* ── Probability meter ── */}
      <div className={styles.section} style={{ animationDelay: "0.1s" }}>
        <div className={styles.meterHeader}>
          <span className={styles.meterEdge}>Human</span>
          <span className={styles.meterTitle}>AI PROBABILITY SCORE</span>
          <span className={styles.meterEdge}>AI</span>
        </div>
        <div className={styles.meterTrack}>
          <div
            className={`${styles.meterFill} ${styles[vc]}`}
            style={{
              width: barFilled ? `${pct}%` : "0%",
              transition: "width 1.2s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
          />
          <div
            className={styles.meterThumb}
            style={{
              left: barFilled ? `${pct}%` : "0%",
              transition: "left 1.2s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
          />
        </div>
        <div className={styles.meterTicks}>
          <span>0%</span>
          <span>25%</span>
          <span>50%</span>
          <span>75%</span>
          <span>100%</span>
        </div>
      </div>

      {/* ── Explanation ── */}
      <div className={styles.section} style={{ animationDelay: "0.18s" }}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionLabel}>WHY WE THINK THIS</span>
        </div>
        <p className={styles.explanation}>{result.explanation}</p>
        {result.suspected_source && (
          <div className={styles.suspectedBadge}>
            <span className={styles.suspectedIcon}>⚡</span>
            Suspected source: <strong>{result.suspected_source}</strong>
          </div>
        )}
      </div>

      {/* ── Sentence highlights ── */}
      {result.sentence_highlights && result.sentence_highlights.length > 0 && (
        <div className={styles.section} style={{ animationDelay: "0.26s" }}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionLabel}>AI-FLAGGED SENTENCES</span>
            <span className={styles.sectionCount}>
              {result.sentence_highlights.length} flagged
            </span>
          </div>
          <div className={styles.highlights}>
            {result.sentence_highlights.map((h, i) => {
              const p = h.ai_probability;
              return (
                <div
                  key={i}
                  className={styles.highlight}
                  style={{
                    background: `rgba(239, 68, 68, ${p * 0.13})`,
                    borderColor: `rgba(239, 68, 68, ${p * 0.35})`,
                  }}
                >
                  <div className={styles.highlightScore}>
                    <span className={styles.highlightPct}>
                      {Math.round(p * 100)}%
                    </span>
                    <div className={styles.highlightBar}>
                      <div
                        className={styles.highlightFill}
                        style={{ width: `${Math.round(p * 100)}%` }}
                      />
                    </div>
                  </div>
                  <p className={styles.highlightText}>"{h.sentence}"</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Footer ── */}
      <div className={styles.resultFooter}>
        <p className={styles.disclaimer}>
          AI detection is probabilistic, not definitive. Results should not be used as sole
          evidence for any decision. False positives can occur, especially for structured or ESL writing.
        </p>
        <button className={styles.resetButton} onClick={onReset}>
          ← Scan something else
        </button>
      </div>

    </div>
  );
}
