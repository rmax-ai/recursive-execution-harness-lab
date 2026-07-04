<script lang="ts">
  import { STACK } from "$lib/data/meta";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">Quickstart</h3>

<pre class="bg-black border border-slate-800 rounded-lg p-5 overflow-x-auto font-mono text-sm leading-relaxed text-slate-300">
<code>git clone https://github.com/rmax-ai/recursive-execution-harness-lab
cd recursive-execution-harness-lab
uv sync --extra dev

rxh run --task benchmarks/research_synthesis/tasks/recursive_execution.yaml \
  --corpus benchmarks/research_synthesis/corpora/sample \
  --mode long-context --model gpt-5.5-thinking --out runs/baseline

rxh run --task benchmarks/research_synthesis/tasks/recursive_execution.yaml \
  --corpus benchmarks/research_synthesis/corpora/sample \
  --mode recursive --model gpt-5.5-thinking --out runs/recursive

rxh compare runs/baseline runs/recursive</code>
</pre>

<p class="mt-4 font-mono text-sm text-slate-500">
  <strong class="text-slate-400">Stack:</strong> {STACK.join(" · ")}
</p>
