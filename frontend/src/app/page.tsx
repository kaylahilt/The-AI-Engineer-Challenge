"use client";

import { useState, FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import styles from "./page.module.css";

export default function Home() {
  const [userMessage, setUserMessage] = useState("");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

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
        body: JSON.stringify({ message: userMessage }),
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

  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <h1 className={styles.title}>Chat with Aethon</h1>
        <p className={styles.description}>
          Engage in meaningful dialogue with Aethon, your whimsical digital sage who bridges wisdom and wonder.
        </p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputGroup}>
            <label htmlFor="userMessage">Your Message</label>
            <textarea
              id="userMessage"
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              placeholder="What would you like to ask?"
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
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {response}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
