<script lang="ts">
  import Card from "$lib/components/ui/Card.svelte";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">Execution Modes Compared</h3>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
  <Card title="Mode A: Long-Context">
    <p>Concatenate all documents → one giant prompt → model answers → verifier checks the final answer.</p>
    {#snippet footer()}
      Simple, common, but degrades with scale. Risk: attention dilution, lost-in-the-middle, and no intermediate evidence artifacts.
    {/snippet}
  </Card>

  <Card title="Mode B: Recursive">
    <p>Ingest → planner → bounded workers → evidence cards → synthesizer → verifier → final answer with provenance trace.</p>
    {#snippet footer()}
      More calls. More inspectable. Verifier sees evidence cards, source-ref mappings, and document-backed source snippets.
    {/snippet}
  </Card>
</div>
