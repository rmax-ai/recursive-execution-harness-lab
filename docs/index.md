---
layout: default
title: Puff — Recursive Execution Harness Lab
description: A research harness for comparing long-context agents against recursive evidence-based execution
---

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    :root {
        --bg: #0d1117;
        --card-bg: #161b22;
        --border: #30363d;
        --text-main: #c9d1d9;
        --text-muted: #8b949e;
        --accent: #58a6ff;
        --code-bg: #010409;
        --warning: #d29922;
    }
    body {
        background-color: var(--bg);
        color: var(--text-main);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }
    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 40px 20px;
    }
    header {
        border-bottom: 1px solid var(--border);
        padding-bottom: 40px;
        margin-bottom: 40px;
    }
    h1 { font-size: 2.2rem; color: #f0f6fc; margin-bottom: 8px; letter-spacing: -0.02em; }
    h2 { font-size: 1.5rem; color: #f0f6fc; margin-top: 48px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
    h3 { color: var(--accent); font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0; }
    .badge {
        display: inline-block;
        background: var(--card-bg);
        border: 1px solid var(--border);
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        color: var(--accent);
        font-weight: 600;
    }
    .thesis-box {
        background: rgba(88, 166, 255, 0.05);
        border-left: 4px solid var(--accent);
        padding: 20px 24px;
        margin: 24px 0;
        font-size: 1.1rem;
        font-style: italic;
        color: #e6edf3;
    }
    .grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-top: 20px;
    }
    @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    .card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 24px;
    }
    .card ul { padding-left: 18px; margin-bottom: 0; }
    .card li { margin-bottom: 8px; font-size: 0.95rem; }
    .card .flow { color: var(--text-muted); font-size: 0.9rem; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
    pre, code {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        background: var(--code-bg);
        border-radius: 6px;
    }
    pre { padding: 16px; overflow-x: auto; border: 1px solid var(--border); font-size: 0.85rem; }
    code { font-size: 0.9rem; }
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 12px;
        margin-top: 20px;
    }
    .metric-item {
        background: var(--card-bg);
        border: 1px solid var(--border);
        padding: 12px 16px;
        border-radius: 6px;
    }
    .metric-item strong { color: var(--accent); display: block; margin-bottom: 4px; }
    .metric-item span { color: var(--text-muted); font-size: 0.9rem; }
    blockquote {
        border-left: 4px solid var(--border);
        padding: 16px 24px;
        margin: 40px 0;
        font-size: 1.05rem;
        color: #e6edf3;
        background: var(--card-bg);
        border-radius: 0 6px 6px 0;
    }
    .footer {
        margin-top: 80px;
        padding-top: 20px;
        border-top: 1px solid var(--border);
        font-size: 0.85rem;
        color: var(--text-muted);
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .limitations ol { padding-left: 20px; }
    .limitations li { margin-bottom: 12px; color: var(--text-muted); }
    .mermaid-wrapper {
        background: #fff;
        padding: 24px;
        border-radius: 6px;
        margin: 20px 0;
        border: 1px solid var(--border);
    }
</style>
</head>
<body>

<div class="container">
    <header>
        <div class="badge">v0.1.0 · MIT</div>
        <h1>Puff <span style="font-weight:400;color:var(--text-muted);font-size:1.4rem;">· Recursive Execution Harness Lab</span></h1>
        <p style="color: var(--text-muted); max-width: 650px;">
            A measurement instrument comparing two agent architectures on multi-document research synthesis:
            monolithic long-context prompts vs. recursive, evidence-based execution.
        </p>
        <div style="margin-top: 16px;">
            <a href="https://github.com/rmax-ai/recursive-execution-harness-lab">GitHub Repository</a>
            &nbsp;·&nbsp;
            <a href="ARCHITECTURE.md">Architecture Docs</a>
        </div>
    </header>

    <section>
        <h2>Research Question</h2>
        <div class="thesis-box">
            When does recursive, reference-based execution outperform naive long-context prompting for long-running agent tasks?
        </div>
        <p style="color: var(--text-muted); font-size: 0.95rem;">
            Secondary: Which failure modes are reduced by recursive execution? Which remain?
            How much token cost is saved? Does evidence provenance improve final-answer trust?
        </p>
    </section>

    <section>
        <h2>Experiment Modes</h2>
        <div class="grid">
            <div class="card">
                <h3>A · Long-Context</h3>
                <ul>
                    <li>Concatenate all documents into one prompt</li>
                    <li>Single model call produces the final answer</li>
                    <li>Low orchestration overhead</li>
                    <li>Risk: attention dilution, lost-in-the-middle</li>
                </ul>
                <div class="flow">corpus → giant prompt → model → answer</div>
            </div>
            <div class="card">
                <h3>B · Recursive</h3>
                <ul>
                    <li>Planner decomposes task into subquestions</li>
                    <li>Bounded workers extract evidence cards</li>
                    <li>Synthesizer writes from evidence store</li>
                    <li>Verifier checks every claim against sources</li>
                </ul>
                <div class="flow">corpus → refs → plan → workers → evidence → synthesis → verification</div>
            </div>
        </div>
    </section>

    <section>
        <h2>Architecture</h2>
        <div class="mermaid-wrapper">

flowchart TD
    A[Task Spec] --> B[Corpus Ingestion]
    B --> C[Reference Store]
    C --> D[Planner]
    D --> E[Plan Items]
    E --> F1[Evidence Worker 1]
    E --> F2[Evidence Worker 2]
    F1 --> G[Evidence Store]
    F2 --> G
    G --> H[Synthesizer]
    H --> I[Verifier]
    I --> J[Policy Gate]
    J --> K[Final Answer]

        </div>
    </section>

    <section>
        <h2>Quickstart</h2>
        <pre><code>git clone https://github.com/rmax-ai/recursive-execution-harness-lab
cd recursive-execution-harness-lab
uv sync --extra dev

# Run baseline
rxh run --task benchmarks/research_synthesis/tasks/recursive_execution.yaml \
  --corpus benchmarks/research_synthesis/corpora/sample \
  --mode long-context --model gpt-5.5-thinking --out runs/baseline

# Run recursive
rxh run --task benchmarks/research_synthesis/tasks/recursive_execution.yaml \
  --corpus benchmarks/research_synthesis/corpora/sample \
  --mode recursive --model gpt-5.5-thinking --out runs/recursive

# Compare
rxh compare runs/baseline runs/recursive</code></pre>
    </section>

    <section>
        <h2>Key Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-item">
                <strong>Claim Support Rate</strong>
                <span>supported claims / total claims</span>
            </div>
            <div class="metric-item">
                <strong>Unsupported Claims</strong>
                <span>claims the verifier flags as lacking evidence</span>
            </div>
            <div class="metric-item">
                <strong>Source Attribution Errors</strong>
                <span>citations that don't match actual sources</span>
            </div>
            <div class="metric-item">
                <strong>Evidence Coverage</strong>
                <span>cited sources / relevant sources</span>
            </div>
            <div class="metric-item">
                <strong>Token Usage</strong>
                <span>total input + output across all LLM calls</span>
            </div>
            <div class="metric-item">
                <strong>Trace Completeness</strong>
                <span>required events present / total required</span>
            </div>
        </div>
    </section>

    <section class="limitations">
        <h2>Threats to Validity</h2>
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

    <section>
        <blockquote>
            This project does not propose a new foundation model or a new agent framework. It proposes a measurement harness for an architectural question: when should long-running agents rely on larger context, and when should they externalize state into recursive execution, evidence stores, and verification gates?
        </blockquote>
    </section>

    <div class="footer">
        <span>MIT License · v0.1.0</span>
        <span><a href="https://github.com/rmax-ai/recursive-execution-harness-lab">rmax-ai/recursive-execution-harness-lab</a></span>
    </div>
</div>

</body>
</html>
