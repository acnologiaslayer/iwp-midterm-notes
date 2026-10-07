# IWP Midterm Notes

Study notes for Internet and Web Programming (CSE 4051), Institute of
Information Technology, University of Dhaka.

**Live site:** https://acnologiaslayer.github.io/iwp-midterm-notes/

Covers HTML, forms, CSS selectors, the box model, flexbox, positioning,
CSS Grid, JavaScript functions, DOM manipulation, events, drag and drop,
classes, and asynchronous JavaScript with fetch and promises.

Each topic has the theory, a pointer to where it was used in coursework,
and a list of probable exam questions with answers.

## Contents of this repo

| File | What it is |
|---|---|
| `index.html` | The interactive notes site |
| `midterm-notes.md` | Source notes in markdown |
| `IWP-Midterm-Notes.pdf` | Printable version, 36 pages |
| `build.py` | Regenerates `index.html` from the markdown |

## Features of the site

- Full-text search across all sections, with match highlighting (press `/`)
- Collapsible sections, and an expand/collapse-all control
- A flashcard quiz with 80 cards generated from the question lists
- Light and dark themes, remembered between visits
- Reading progress indicator
- Copy buttons on every code block
- Responsive down to phone width, and a print stylesheet

## Rebuilding

```
pip install markdown
python3 build.py
```

Edit `midterm-notes.md` and re-run to regenerate the site.

---

Md. Mahir Musleh
