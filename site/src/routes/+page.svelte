<script lang="ts">
  import Section from "$lib/components/ui/Section.svelte";
  import Header from "$lib/components/sections/Header.svelte";
  import Hero from "$lib/components/sections/Hero.svelte";
  import ModeComparison from "$lib/components/sections/ModeComparison.svelte";
  import Pipeline from "$lib/components/sections/Pipeline.svelte";
  import Quickstart from "$lib/components/sections/Quickstart.svelte";
  import Metrics from "$lib/components/sections/Metrics.svelte";
  import Validity from "$lib/components/sections/Validity.svelte";
  import Contribution from "$lib/components/sections/Contribution.svelte";
  import Inspiration from "$lib/components/sections/Inspiration.svelte";
  import Footer from "$lib/components/sections/Footer.svelte";
</script>

<Header />

<Section>
  <Hero />
</Section>

<Section>
  <ModeComparison />
</Section>

<Section>
  <Pipeline />
</Section>

<Section>
  <Quickstart />
</Section>

<Section>
  <Metrics />
</Section>

<Section>
  <Validity />
</Section>

<Section>
  <Contribution />
</Section>

<Section>
  <Inspiration />
</Section>

<Footer />
