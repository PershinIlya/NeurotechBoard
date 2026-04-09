// Observable Framework config — NeurotechBoard dashboard.
// Single-page layout, no sidebar nav, dashboard theme.
//
// https://observablehq.com/framework/config
export default {
  title: "NeurotechBoard",
  root: "src",
  pages: [],
  toc: false,
  sidebar: false,
  pager: false,
  theme: ["cotton", "wide"],
  head: `<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E🧠%3C/text%3E%3C/svg%3E">`,
  header: "",
  footer: `
    <div>
      Built with <a href="https://observablehq.com/framework" target="_blank">Observable Framework</a>
      • Open data, open methodology
      • <a href="https://github.com/PershinIlya/NeurotechBoard" target="_blank">Source on GitHub</a>
    </div>
  `,
  // Base path for GitHub Pages subdirectory deployment:
  // https://pershinilya.github.io/NeurotechBoard/
  base: "/NeurotechBoard/",
  preserveExtension: false,
  preserveIndex: false,
};
