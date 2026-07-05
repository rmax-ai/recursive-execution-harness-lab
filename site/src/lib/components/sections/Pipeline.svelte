<script lang="ts">
  import { base } from "$app/paths";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">Pipeline Architecture</h3>
<p class="text-slate-400 mb-6">The recursive mode externalizes state into a sequential, reference-indexed execution graph:</p>
<img src="{base}/pipeline.svg" alt="Recursive execution pipeline: Corpus → Document Refs → Planner → Source Slices → Evidence Cards → Synthesizer → Verifier → Revision if needed → Deterministic Policy Gate → Final Answer" class="w-full h-auto max-w-2xl mx-auto" />
<p class="text-slate-500 text-sm mt-6">
  The checked-in diagram still shows the high-level flow. The current harness adds one bounded revision pass after failed verification and applies deterministic policy rules over verifier output.
</p>
