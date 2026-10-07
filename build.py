#!/usr/bin/env python3
"""Build the interactive notes site from midterm-notes.md.

Produces notes-site/index.html: a single self-contained page with search,
a sidebar, collapsible sections, a flashcard quiz built from the
"Probable questions" lists, and light/dark themes.
"""

import json
import os
import re

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "midterm-notes.md")
OUT = os.path.join(ROOT, "index.html")

md_text = open(SRC, encoding="utf-8").read()

# ---------------------------------------------------------------- split sections
# Each "## N. Title" starts a section. Everything before the first one is intro.
parts = re.split(r"^## ", md_text, flags=re.MULTILINE)
intro_raw = parts[0]
# The markdown file has its own "## Contents" list; the sidebar replaces it.
section_raws = [p for p in parts[1:] if not p.lower().startswith("contents")]

md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list"])


def slugify(text):
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s


def render(text):
    md.reset()
    return md.convert(text)


sections = []
quiz = []

for raw in section_raws:
    lines = raw.split("\n")
    heading = lines[0].strip()
    body = "\n".join(lines[1:])

    num_match = re.match(r"^(\d+)\.\s*(.*)$", heading)
    if num_match:
        number, title = num_match.group(1), num_match.group(2)
    else:
        number, title = "", heading

    slug = slugify(heading)

    def clean(t):
        t = re.sub(r"\s+", " ", t).strip()
        return re.sub(r"[`*_]", "", t)

    def add_card(question, answer):
        q = clean(question)
        raw = answer.strip()

        # A table or code block does not survive being flattened into one
        # line, so send the reader to the section instead of showing mush.
        if raw.startswith("|") or raw.startswith("```") or raw.startswith("css") \
           or raw.startswith("js") or raw.startswith("html"):
            a = "Worked answer with a table or code block: open section "  + (number or "") + ", " + title + "."
        else:
            a = clean(answer) or "See the section notes."

        if len(q) > 3 and not any(c["q"] == q for c in quiz):
            quiz.append({"q": q, "a": a, "topic": title, "slug": slug})

    # Format 1: "### Probable questions" bullets, "- *Question?* Answer."
    q_match = re.search(
        r"### Probable questions\s*\n(.*?)(?=\n###|\Z)", body, re.DOTALL
    )
    if q_match:
        for m in re.finditer(r"^-\s+(.*?)$", q_match.group(1), re.MULTILINE):
            qm = re.match(r"\*(.+?)\*\s*(.*)$", m.group(1).strip())
            if qm:
                add_card(qm.group(1), qm.group(2))

    # Format 2: past-paper style, "**Q. Question?**" then the answer below,
    # continuing until a blank line followed by something that is not prose.
    for m in re.finditer(
        r"^\*\*Q\.\s*(.+?)\*\*\s*\n(.*?)(?=\n\s*\n|\n```|\Z)",
        body,
        re.DOTALL | re.MULTILINE,
    ):
        add_card(m.group(1), m.group(2))

    # Worked exam answers (### Q1 ... ### Q6) are deliberately NOT turned into
    # flashcards: each is a multi-part answer with tables and code, which does
    # not compress into a single card. Read them in full in section 16.

    sections.append(
        {
            "number": number,
            "title": title,
            "slug": slug,
            "html": render(body),
            "text": re.sub(r"\s+", " ", re.sub(r"[#`*|>-]", " ", body)).strip(),
        }
    )

intro_html = render(re.sub(r"^# .*$", "", intro_raw, count=1, flags=re.MULTILINE))

# Drop the generated table of contents: the sidebar replaces it.
intro_html = re.sub(
    r"<h2[^>]*>Contents</h2>.*?</ol>", "", intro_html, flags=re.DOTALL
)
intro_html = re.sub(r"<hr\s*/?>", "", intro_html)

