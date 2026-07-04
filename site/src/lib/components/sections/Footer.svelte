<script lang="ts">
  import { LICENSE, PROJECT_VERSION, REPO_URL } from "$lib/data/meta";
</script>

<footer class="border-t border-slate-800 mt-24 py-8 text-center font-mono text-sm text-slate-600">
  <p>
    {LICENSE} License · {PROJECT_VERSION} ·
    <a href={REPO_URL} class="text-indigo-400 hover:text-indigo-300 transition-colors">rmax-ai/recursive-execution-harness-lab</a>
  </p>
</footer>
