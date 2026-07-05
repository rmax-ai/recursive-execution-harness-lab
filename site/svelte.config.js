import adapter from "@sveltejs/adapter-static";

/** @type {import('@sveltejs/kit').Config} */
const base = process.env.SITE_BASE_PATH ?? "";

const config = {
  kit: {
    adapter: adapter({
      pages: "../docs",
      assets: "../docs",
      fallback: undefined,
      precompress: false,
    }),
    paths: {
      base,
      assets: base,
    },
  },
};

export default config;