# ---------------------------------------------------------------- page assembly
nav_items = "\n".join(
    '        <li><a href="#{slug}" data-nav="{slug}">'
    '<span class="nav-num">{num}</span>{title}</a></li>'.format(
        slug=s["slug"], num=s["number"] or "&bull;", title=s["title"]
    )
    for s in sections
)

section_blocks = "\n".join(
    """
      <section class="section" id="{slug}" data-title="{title_attr}">
        <h2 class="section-head">
          <button type="button" class="collapse-btn" aria-expanded="true"
                  aria-controls="body-{slug}">
            <span class="chev" aria-hidden="true">&#9662;</span>
            <span class="sec-num">{num}</span>
            <span class="sec-title">{title}</span>
          </button>
          <a class="anchor" href="#{slug}" aria-label="Link to this section">#</a>
        </h2>
        <div class="section-body" id="body-{slug}">
{html}
        </div>
      </section>""".format(
        slug=s["slug"],
        num=s["number"],
        title=s["title"],
        title_attr=s["title"].replace('"', "&quot;"),
        html=s["html"],
    )
    for s in sections
)

search_index = json.dumps(
    [
        {"slug": s["slug"], "title": s["title"], "num": s["number"], "text": s["text"][:6000]}
        for s in sections
    ]
)

quiz_json = json.dumps(quiz)

HTML = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IWP Midterm Notes &mdash; Md. Mahir Musleh</title>
<meta name="description" content="Interactive study notes for Internet and Web Programming, built from twelve coursework assignments.">
<meta name="author" content="Md. Mahir Musleh">
<style>
:root {
  --navy: #14293f;
  --navy-2: #1d3b59;
  --accent: #2f9e6f;
  --accent-dark: #24805a;
  --amber: #b7791f;
  --danger: #b32d20;

  --panel: #ffffff;
  --line: #e2e8f0;
  --ink: #1f2933;
  --ink-soft: #5a6672;
  --bg: #f4f6f9;
  --code-bg: #eef2f7;
  --mark: #fde68a;

  --sidebar: 280px;
  --speed: 0.2s;
}

html[data-theme="dark"] {
  --navy: #e8eef5;
  --navy-2: #cbd8e6;
  --accent: #46b588;
  --accent-dark: #6fd3a8;

  --panel: #16202b;
  --line: #2a3847;
  --ink: #e4e9ef;
  --ink-soft: #9aa7b5;
  --bg: #0f1720;
  --code-bg: #1d2935;
  --mark: #7a5c12;
}

* { box-sizing: border-box; }

html { scroll-behavior: smooth; scroll-padding-top: 80px; }

body {
  background: var(--bg);
  color: var(--ink);
  font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.7;
  margin: 0;
  transition: background var(--speed), color var(--speed);
}

/* ---------- top bar ---------- */

.topbar {
  align-items: center;
  background: var(--navy);
  display: flex;
  gap: 14px;
  padding: 10px 18px;
  position: sticky;
  top: 0;
  z-index: 50;
}

html[data-theme="dark"] .topbar { background: #0b1118; border-bottom: 1px solid var(--line); }

.brand {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  margin-right: auto;
  white-space: nowrap;
}

html[data-theme="dark"] .brand { color: var(--ink); }

.brand small {
  color: #9fb3c8;
  display: block;
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 1px;
  text-transform: uppercase;
}

#search {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.22);
  border-radius: 8px;
  color: #fff;
  font-family: inherit;
  font-size: 14px;
  max-width: 340px;
  padding: 9px 13px;
  width: 100%;
  transition: background var(--speed), border-color var(--speed);
}

#search::placeholder { color: rgba(255,255,255,0.65); }

#search:focus {
  background: rgba(255,255,255,0.2);
  border-color: var(--accent);
  outline: none;
}

.icon-btn {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.22);
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  padding: 8px 13px;
  transition: background var(--speed);
  white-space: nowrap;
}

.icon-btn:hover { background: rgba(255,255,255,0.26); }

a.icon-btn { text-decoration: none; }

#menu-btn { display: none; }

/* ---------- layout ---------- */

