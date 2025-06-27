"use client";

import { useState, FormEvent } from "react";
import styles from "./page.module.css";

export default function Home() {
  const [developerMessage, setDeveloperMessage] = useState(
    "You are a helpful assistant."
  );
  const [userMessage, setUserMessage] = useState("");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setResponse("");



    try {
      const res = await fetch("https://the-ai-engineer-challenge-bice.vercel.app/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          developer_message: developerMessage,
          user_message: userMessage,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) {
        throw new Error("Failed to get response reader");
      }
      
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        setResponse((prev) => prev + chunk);
      }
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
        <h1 className={styles.title}>AI-Engineer-Challenge Chat</h1>
        <p className={styles.description}>
          Provide the messages below to start a chat with AI.
        </p>

        <form onSubmit={handleSubmit} className={styles.form}>


          <div className={styles.inputGroup}>
            <label htmlFor="developerMessage">Developer Message</label>
            <textarea
              id="developerMessage"
              value={developerMessage}
              onChange={(e) => setDeveloperMessage(e.target.value)}
              rows={3}
              required
            />
          </div>

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
            <p>{response}</p>
          </div>
        )}
      </div>
    </main>
  );
}
