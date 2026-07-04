<script lang="ts">
  import Badge from "$lib/components/ui/Badge.svelte";
  import { PROJECT_VERSION, TEST_COUNT, LICENSE, REPO_URL, DOCS_URL } from "$lib/data/meta";
</script>

<header class="py-16 px-4 sm:px-6 max-w-4xl mx-auto">
  <div class="flex flex-wrap gap-2 mb-4">
    <Badge text={PROJECT_VERSION} />
    <Badge text="{TEST_COUNT} tests" />
    <Badge text={LICENSE} />
  </div>

  <h1 class="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-3">
    Recursive Execution Harness Lab
  </h1>

  <p class="text-slate-400 text-lg max-w-2xl mb-6">
    A CLI-first Python research instrument that compares two agent architectures
    on multi-document synthesis tasks.
  </p>

  <div class="flex gap-3 font-mono text-sm">
    <a href={REPO_URL} class="inline-block px-4 py-2 bg-slate-900 border border-slate-800 rounded-md text-slate-300 hover:border-slate-600 transition-colors">
      GitHub Repository
    </a>
    <a href={DOCS_URL} class="inline-block px-4 py-2 bg-slate-900 border border-slate-800 rounded-md text-slate-300 hover:border-slate-600 transition-colors">
      Architecture Docs
    </a>
  </div>
</header>