.shell {
  display: grid;
  grid-template-columns: var(--sidebar) minmax(0, 1fr);
  margin: 0 auto;
  max-width: 1500px;
}

/* ---------- sidebar ---------- */

.sidebar {
  align-self: start;
  border-right: 1px solid var(--line);
  max-height: calc(100vh - 56px);
  overflow-y: auto;
  padding: 22px 14px 40px;
  position: sticky;
  top: 56px;
}

.side-title {
  color: var(--ink-soft);
  font-size: 11px;
  letter-spacing: 1.4px;
  margin: 0 0 10px 10px;
  text-transform: uppercase;
}

.sidebar ol { list-style: none; margin: 0; padding: 0; }

.sidebar a {
  align-items: baseline;
  border-radius: 7px;
  color: var(--ink-soft);
  display: flex;
  font-size: 14px;
  gap: 9px;
  padding: 7px 10px;
  text-decoration: none;
  transition: background var(--speed), color var(--speed);
}

.sidebar a:hover { background: var(--code-bg); color: var(--ink); }

.sidebar a.active {
  background: var(--code-bg);
  color: var(--accent-dark);
  font-weight: 600;
}

.nav-num {
  color: var(--accent);
  flex: 0 0 18px;
  font-size: 12px;
  font-weight: 700;
}

.progress-wrap { margin: 0 10px 16px; }

.progress-bar {
  background: var(--line);
  border-radius: 999px;
  height: 5px;
  overflow: hidden;
}

#progress-fill {
  background: var(--accent);
  height: 100%;
  width: 0%;
  transition: width 0.1s linear;
}

.progress-label {
  color: var(--ink-soft);
  font-size: 11px;
  margin-top: 5px;
}

/* ---------- content ---------- */

.content { min-width: 0; padding: 26px 36px 80px; }

.page-title {
  color: var(--navy);
  font-size: 32px;
  margin: 0 0 6px;
}

.subtitle {
  color: var(--ink-soft);
  font-size: 14px;
  margin: 0 0 22px;
}

.section {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  margin-bottom: 18px;
  padding: 4px 26px 6px;
}

.section-head {
  align-items: center;
  display: flex;
  gap: 8px;
  margin: 0;
}

.collapse-btn {
  align-items: center;
  background: none;
  border: none;
  color: var(--navy);
  cursor: pointer;
  display: flex;
  flex: 1 1 auto;
  font-family: inherit;
  font-size: 21px;
  font-weight: 700;
  gap: 10px;
  padding: 16px 0;
  text-align: left;
}

.chev { color: var(--accent); font-size: 14px; transition: transform var(--speed); }
.collapse-btn[aria-expanded="false"] .chev { transform: rotate(-90deg); }

.sec-num {
  background: var(--accent);
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  min-width: 26px;
  padding: 1px 7px;
  text-align: center;
}

.anchor {
  color: var(--line);
  font-size: 18px;
  text-decoration: none;
}
.anchor:hover { color: var(--accent); }

.section-body { padding-bottom: 14px; }
.section-body[hidden] { display: none; }

.content h3 {
  border-bottom: 2px solid var(--accent);
  color: var(--navy);
  display: inline-block;
  font-size: 15px;
  letter-spacing: 0.8px;
  margin: 22px 0 10px;
  padding-bottom: 4px;
  text-transform: uppercase;
}

.content p { margin: 0 0 12px; }
.content ul, .content ol { margin: 0 0 14px; padding-left: 22px; }
.content li { margin-bottom: 5px; }
.content strong { color: var(--navy); }

.content blockquote {
  background: var(--code-bg);
  border-left: 4px solid var(--amber);
  border-radius: 0 8px 8px 0;
  margin: 14px 0;
  padding: 12px 16px;
}
.content blockquote p:last-child { margin-bottom: 0; }

code {
  background: var(--code-bg);
  border-radius: 4px;
  font-family: "Cascadia Code", Consolas, Monaco, monospace;
  font-size: 13px;
  padding: 2px 5px;
}

