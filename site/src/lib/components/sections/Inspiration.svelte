<script lang="ts">
  import { REFERENCE } from "$lib/data/meta";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">
  Inspiration & References
</h3>

<p class="text-slate-500 text-sm mb-8">
  This project is informed by the emerging consensus that long-running agents need
  architectural patterns beyond raw context scaling.
</p>

<!-- Featured reference card -->
<a
  href={REFERENCE.url}
  target="_blank"
  rel="noopener noreferrer"
  class="block border border-slate-800 bg-gradient-to-br from-slate-900 to-indigo-950/20 rounded-lg p-6 mb-10 hover:border-indigo-700/50 transition-colors group"
>
  <div class="flex items-start justify-between flex-wrap gap-2 mb-3">
    <div>
      <h4 class="text-lg font-semibold text-white group-hover:text-indigo-300 transition-colors">
        {REFERENCE.title}
      </h4>
      <p class="text-slate-500 text-sm mt-1">
        {REFERENCE.speaker} &middot; {REFERENCE.role}
      </p>
    </div>
    <span class="text-xs text-slate-600 bg-slate-800 px-2.5 py-1 rounded-full shrink-0">
      {REFERENCE.venue}
    </span>
  </div>
  <p class="text-slate-400 text-sm leading-relaxed">{REFERENCE.summary}</p>
</a>

<!-- Concept mapping -->
<h4 class="text-base font-semibold text-slate-300 mb-4">
  Key Concepts → Manifestation in This Harness
</h4>

<div class="overflow-x-auto">
  <table class="w-full text-sm border-collapse">
    <thead>
      <tr class="border-b border-slate-800 text-left">
        <th class="py-3 pr-4 text-slate-500 font-medium w-1/5">Concept</th>
        <th class="py-3 pr-4 text-slate-500 font-medium">Talk Insight</th>
        <th class="py-3 text-slate-500 font-medium">In This Project</th>
      </tr>
    </thead>
    <tbody>
      {#each REFERENCE.concepts as row}
        <tr class="border-b border-slate-800/50">
          <td class="py-3 pr-4 text-indigo-400 font-medium align-top">{row.concept}</td>
          <td class="py-3 pr-4 text-slate-400 align-top">{row.insight}</td>
          <td class="py-3 text-slate-500 align-top">{row.manifestation}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
