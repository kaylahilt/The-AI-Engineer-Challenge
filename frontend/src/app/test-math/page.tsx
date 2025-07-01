"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import styles from "../page.module.css";

export default function TestMath() {
  const testContent = `
# Math Rendering Test

## Inline Math
Here's inline math: $x = 5$ and $y = 10$

## Display Math
Here's display math:

$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

## Your Example
Number of packs of apples = $\\frac{\\text{Total apples}}{\\text{Apples per pack}} = \\frac{12}{4} = 3$

Number of packs of oranges = $\\frac{9}{3} = 3$
`;

  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <h1 className={styles.title}>Math Rendering Test</h1>
        <div className={styles.response}>
          <div className={styles.markdown}>
            <ReactMarkdown 
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {testContent}
            </ReactMarkdown>
          </div>
        </div>
        <p>If math renders above, the issue is with the API response format.</p>
      </div>
    </main>
  );
} 