pre {
  background: var(--code-bg);
  border: 1px solid var(--line);
  border-radius: 9px;
  margin: 0 0 14px;
  overflow-x: auto;
  padding: 14px 16px;
  position: relative;
}

pre code { background: none; font-size: 13px; line-height: 1.6; padding: 0; }

.copy-btn {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  color: var(--ink-soft);
  cursor: pointer;
  font-family: inherit;
  font-size: 11px;
  opacity: 0;
  padding: 3px 9px;
  position: absolute;
  right: 8px;
  top: 8px;
  transition: opacity var(--speed);
}

pre:hover .copy-btn, .copy-btn:focus { opacity: 1; }
.copy-btn.done { border-color: var(--accent); color: var(--accent-dark); }

/* tables */

.content table {
  border-collapse: collapse;
  display: block;
  margin: 0 0 16px;
  overflow-x: auto;
  width: 100%;
}

.content th {
  background: var(--navy);
  color: #fff;
  font-size: 13px;
  letter-spacing: 0.4px;
  padding: 9px 13px;
  text-align: left;
}

html[data-theme="dark"] .content th { background: #223040; color: var(--ink); }

.content td {
  border-top: 1px solid var(--line);
  font-size: 14px;
  padding: 8px 13px;
  vertical-align: top;
}

.content tbody tr:nth-child(even) { background: var(--code-bg); }

/* search */

mark { background: var(--mark); border-radius: 3px; color: inherit; padding: 0 2px; }

.section.hidden { display: none; }

#no-results {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  color: var(--ink-soft);
  display: none;
  padding: 30px;
  text-align: center;
}

#search-note {
  color: var(--ink-soft);
  display: none;
  font-size: 13px;
  margin-bottom: 14px;
}

/* ---------- quiz ---------- */

.quiz-overlay {
  background: rgba(10, 18, 26, 0.72);
  display: none;
  inset: 0;
  padding: 20px;
  position: fixed;
  z-index: 100;
}

.quiz-overlay.open { align-items: center; display: flex; justify-content: center; }

.quiz-card {
  background: var(--panel);
  border-radius: 14px;
  max-width: 620px;
  padding: 26px 28px;
  width: 100%;
}

.quiz-top {
  align-items: center;
  color: var(--ink-soft);
  display: flex;
  font-size: 12px;
  justify-content: space-between;
  letter-spacing: 1px;
  margin-bottom: 14px;
  text-transform: uppercase;
}

.quiz-topic { color: var(--accent-dark); font-weight: 700; }

.quiz-q {
  color: var(--navy);
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 16px;
}

.quiz-a {
  background: var(--code-bg);
  border-left: 3px solid var(--accent);
  border-radius: 0 8px 8px 0;
  margin-bottom: 18px;
  padding: 13px 16px;
}

.quiz-a[hidden] { display: none; }

.quiz-actions { display: flex; flex-wrap: wrap; gap: 9px; }

.btn {
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 18px;
  transition: background var(--speed);
}

.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-dark); }

.btn-quiet {
  background: var(--code-bg);
  border-color: var(--line);
  color: var(--ink);
}
.btn-quiet:hover { background: var(--line); }

.btn-ghost { background: none; color: var(--ink-soft); margin-left: auto; }

/* ---------- print ---------- */

