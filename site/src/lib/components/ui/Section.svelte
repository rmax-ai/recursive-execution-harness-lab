<script lang="ts">
  interface Props {
    tag?: string;
    children?: import("svelte").Snippet;
  }

  let { tag = "section", children }: Props = $props();
</script>

<svelte:element this={tag} class="py-16 px-4 sm:px-6 max-w-4xl mx-auto">
  {@render children?.()}
</svelte:element>
