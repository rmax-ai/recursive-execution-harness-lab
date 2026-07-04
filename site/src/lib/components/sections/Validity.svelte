<script lang="ts">
  import { THREATS } from "$lib/data/meta";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">Threats to Validity</h3>

<p class="text-slate-500 text-sm mb-6">
  Every credible measurement instrument documents its limitations. These are ours:
</p>

<ol class="space-y-3 text-slate-400 list-decimal list-inside marker:text-slate-600">
  {#each THREATS as threat, i}
    <li class="leading-relaxed">{threat}</li>
  {/each}
</ol>
