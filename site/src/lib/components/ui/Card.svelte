<script lang="ts">
  interface Props {
    title: string;
    children?: import("svelte").Snippet;
    footer?: import("svelte").Snippet;
  }

  let { title, children, footer }: Props = $props();
</script>

<div class="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
  <h4 class="text-indigo-400 font-mono text-xs uppercase tracking-wider mb-4">{title}</h4>
  <div class="text-slate-300 text-sm leading-relaxed">
    {@render children?.()}
  </div>
  {#if footer}
    <div class="mt-4 pt-4 border-t border-slate-800 text-slate-500 text-xs">
      {@render footer()}
    </div>
  {/if}
</div>
