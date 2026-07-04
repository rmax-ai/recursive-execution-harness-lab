<script lang="ts">
  import { base } from "$app/paths";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">Pipeline Architecture</h3>
<p class="text-slate-400 mb-6">The recursive mode externalizes state into a governed execution graph:</p>
<img src="{base}/pipeline.svg" alt="Recursive execution pipeline: Corpus → Reference Store → Planner → Bounded Workers → Evidence Cards → Synthesizer → Verifier → Policy Gate → Final Answer" class="w-full h-auto max-w-2xl mx-auto" />
