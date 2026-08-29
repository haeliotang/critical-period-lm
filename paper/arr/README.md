# ARR submission build

The paper in ACL format, anonymized for review. `paper/draft.md` stays the working
document; this directory is the typeset version of it and nothing here is a source
of truth for any number.

```bash
make paper          # from the repository root
```

or `latexmk -pdf main.tex` here. Produces `main.pdf` — currently **6 pages**,
against an 8-page limit for a long paper. Limitations and references do not count
against that limit.

## Layout

| | |
| --- | --- |
| `main.tex` | the paper |
| `custom.bib` | 7 references, each checked against its arXiv or ACL Anthology record |
| `acl.sty`, `acl_natbib.bst` | official style files, unmodified, from `acl-org/acl-style-files` |
| `acl_latex.tex` | the upstream template, kept for reference; not built |
| `main.pdf` | committed, because it is what a reviewer reads |

The figure is not duplicated here. `main.tex` includes `../figures/decay-v5.pdf`,
which `make figure` regenerates from the run records, so the typeset paper cannot
drift from the registered results.

## Before submitting

1. **Create the anonymous repository mirror** and replace `ANONYMIZED` in the
   footnote in Section 7. As it stands that URL is a placeholder and resolves to
   nothing.
2. **Check the mirror does not deanonymize.** The git history, tag annotations and
   commit authorship all carry a real name even when the file contents do not.
   Mirror the working tree, not the history.
3. **Register as a reviewer with ARR.** Every author must, and non-registration is
   a desk reject. The exemption for insufficient reviewing experience covers being
   assigned reviews; it does not cover skipping the registration itself.
4. Complete the Responsible NLP checklist.

## Anonymity as it stands

Audited: PDF `/Author` and `/Title` are empty, the figure carries only matplotlib's
own producer strings and no filesystem paths, and neither `main.tex` nor
`custom.bib` contains a name, handle, institution or repository URL. The only
identifying thing left is the placeholder above, which is currently inert.

## For camera-ready

Change `\usepackage[review]{acl}` to `\usepackage[final]{acl}`, add the author
block, and replace the anonymous URL with the real one. `[preprint]` gives a
non-anonymous version with page numbers, which is the right option for arXiv.
