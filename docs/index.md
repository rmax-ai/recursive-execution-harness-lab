---
layout: default
title: Recursive Execution Harness Lab
description: A CLI-first Python research instrument comparing agent architectures on multi-document synthesis tasks.
---

<style>
  :root {
    --bg-color: #0d1117;
    --text-main: #c9d1d9;
    --text-muted: #8b949e;
    --text-heading: #ffffff;
    --border-color: #30363d;
    --bg-surface: #161b22;
    --accent: #58a6ff;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
  }
  * { box-sizing: border-box; }
  body {
    background-color: var(--bg-color);
    color: var(--text-main);
    font-family: var(--font-sans);
    line-height: 1.6;
    margin: 0;
    padding: 0;
    -webkit-font-smoothing: antialiased;
  }
  .container { max-width: 900px; margin: 0 auto; padding: 4rem 2rem; }
  h1, h2, h3, h4 { color: var(--text-heading); margin-top: 0; font-weight: 600; }
  h1 { font-size: 2rem; margin-bottom: 0.5rem; letter-spacing: -0.02em; }
  h2 { font-size: 1.5rem; margin-bottom: 1rem; }
  h3 { font-size: 1.25rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; }
  h4 { font-size: 1rem; margin-bottom: 0.5rem; }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .header { margin-bottom: 4rem; }
  .meta-bar {
    font-family: var(--font-mono); font-size: 0.85rem;
    color: var(--text-muted); margin-bottom: 1rem;
    display: flex; gap: 1rem; align-items: center;
  }
  .meta-tag {
    background: var(--bg-surface); border: 1px solid var(--border-color);
    padding: 0.2rem 0.6rem; border-radius: 4px;
  }
  .subtitle { font-size: 1.2rem; color: var(--text-muted); margin-bottom: 1.5rem; }
  .nav-links { display: flex; gap: 1rem; font-family: var(--font-mono); font-size: 0.9rem; }
  .nav-links a {
    display: inline-block; padding: 0.5rem 1rem;
    border: 1px solid var(--border-color); border-radius: 6px;
    background: var(--bg-surface); color: var(--text-main);
  }
  .nav-links a:hover { border-color: var(--text-muted); text-decoration: none; }
  .hero { margin-bottom: 4rem; }
  .hero h2 {
    font-size: 2.25rem; line-height: 1.3; font-weight: 700;
    letter-spacing: -0.03em; color: var(--text-heading);
    border-left: 4px solid var(--accent); padding-left: 1.5rem; margin: 0;
  }
  .thesis { font-size: 1.1rem; margin-bottom: 4rem; }
  .comparison-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 4rem;
  }
  .card {
    background: var(--bg-surface); border: 1px solid var(--border-color);
    border-radius: 6px; padding: 1.5rem;
  }
  .card h4 { color: var(--accent); font-family: var(--font-mono); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }
  .card p.muted { color: var(--text-muted); font-size: 0.9rem; margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 1rem; }
  .architecture { margin-bottom: 4rem; }
  .quickstart { margin-bottom: 4rem; }
  pre {
    background: var(--bg-surface); border: 1px solid var(--border-color);
    border-radius: 6px; padding: 1.25rem; overflow-x: auto;
    font-family: var(--font-mono); font-size: 0.9rem;
    line-height: 1.5; color: var(--text-main);
  }
  .stack-meta { font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-muted); margin-top: 1rem; }
  .metrics-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem; margin-bottom: 4rem;
  }
  .metric-item { border-left: 2px solid var(--border-color); padding-left: 1rem; }
  .metric-item h4 { margin-bottom: 0.25rem; }
  .metric-item p { margin: 0; font-size: 0.9rem; color: var(--text-muted); }
  .threats { margin-bottom: 4rem; }
  .threats ol { padding-left: 1.25rem; color: var(--text-main); }
  .threats li { margin-bottom: 0.75rem; }
  .contribution {
    border: 1px solid var(--border-color); background: var(--bg-surface);
    padding: 2rem; border-radius: 6px; margin-bottom: 4rem;
    font-size: 1.1rem; line-height: 1.6; color: var(--text-heading); font-style: italic;
  }
  footer {
    border-top: 1px solid var(--border-color); padding-top: 2rem;
    text-align: center; font-family: var(--font-mono);
    font-size: 0.85rem; color: var(--text-muted);
  }
  @media (max-width: 768px) {
    .comparison-grid { grid-template-columns: 1fr; }
    .hero h2 { font-size: 1.75rem; }
  }
</style>

