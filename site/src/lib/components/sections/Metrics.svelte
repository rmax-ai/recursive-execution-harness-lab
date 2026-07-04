<script lang="ts">
  import { METRICS } from "$lib/data/meta";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">Key Metrics</h3>

<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  {#each METRICS as metric}
    <div class="border-l-2 border-slate-800 pl-4 py-1">
      <h4 class="text-sm font-semibold text-indigo-400 mb-1">{metric.label}</h4>
      <p class="text-sm text-slate-500">{metric.desc}</p>
    </div>
  {/each}
</div>
