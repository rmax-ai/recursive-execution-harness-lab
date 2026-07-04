import adapter from "@sveltejs/adapter-static";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    adapter: adapter({
      pages: "../docs",
      assets: "../docs",
      fallback: undefined,
      precompress: false,
    }),
    paths: {
      base: "/recursive-execution-harness-lab",
    },
  },
};

export default config;
