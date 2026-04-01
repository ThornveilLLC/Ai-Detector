import { useState } from "react";
import type { ScanResult } from "./types";
import { ScanInput } from "./components/ScanInput";
import { ScanResultView } from "./components/ScanResult";
import styles from "./App.module.css";

export default function App() {
  const [result, setResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.wordmark}>
          <div className={styles.scanIcon}>
            <span className={styles.scanRingOuter} />
            <span className={styles.scanRingInner} />
            <span className={styles.scanDot} />
          </div>
          <div className={styles.wordmarkText}>
            <span className={styles.logoText}>RealCheck</span>
            <span className={styles.logoSub}>FORENSIC AI ANALYSIS</span>
          </div>
        </div>
        <p className={styles.tagline}>
          Is it human-made or AI-generated?<br />
          Analyze text, images, audio, and video — instantly.
        </p>
        <div className={styles.statusRow}>
          <div className={styles.statusPill}>
            <span className={styles.statusDot} />
            <span>ONLINE</span>
          </div>
          <div className={styles.statusPill}>
            <span>Image · Text · Audio · Video</span>
          </div>
        </div>
      </header>

      <main className={styles.main}>
        {loading && (
          <div className={styles.loadingOverlay}>
            <div className={styles.loadingScanner}>
              <div className={styles.scannerLine} />
            </div>
            <div className={styles.loadingText}>
              <span className={styles.loadingLabel}>ANALYZING</span>
              <span className={styles.loadingDots}>
                <span /><span /><span />
              </span>
            </div>
          </div>
        )}
        {!result ? (
          <ScanInput onResult={setResult} onLoading={setLoading} loading={loading} />
        ) : (
          <ScanResultView result={result} onReset={() => setResult(null)} />
        )}
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerPowered}>
          Powered by <strong>Sightengine</strong> · <strong>Claude</strong> · <strong>Hive</strong>
        </div>
        <div className={styles.footerNote}>
          © 2026 Thornveil LLC · Results indicate likelihood, not certainty.
        </div>
      </footer>
    </div>
  );
}
