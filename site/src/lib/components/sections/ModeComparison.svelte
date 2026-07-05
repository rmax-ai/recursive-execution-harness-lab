<script lang="ts">
  import Card from "$lib/components/ui/Card.svelte";
</script>

<h3 class="text-xl font-semibold text-white border-b border-slate-800 pb-3 mb-8">Execution Modes Compared</h3>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
  <Card title="Mode A: Long-Context">
    <p>Concatenate all documents → one giant prompt → model answers → verifier checks the answer → revise once if needed → deterministic policy decides allow, revise, or deny.</p>
    {#snippet footer()}
      Simple, common, but degrades with scale. Risk: attention dilution, lost-in-the-middle, and no intermediate evidence artifacts before verification.
    {/snippet}
  </Card>

  <Card title="Mode B: Recursive">
    <p>Ingest → planner → bounded source slices → evidence cards → synthesizer → verifier → optional revision → deterministic policy gate → final answer with provenance trace.</p>
    {#snippet footer()}
      More calls. More inspectable. Workers operate on bounded source slices, invalid provenance is rejected, and the delivered answer passes verification before policy.
    {/snippet}
  </Card>
</div>
