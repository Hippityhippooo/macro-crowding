"""Render carousel slides (1080x1350) from slides.json + templates to PNG and one PDF.

Design system [given: linkedin-presence 4.5 / document-design]: cream surface, Fraunces headings,
Schibsted Grotesk body, JetBrains Mono for figures and labels. Margins 96px. Body >= 34px.
Accent (crowded sessions) #2a78d6, contrast (negatives / placebo marker) #eb6834, validated
with the dataviz palette script 2026-10-30. Everything else ink and grey.

Usage: python build.py            -> carousel/out/slide_NN.png, carousel/out/carousel.pdf
Figures come only from output/RESULTS.md via slides.json; this file holds no numbers.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
W, H = 1080, 1350

CSS = """
@font-face{font-family:Fraunces;src:url('file://%(fonts)s/Fraunces.ttf');font-weight:100 900}
@font-face{font-family:Fraunces;src:url('file://%(fonts)s/Fraunces-Italic.ttf');font-style:italic;font-weight:100 900}
@font-face{font-family:'Schibsted Grotesk';src:url('file://%(fonts)s/SchibstedGrotesk.ttf');font-weight:400 900}
@font-face{font-family:'Schibsted Grotesk';src:url('file://%(fonts)s/SchibstedGrotesk-Italic.ttf');font-style:italic;font-weight:400 900}
@font-face{font-family:'JetBrains Mono';src:url('file://%(fonts)s/JetBrainsMono.ttf');font-weight:100 800}
:root{--cream:#f6f1e7;--ink:#141311;--grey:#6b665c;--line:#d9d2c2;--accent:#2a78d6;--contrast:#eb6834;--soft:#e9e2d2}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px;background:var(--cream);color:var(--ink);font-family:'Schibsted Grotesk',sans-serif;-webkit-font-smoothing:antialiased}
.slide{position:relative;width:1080px;height:1350px;padding:96px;display:flex;flex-direction:column}
.kicker{font-family:'JetBrains Mono',monospace;font-size:24px;letter-spacing:.02em;color:var(--grey);margin-bottom:28px}
.page{position:absolute;top:96px;right:96px;font-family:'JetBrains Mono',monospace;font-size:24px;color:var(--grey)}
h1{font-family:Fraunces,serif;font-weight:600;font-size:84px;line-height:1.04;letter-spacing:-.01em;margin-bottom:36px}
h1.small{font-size:72px}
h2{font-family:Fraunces,serif;font-weight:600;font-size:64px;line-height:1.08;margin-bottom:36px}
.lead{font-size:40px;line-height:1.3;color:var(--ink);margin-bottom:28px}
.lead i{font-family:Fraunces,serif;font-style:italic}
p.body{font-size:38px;line-height:1.32;margin-bottom:22px}
.muted{color:var(--grey)}
.chips{display:flex;flex-wrap:wrap;gap:14px;margin:24px 0 0}
.chip{font-family:'JetBrains Mono',monospace;font-size:26px;padding:12px 20px;border:2px solid var(--line);border-radius:999px;color:var(--ink)}
.hero{font-family:'JetBrains Mono',monospace;font-size:200px;line-height:1;font-weight:600;color:var(--accent);margin:28px 0 12px}
.hero.neg{color:var(--contrast)}
.hero.ink{color:var(--ink)}
.herolabel{font-size:36px;color:var(--grey);margin-bottom:36px}
ol{list-style:none;counter-reset:n;margin-top:8px}
ol li{counter-increment:n;font-size:38px;line-height:1.32;padding-left:84px;position:relative;margin-bottom:26px}
ol li::before{content:counter(n);position:absolute;left:0;top:2px;font-family:'JetBrains Mono',monospace;font-size:34px;color:var(--accent);font-weight:600}
ul.plain{list-style:none}
ul.plain li{font-size:36px;line-height:1.32;margin-bottom:18px;padding-left:40px;position:relative}
ul.plain li::before{content:'\\2022';position:absolute;left:0;color:var(--grey)}
.fig{flex:1;display:flex;align-items:center;justify-content:center;margin:12px 0 20px}
.fig img{max-width:888px;max-height:720px}
.foot{position:absolute;left:96px;right:96px;bottom:72px;font-family:'JetBrains Mono',monospace;font-size:22px;color:var(--grey);display:flex;justify-content:space-between}
.swipe{position:absolute;right:96px;bottom:72px;font-family:'JetBrains Mono',monospace;font-size:26px;color:var(--accent)}
.name{position:absolute;left:96px;bottom:72px;font-size:28px;color:var(--grey)}
.accent{color:var(--accent)}.contrast{color:var(--contrast)}
table.t{border-collapse:collapse;width:100%%;font-size:34px;margin:12px 0 24px}
table.t th{font-family:'JetBrains Mono',monospace;font-weight:400;font-size:26px;color:var(--grey);text-align:left;padding:10px 0;border-bottom:2px solid var(--line)}
table.t td{padding:16px 0;border-bottom:1px solid var(--line);font-family:'JetBrains Mono',monospace}
table.t td:first-child{font-family:'Schibsted Grotesk',sans-serif}
.rule{height:2px;background:var(--line);margin:28px 0}
"""


def html_for(slide: dict, n: int, N: int) -> str:
    t = slide["type"]
    body = ""
    if t == "cover":
        chips = "".join(f'<span class="chip">{c}</span>' for c in slide.get("chips", []))
        body = f'<div class="kicker">{slide.get("kicker","")}</div><h1>{slide["title"]}</h1><div class="lead"><i>{slide["sub"]}</i></div><div class="chips">{chips}</div><div class="name">{slide["name"]}</div><div class="swipe">swipe &#8594;</div>'
    elif t == "text":
        paras = "".join(f'<p class="body">{p}</p>' for p in slide.get("paras", []))
        hero = f'<div class="hero {slide.get("hero_class","")}">{slide["hero"]}</div><div class="herolabel">{slide["hero_label"]}</div>' if slide.get("hero") else ""
        body = f'<div class="kicker">{slide.get("kicker","")}</div><h2>{slide["title"]}</h2>{hero}{paras}'
    elif t == "steps":
        items = "".join(f"<li>{s}</li>" for s in slide["steps"])
        body = f'<div class="kicker">{slide.get("kicker","")}</div><h2>{slide["title"]}</h2><ol>{items}</ol>'
    elif t == "figure":
        paras = "".join(f'<p class="body">{p}</p>' for p in slide.get("paras", []))
        body = f'<div class="kicker">{slide.get("kicker","")}</div><h2>{slide["title"]}</h2><div class="fig"><img src="file://{HERE / "figs" / slide["img"]}"></div>{paras}'
    elif t == "table":
        head = "".join(f"<th>{h}</th>" for h in slide["head"])
        rows = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in slide["rows"])
        paras = "".join(f'<p class="body">{p}</p>' for p in slide.get("paras", []))
        body = f'<div class="kicker">{slide.get("kicker","")}</div><h2>{slide["title"]}</h2><table class="t"><tr>{head}</tr>{rows}</table>{paras}'
    elif t == "list":
        items = "".join(f"<li>{s}</li>" for s in slide["items"])
        body = f'<div class="kicker">{slide.get("kicker","")}</div><h2>{slide["title"]}</h2><ul class="plain">{items}</ul>'
    foot = f'<div class="foot"><span>{slide.get("foot","")}</span></div>' if slide.get("foot") else ""
    page = f'<div class="page">{n} / {N}</div>' if t != "cover" else ""
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS % {'fonts': Path.home() / 'fonts'}}</style></head><body><div class='slide'>{page}{body}{foot}</div></body></html>"


def main():
    slides = json.loads((HERE / "slides.json").read_text())
    OUT.mkdir(exist_ok=True)
    N = len(slides)
    from playwright.sync_api import sync_playwright
    pngs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for i, s in enumerate(slides, 1):
            f = OUT / f"slide_{i:02d}.html"
            f.write_text(html_for(s, i, N))
            pg.goto(f"file://{f}")
            pg.wait_for_timeout(250)
            overflow = pg.evaluate("() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
            words = pg.evaluate("() => document.body.innerText.split(/\\s+/).filter(Boolean).length")
            png = OUT / f"slide_{i:02d}.png"
            pg.screenshot(path=str(png), full_page=False)
            pngs.append(png)
            flag = " OVERFLOW" if overflow > H else ""
            print(f"slide {i:02d} words={words} height={overflow}{flag}")
        b.close()
    # PDF from PNGs
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in pngs]
    ims[0].save(OUT / "carousel.pdf", save_all=True, append_images=ims[1:], resolution=96)
    print("pdf", OUT / "carousel.pdf", (OUT / "carousel.pdf").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    sys.exit(main())
