#!/usr/bin/env python3
"""Assemble une fiche (fragment HTML) dans le gabarit, puis génère le PDF."""
import sys, pathlib, asyncio
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
TEMPLATE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Fiche de révision</title>
<link rel="stylesheet" href="../assets/fiche.css">
</head>
<body class="fiche c-{slug}">
<a class="no-print backlink" href="../index.html" style="position:fixed;left:16px;top:16px;z-index:10;background:#fff;border:1px solid #e6e3dd;border-radius:99px;padding:6px 14px;font:600 13px InterV,sans-serif;color:#1b1b1f;text-decoration:none;box-shadow:0 4px 14px rgba(0,0,0,.06)">← Tous les cours</a>
<main>
{body}
</main>
</body></html>"""

async def pdf(html_path, pdf_path, title):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto(html_path.resolve().as_uri())
        await pg.wait_for_timeout(400)
        footer = ('<div style="width:100%;font:7.5pt Inter,sans-serif;color:#8a8d93;padding:0 14mm;'
                  'display:flex;justify-content:space-between"><span>' + title +
                  '</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
        await pg.pdf(path=str(pdf_path), format="A4", print_background=True,
                     display_header_footer=True, header_template="<div></div>",
                     footer_template=footer,
                     margin={"top":"14mm","bottom":"16mm","left":"14mm","right":"14mm"})
        await b.close()

def main(slug, title):
    body = (ROOT/"src"/f"{slug}.html").read_text(encoding="utf-8")
    out = ROOT/"fiches"/f"{slug}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(TEMPLATE.format(title=title, slug=slug, body=body), encoding="utf-8")
    pdir = ROOT/"pdf"; pdir.mkdir(exist_ok=True)
    asyncio.run(pdf(out, pdir/f"{slug}.pdf", title))
    print("ok", out, pdir/f"{slug}.pdf")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
