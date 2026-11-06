#!/usr/bin/env python3
"""Assemble un roman (chapitres .md dans romans/src/<slug>/) en une page HTML.

Syntaxe des chapitres :
  # Titre du chapitre        (1re ligne)
  > Épigraphe                (2e ligne, facultative)
  [[texte|référence]]        terme juridique avec info-bulle
  **gras**  *italique*       ***  = changement de scène
  ::: retenir  … :::         encadré « Ce que tu viens d'apprendre »
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONF = json.loads((ROOT / "romans" / "romans.json").read_text(encoding="utf-8"))


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[\[(.+?)\|(.+?)\]\]",
               lambda m: f'<span class="k" tabindex="0" data-r="{html.escape(m.group(2), quote=True)}">{m.group(1)}</span>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def chapter(path, idx):
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    title = lines.pop(0).lstrip("# ").strip()
    epi = ""
    if lines and lines[0].startswith(">"):
        epi = lines.pop(0)[1:].strip()
    out, para, box = [], [], None

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    for ln in lines:
        t = ln.strip()
        if box is not None:
            if t == ":::":
                out.append('<aside class="retenir"><h4>Ce que tu viens d\'apprendre</h4><ul>' +
                           "".join(f"<li>{inline(x)}</li>" for x in box) + "</ul></aside>")
                box = None
            elif t.startswith("- "):
                box.append(t[2:])
            continue
        if t.startswith("::: retenir"):
            flush(); box = []
        elif t == "***":
            flush(); out.append('<div class="scene">❦</div>')
        elif not t:
            flush()
        else:
            para.append(t)
    flush()
    num = "Épilogue" if title.lower().startswith("épilogue") else f"Chapitre {idx}"
    short = re.sub(r"^(Chapitre \d+|Épilogue)\s*[—-]\s*", "", title)
    epi_html = f'<blockquote class="epi">{inline(epi)}</blockquote>' if epi else ""
    body = (f'<section class="chap" id="ch{idx}"><header><div class="num">{num}</div>'
            f'<h2>{html.escape(short)}</h2>{epi_html}</header>' + "\n".join(out) + "</section>")
    return num, short, body


def build(slug):
    c = CONF[slug]
    files = sorted((ROOT / "romans" / "src" / slug).glob("*.md"))
    chaps = [chapter(f, i + 1) for i, f in enumerate(files)]
    words = sum(len(re.sub(r"<[^>]+>", " ", b).split()) for _, _, b in chaps)
    toc = "".join(f'<li><a href="#ch{i+1}"><span>{n}</span>{html.escape(s)}</a></li>' for i, (n, s, _) in enumerate(chaps))
    cast = "".join(f"<li><b>{html.escape(n)}</b><span>{html.escape(d)}</span></li>" for n, d in c["cast"])
    tpl = (ROOT / "romans" / "roman_tpl.html").read_text(encoding="utf-8")
    page = (tpl.replace("__TITLE__", html.escape(c["title"]))
               .replace("__COURSE__", html.escape(c["course"]))
               .replace("__PITCH__", html.escape(c["pitch"]))
               .replace("__C__", c["c"]).replace("__SOFT__", c["soft"]).replace("__DEEP__", c["deep"])
               .replace("__SLUG__", slug)
               .replace("__MINUTES__", str(round(words / 230)))
               .replace("__NCH__", str(len(chaps)))
               .replace("__TOC__", toc).replace("__CAST__", cast)
               .replace("__BODY__", "\n".join(b for _, _, b in chaps)))
    (ROOT / "romans" / f"{slug}.html").write_text(page, encoding="utf-8")
    print("ok", slug, len(chaps), "chapitres", words, "mots")


if __name__ == "__main__":
    for s in (sys.argv[1:] or CONF.keys()):
        build(s)