@media print {
  .topbar, .sidebar, .quiz-overlay, .copy-btn, .anchor, #search-note { display: none !important; }
  .shell { display: block; }
  .content { padding: 0; }
  .section { border: none; break-inside: avoid; margin-bottom: 10px; padding: 0; }
  .section-body[hidden] { display: block !important; }
  .chev { display: none; }
  body { background: #fff; }
  pre, .content table { break-inside: avoid; }
}

/* ---------- responsive ---------- */

@media (max-width: 1000px) {
  .shell { grid-template-columns: 1fr; }

  #menu-btn { display: block; }

  .sidebar {
    background: var(--panel);
    border-right: 1px solid var(--line);
    bottom: 0;
    left: 0;
    max-height: none;
    position: fixed;
    top: 56px;
    transform: translateX(-100%);
    transition: transform var(--speed);
    width: var(--sidebar);
    z-index: 40;
  }

  .sidebar.open { transform: none; }

  .content { padding: 20px 18px 70px; }
  .page-title { font-size: 25px; }
}

@media (max-width: 620px) {
  .brand small { display: none; }
  .section { padding: 2px 15px 4px; }
  .collapse-btn { font-size: 17px; }
  .quiz-card { padding: 20px 18px; }
  #quiz-btn span.full { display: none; }
}
</style>
</head>
<body>

<header class="topbar">
  <button type="button" class="icon-btn" id="menu-btn" aria-label="Toggle contents">&#9776;</button>
  <div class="brand">IWP Midterm Notes<small>Md. Mahir Musleh &middot; IIT, DU</small></div>
  <input type="search" id="search" placeholder="Search notes&hellip;  (press /)" autocomplete="off" aria-label="Search notes">
  <button type="button" class="icon-btn" id="quiz-btn">&#9733; <span class="full">Quiz</span></button>
  <button type="button" class="icon-btn" id="expand-btn" title="Expand or collapse all">&#8597;</button>
  <a class="icon-btn" href="IWP-Midterm-Notes.pdf" download title="Download the PDF">&#8681; <span class="full">PDF</span></a>
  <button type="button" class="icon-btn" id="theme-btn" title="Toggle theme">&#9680;</button>
</header>

<div class="shell">

  <nav class="sidebar" id="sidebar">
    <div class="progress-wrap">
      <div class="progress-bar"><div id="progress-fill"></div></div>
      <div class="progress-label"><span id="progress-pct">0</span>% read</div>
    </div>
    <p class="side-title">Contents</p>
    <ol>
__NAV__
    </ol>
  </nav>

  <main class="content">
    <h1 class="page-title">Internet &amp; Web Programming</h1>
    <p class="subtitle">Midterm study notes, built from Assignments 01&ndash;12.</p>

    <div id="intro">__INTRO__</div>

    <p id="search-note"></p>

    <div id="sections">
__SECTIONS__
    </div>

    <div id="no-results">
      <strong>No matches.</strong><br>Try another word, or clear the search box.
    </div>
  </main>

</div>

<div class="quiz-overlay" id="quiz" role="dialog" aria-modal="true" aria-label="Flashcard quiz">
  <div class="quiz-card">
    <div class="quiz-top">
      <span class="quiz-topic" id="quiz-topic"></span>
      <span><span id="quiz-i">1</span> / <span id="quiz-n">0</span></span>
    </div>
    <p class="quiz-q" id="quiz-q"></p>
    <div class="quiz-a" id="quiz-a" hidden></div>
    <div class="quiz-actions">
      <button type="button" class="btn btn-primary" id="reveal-btn">Show answer</button>
      <button type="button" class="btn btn-quiet" id="next-btn">Next &rarr;</button>
      <button type="button" class="btn btn-quiet" id="shuffle-btn">Shuffle</button>
      <button type="button" class="btn btn-ghost" id="close-quiz">Close</button>
    </div>
  </div>
</div>

<script>
'use strict';

var INDEX = __INDEX__;
var QUIZ  = __QUIZ__;

/* ---------- theme ---------- */

var root = document.documentElement;
var saved = null;
try { saved = localStorage.getItem('iwp-notes-theme'); } catch (e) {}
if (saved) { root.setAttribute('data-theme', saved); }

document.getElementById('theme-btn').addEventListener('click', function () {
  var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
  try { localStorage.setItem('iwp-notes-theme', next); } catch (e) {}
});

/* ---------- sidebar (small screens) ---------- */

var sidebar = document.getElementById('sidebar');

document.getElementById('menu-btn').addEventListener('click', function () {
  sidebar.classList.toggle('open');
});

sidebar.addEventListener('click', function (e) {
  if (e.target.closest('a') && window.innerWidth <= 1000) {
    sidebar.classList.remove('open');
  }
});

/* ---------- collapse ---------- */

document.addEventListener('click', function (e) {
  var btn = e.target.closest('.collapse-btn');
  if (!btn) { return; }
  var open = btn.getAttribute('aria-expanded') === 'true';
  btn.setAttribute('aria-expanded', String(!open));
  document.getElementById(btn.getAttribute('aria-controls')).hidden = open;
});

var allOpen = true;
document.getElementById('expand-btn').addEventListener('click', function () {
  allOpen = !allOpen;
  document.querySelectorAll('.collapse-btn').forEach(function (btn) {
    btn.setAttribute('aria-expanded', String(allOpen));
    document.getElementById(btn.getAttribute('aria-controls')).hidden = !allOpen;
  });
});

/* ---------- copy buttons on code blocks ---------- */

document.querySelectorAll('pre').forEach(function (pre) {
  var b = document.createElement('button');
  b.type = 'button';
  b.className = 'copy-btn';
  b.textContent = 'Copy';
  b.addEventListener('click', function () {
    var code = pre.querySelector('code');
    var text = code ? code.textContent : pre.textContent;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () {
        b.textContent = 'Copied';
        b.classList.add('done');
        setTimeout(function () { b.textContent = 'Copy'; b.classList.remove('done'); }, 1400);
      });
    }
  });
  pre.appendChild(b);
});

