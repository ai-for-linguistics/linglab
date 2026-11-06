# Third-party software

- **KaTeX** 0.16.11 (MIT, Khan Academy and contributors): renders LaTeX notation in the report, offline.
  Vendored in `template/report/vendor/katex/` (`katex.min.js`, `katex.min.css`, a subset of the woff2 fonts, `LICENSE`).
  `linglab report` inlines it (fonts as base64) into `report/index.html` only when the project has some notation.
  Source: https://github.com/KaTeX/KaTeX
