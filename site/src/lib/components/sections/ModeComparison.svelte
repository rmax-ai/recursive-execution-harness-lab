<script lang="ts">
  import Card from "$lib/components/ui/Card.svelte";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">Execution Modes Compared</h3>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
  <Card title="Mode A: Long-Context">
    <p>Concatenate all documents → one giant prompt → model answers.</p>
    {#snippet footer()}
      Simple, common, but degrades with scale. Risk: attention dilution, lost-in-the-middle, no provenance.
    {/snippet}
  </Card>

  <Card title="Mode B: Recursive">
    <p>Ingest → planner → bounded workers → evidence cards → synthesizer → verifier → policy gate → final answer with provenance trace.</p>
    {#snippet footer()}
      More calls. More inspectable. Every claim linked to a source.
    {/snippet}
  </Card>
</div>