<div class="container">
  <header class="header">
    <div class="meta-bar">
      <span class="meta-tag">v0.1.0</span>
      <span class="meta-tag">38 tests</span>
      <span class="meta-tag">MIT</span>
    </div>
    <h1>Recursive Execution Harness Lab</h1>
    <p class="subtitle">A CLI-first Python research instrument that compares two agent architectures on multi-document synthesis tasks.</p>
    <div class="nav-links">
      <a href="https://github.com/rmax-ai/recursive-execution-harness-lab">GitHub Repository</a>
      <a href="ARCHITECTURE.md">Architecture Docs</a>
    </div>
  </header>

  <main>
    <section class="hero">
      <h2>When does recursive, reference-based execution outperform naive long-context prompting for long-running agent tasks?</h2>
    </section>

    <section class="thesis">
      <h3>Core Thesis</h3>
      <p>Long-running AI agents should not stuff everything into growing context windows. They should execute over durable references, bounded subtasks, evidence stores, and verification gates. This project <strong>measures</strong> whether that claim holds — and under what conditions it breaks.</p>
    </section>

    <section class="comparison">
      <h3>Execution Modes Compared</h3>
      <div class="comparison-grid">
        <div class="card">
          <h4>Mode A: Long-Context</h4>
          <p>Concatenate all documents → one giant prompt → model answers.</p>
          <p class="muted">Simple, common, but degrades with scale. Risk: attention dilution, lost-in-the-middle, no provenance.</p>
        </div>
        <div class="card">
          <h4>Mode B: Recursive</h4>
          <p>Ingest → planner → bounded workers → evidence cards → synthesizer → verifier → policy gate → final answer with provenance trace.</p>
          <p class="muted">More calls. More inspectable. Every claim linked to a source.</p>
        </div>
      </div>
    </section>

    <section class="architecture">
      <h3>Pipeline Architecture</h3>
      <p>The recursive mode externalizes state into a governed execution graph:</p>

flowchart TD
    C[Corpus] --> RS[(Reference Store)]
    RS --> P[Planner]
    P --> BW[Bounded Workers]
    BW --> EC[Evidence Cards]
    EC --> S[Synthesizer]
    S --> V[Verifier]
    V --> PG{Policy Gate}
    PG -- Fail --> P
    PG -- Pass --> FA[Final Answer + Report]

    </section>

    <section class="quickstart">
      <h3>Quickstart</h3>
<pre><code>git clone https://github.com/rmax-ai/recursive-execution-harness-lab
cd recursive-execution-harness-lab
uv sync --extra dev

rxh run --task benchmarks/research_synthesis/tasks/recursive_execution.yaml \
  --corpus benchmarks/research_synthesis/corpora/sample \
  --mode long-context --model gpt-5.5-thinking --out runs/baseline

rxh run --task benchmarks/research_synthesis/tasks/recursive_execution.yaml \
  --corpus benchmarks/research_synthesis/corpora/sample \
  --mode recursive --model gpt-5.5-thinking --out runs/recursive

rxh compare runs/baseline runs/recursive</code></pre>
      <div class="stack-meta">
        <strong>Stack:</strong> Python 3.12+ · Typer CLI · Pydantic v2 · httpx · JSONL traces · Local filesystem · OpenAI-compatible providers
      </div>
    </section>

    <section class="metrics">
      <h3>Key Metrics</h3>
      <div class="metrics-grid">
        <div class="metric-item">
          <h4>Claim Support Rate</h4>
          <p>Fraction of major claims backed by evidence cards</p>
        </div>
        <div class="metric-item">
          <h4>Unsupported Claims</h4>
          <p>Claims the verifier flags as lacking source evidence</p>
        </div>
        <div class="metric-item">
          <h4>Source Attribution Errors</h4>
          <p>Citations that don't match actual documents</p>
        </div>
        <div class="metric-item">
          <h4>Evidence Coverage</h4>
          <p>Cited sources / relevant sources in the corpus</p>
        </div>
        <div class="metric-item">
          <h4>Token Usage</h4>
          <p>Total input + output across all LLM calls</p>
        </div>
        <div class="metric-item">
          <h4>Trace Completeness</h4>
          <p>Required trace events present / total required</p>
        </div>
      </div>
    </section>

    <section class="threats">
      <h3>Threats to Validity</h3>
      <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Every credible measurement instrument documents its limitations. These are ours:</p>
      <ol>
        <li>The verifier is model-based and may share blind spots with the generator.</li>
        <li>The corpus may favor one architecture over another.</li>
        <li>Recursive execution uses more explicit scaffolding — prompt clarity may improve independently of architecture.</li>
        <li>The baseline may be disadvantaged if context limits force document truncation.</li>
        <li>Results from research synthesis may not generalize to coding, customer support, or enterprise workflows.</li>
        <li>Token cost may vary by provider and caching strategy.</li>
        <li>Better long-context models may reduce the observed gap.</li>
      </ol>
    </section>

    <section class="contribution">
      <p>This project does not propose a new foundation model or a new agent framework. It proposes a measurement harness for an architectural question: when should long-running agents rely on larger context, and when should they externalize state into recursive execution, evidence stores, and verification gates?</p>
    </section>
  </main>

  <footer>
    <p>MIT License · v0.1.0 · <a href="https://github.com/rmax-ai/recursive-execution-harness-lab">rmax-ai/recursive-execution-harness-lab</a></p>
  </footer>
</div>