/* ---------- search ---------- */

var searchBox = document.getElementById('search');
var noResults = document.getElementById('no-results');
var note = document.getElementById('search-note');
var intro = document.getElementById('intro');

function clearMarks(el) {
  el.querySelectorAll('mark').forEach(function (m) {
    m.replaceWith(document.createTextNode(m.textContent));
  });
  el.normalize();
}

function highlight(el, term) {
  var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
    acceptNode: function (n) {
      if (!n.nodeValue.trim()) { return NodeFilter.FILTER_REJECT; }
      if (n.parentNode.closest('mark, script, style')) { return NodeFilter.FILTER_REJECT; }
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  var targets = [];
  var node;
  while ((node = walker.nextNode())) {
    if (node.nodeValue.toLowerCase().indexOf(term) !== -1) { targets.push(node); }
  }
  targets.forEach(function (n) {
    var frag = document.createDocumentFragment();
    var rest = n.nodeValue;
    var idx;
    while ((idx = rest.toLowerCase().indexOf(term)) !== -1) {
      frag.appendChild(document.createTextNode(rest.slice(0, idx)));
      var mk = document.createElement('mark');
      mk.textContent = rest.substr(idx, term.length);
      frag.appendChild(mk);
      rest = rest.slice(idx + term.length);
    }
    frag.appendChild(document.createTextNode(rest));
    n.parentNode.replaceChild(frag, n);
  });
}

var searchTimer;

searchBox.addEventListener('input', function () {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(runSearch, 140);
});

function runSearch() {
  var term = searchBox.value.trim().toLowerCase();
  var sections = document.querySelectorAll('.section');

  sections.forEach(function (s) { clearMarks(s); });

  if (term.length < 2) {
    sections.forEach(function (s) { s.classList.remove('hidden'); });
    noResults.style.display = 'none';
    note.style.display = 'none';
    intro.style.display = '';
    return;
  }

  intro.style.display = 'none';
  var hits = 0;

  sections.forEach(function (s) {
    var hay = (s.dataset.title + ' ' + s.textContent).toLowerCase();
    var match = hay.indexOf(term) !== -1;
    s.classList.toggle('hidden', !match);
    if (match) {
      hits++;
      /* make sure a matching section is open so the hit is visible */
      var btn = s.querySelector('.collapse-btn');
      btn.setAttribute('aria-expanded', 'true');
      document.getElementById(btn.getAttribute('aria-controls')).hidden = false;
      highlight(s.querySelector('.section-body'), term);
      highlight(s.querySelector('.sec-title'), term);
    }
  });

  noResults.style.display = hits ? 'none' : 'block';
  note.style.display = 'block';
  note.textContent = hits
    ? hits + ' section' + (hits === 1 ? '' : 's') + ' matching "' + searchBox.value.trim() + '"'
    : '';
}

/* keyboard: "/" focuses search, Escape clears it */
document.addEventListener('keydown', function (e) {
  if (e.key === '/' && document.activeElement !== searchBox) {
    e.preventDefault();
    searchBox.focus();
  } else if (e.key === 'Escape') {
    if (document.getElementById('quiz').classList.contains('open')) {
      closeQuiz();
    } else if (document.activeElement === searchBox) {
      searchBox.value = '';
      runSearch();
      searchBox.blur();
    }
  }
});

/* ---------- active section + reading progress ---------- */

var navLinks = {};
document.querySelectorAll('[data-nav]').forEach(function (a) {
  navLinks[a.dataset.nav] = a;
});

var fill = document.getElementById('progress-fill');
var pct = document.getElementById('progress-pct');

function onScroll() {
  var doc = document.documentElement;
  var max = doc.scrollHeight - doc.clientHeight;
  var p = max > 0 ? Math.min(100, Math.round((doc.scrollTop / max) * 100)) : 0;
  fill.style.width = p + '%';
  pct.textContent = p;

  var current = null;
  document.querySelectorAll('.section').forEach(function (s) {
    if (s.classList.contains('hidden')) { return; }
    if (s.getBoundingClientRect().top <= 120) { current = s.id; }
  });

  Object.keys(navLinks).forEach(function (k) {
    navLinks[k].classList.toggle('active', k === current);
  });
}

window.addEventListener('scroll', onScroll, { passive: true });
window.addEventListener('resize', onScroll);
onScroll();

/* ---------- flashcard quiz ---------- */

var overlay = document.getElementById('quiz');
var order = QUIZ.map(function (_, i) { return i; });
var pos = 0;

function shuffle() {
  for (var i = order.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = order[i]; order[i] = order[j]; order[j] = t;
  }
  pos = 0;
  showCard();
}

function showCard() {
  if (!QUIZ.length) { return; }
  var card = QUIZ[order[pos]];
  document.getElementById('quiz-topic').textContent = card.topic;
  document.getElementById('quiz-q').textContent = card.q;
  var a = document.getElementById('quiz-a');
  a.textContent = card.a;
  a.hidden = true;
  document.getElementById('reveal-btn').textContent = 'Show answer';
  document.getElementById('quiz-i').textContent = pos + 1;
  document.getElementById('quiz-n').textContent = QUIZ.length;
}

function openQuiz() {
  overlay.classList.add('open');
  showCard();
}

function closeQuiz() { overlay.classList.remove('open'); }

document.getElementById('quiz-btn').addEventListener('click', openQuiz);
document.getElementById('close-quiz').addEventListener('click', closeQuiz);
document.getElementById('shuffle-btn').addEventListener('click', shuffle);

document.getElementById('reveal-btn').addEventListener('click', function () {
  var a = document.getElementById('quiz-a');
  a.hidden = !a.hidden;
  this.textContent = a.hidden ? 'Show answer' : 'Hide answer';
});

document.getElementById('next-btn').addEventListener('click', function () {
  pos = (pos + 1) % QUIZ.length;
  showCard();
});

overlay.addEventListener('click', function (e) {
  if (e.target === overlay) { closeQuiz(); }
});

shuffle();
</script>
</body>
</html>
"""

page = (
    HTML.replace("__NAV__", nav_items)
    .replace("__INTRO__", intro_html)
    .replace("__SECTIONS__", section_blocks)
    .replace("__INDEX__", search_index)
    .replace("__QUIZ__", quiz_json)
)

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(page)

print("sections:", len(sections))
print("quiz cards:", len(quiz))
print("bytes:", len(page))
