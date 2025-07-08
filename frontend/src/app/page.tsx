"use client";

import { useState, FormEvent, ChangeEvent, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import styles from "./page.module.css";

export default function Home() {
  const [userMessage, setUserMessage] = useState("");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [pdfInfo, setPdfInfo] = useState<{
    filename: string;
    pdf_id: string;
    num_chunks: number;
    named_entities?: { text: string; label: string; count: number }[];
  } | null>(null);
  const [isUploadingPdf, setIsUploadingPdf] = useState(false);
  const [usePdf, setUsePdf] = useState(true);
  const [extractEntities, setExtractEntities] = useState(false);
  const [isExtractingEntities, setIsExtractingEntities] = useState(false);

  // Handle entity extraction when checkbox changes
  useEffect(() => {
    if (pdfInfo && extractEntities && !pdfInfo.named_entities) {
      handleExtractEntities();
    } else if (pdfInfo && !extractEntities && pdfInfo.named_entities) {
      // Clear entities when unchecked
      setPdfInfo(prev => prev ? {
        ...prev,
        named_entities: undefined
      } : null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [extractEntities, pdfInfo?.pdf_id]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!userMessage.trim()) return;

    setIsLoading(true);
    setError("");
    setResponse("");

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: userMessage,
          use_pdf: usePdf && pdfInfo !== null
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResponse(data.response);
    } catch (err: any) {
      setError(
        `Failed to get response: ${err.message}. Is the backend server running?`
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handlePdfUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || file.type !== 'application/pdf') {
      setError("Please select a PDF file");
      return;
    }

    setIsUploadingPdf(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append('pdf', file);
      formData.append('extract_entities', 'false');

      const response = await fetch('/api/upload-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const data = await response.json();
      setPdfInfo({
        filename: data.filename,
        pdf_id: data.pdf_id,
        num_chunks: data.num_chunks,
        named_entities: data.named_entities
      });
      setUsePdf(true);
    } catch (err: any) {
      setError(`Failed to upload PDF: ${err.message}`);
    } finally {
      setIsUploadingPdf(false);
    }
  };

  const handleExtractEntities = async () => {
    if (!pdfInfo) return;

    setIsExtractingEntities(true);
    setError("");

    try {
      const response = await fetch('/api/extract-entities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          pdf_id: pdfInfo.pdf_id
        }),
      });

      if (!response.ok) {
        throw new Error(`Entity extraction failed: ${response.status}`);
      }

      const data = await response.json();
      setPdfInfo(prev => prev ? {
        ...prev,
        named_entities: data.named_entities
      } : null);
    } catch (err: any) {
      setError(`Failed to extract entities: ${err.message}`);
    } finally {
      setIsExtractingEntities(false);
    }
  };

  const handleClearPdf = async () => {
    try {
      const response = await fetch('/api/clear-pdf', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Clear failed: ${response.status}`);
      }

      setPdfInfo(null);
      setUsePdf(false);
      setExtractEntities(false);
      setError("");
    } catch (err: any) {
      setError(`Failed to clear PDF: ${err.message}`);
    }
  };

  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <h1 className={styles.title}>Chat with Aethon</h1>
        <p className={styles.description}>
          Engage in meaningful dialogue with Aethon, your whimsical digital sage who bridges wisdom and wonder.
        </p>

        {/* PDF Upload Section */}
        <div className={styles.pdfSection}>
          <h3>PDF Knowledge Base</h3>
          {!pdfInfo ? (
            <div className={styles.uploadArea}>
              <input
                type="file"
                accept=".pdf"
                onChange={handlePdfUpload}
                disabled={isUploadingPdf}
                id="pdf-upload"
                className={styles.fileInput}
              />
              <label htmlFor="pdf-upload" className={styles.uploadButton}>
                {isUploadingPdf ? "Uploading..." : "Upload PDF"}
              </label>
              <p className={styles.uploadHint}>
                Upload a PDF to enable document-based Q&A
              </p>
              <p className={styles.uploadWarning}>
                ⚠️ Note: On Vercel, PDFs are stored temporarily and may be cleared between sessions
              </p>
            </div>
          ) : (
            <div className={styles.pdfInfo}>
              <div className={styles.pdfDetails}>
                <strong>📄 {pdfInfo.filename}</strong>
                <span className={styles.chunks}>
                  {pdfInfo.num_chunks} text chunks indexed
                </span>
              </div>
              {pdfInfo.named_entities && pdfInfo.named_entities.length > 0 && (
                <div className={styles.namedEntities}>
                  <h4>Top Named Entities:</h4>
                  <ul className={styles.entityList}>
                    {pdfInfo.named_entities.map((entity, index) => (
                      <li key={index}>
                        <span className={styles.entityText}>{entity.text}</span>
                        <span className={styles.entityLabel} title={
                          entity.label === 'PERSON' ? 'Person' :
                          entity.label === 'ORG' ? 'Organization' :
                          'Entity'
                        }>{entity.label}</span>
                        <span className={styles.entityCount}>({entity.count})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className={styles.pdfControls}>
                <div className={styles.checkboxGroup}>
                  <label className={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={usePdf}
                      onChange={(e) => setUsePdf(e.target.checked)}
                    />
                    Use PDF context
                  </label>
                  <label className={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={extractEntities}
                      onChange={(e) => setExtractEntities(e.target.checked)}
                      disabled={isExtractingEntities}
                    />
                    {isExtractingEntities ? "Extracting entities..." : "Extract named entities"}
                  </label>
                </div>
                <button
                  onClick={handleClearPdf}
                  className={styles.clearButton}
                >
                  Clear PDF
                </button>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputGroup}>
            <label htmlFor="userMessage">
              Your Message {pdfInfo && usePdf && "(PDF context enabled)"}
            </label>
            <textarea
              id="userMessage"
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              placeholder={
                pdfInfo && usePdf
                  ? "Ask about the PDF content..."
                  : "What would you like to ask?"
              }
              rows={5}
              required
            />
          </div>

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Getting Response..." : "Send"}
          </button>
        </form>

        {error && <p className={styles.error}>{error}</p>}

        {response && (
          <div className={styles.response}>
            <h2>Response</h2>
            <div className={styles.markdown}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {response}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
