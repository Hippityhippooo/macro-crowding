"""v2 deck: five layouts, page-scale charts, sharp photos in solid panels.

Layouts
  photo_cover   full-bleed photo, solid ink panel at the bottom with the title
  bignum        navy page, two giant numbers
  chart         header band (tag, action title, one line) + chart image filling the rest, cream or navy
  split_photo   photo on the left 44%, solid panel on the right with numbered steps
  statement     one large serif statement (verdict), plus two short lines
  list          plain list page (limits)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out2"; FIGS = HERE / "figs2"; PHOTOS = HERE / "figs"
W, H = 1080, 1350
FONTS = Path.home() / "fonts"

CSS = f"""
@font-face{{font-family:Fraunces;src:url('file://{FONTS}/Fraunces.ttf');font-weight:100 900}}
@font-face{{font-family:Fraunces;src:url('file://{FONTS}/Fraunces-Italic.ttf');font-style:italic;font-weight:100 900}}
@font-face{{font-family:'Schibsted Grotesk';src:url('file://{FONTS}/SchibstedGrotesk.ttf');font-weight:400 900}}
@font-face{{font-family:'JetBrains Mono';src:url('file://{FONTS}/JetBrainsMono.ttf');font-weight:100 800}}
:root{{--cream:#f6f1e7;--ink:#141311;--navy:#0f1f33;--muted:#6b665c;--line:#d9d2c2;--accent:#2a78d6;--accent-l:#7faae0;--contrast:#eb6834}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:var(--cream);color:var(--ink);font-family:'Schibsted Grotesk',sans-serif;-webkit-font-smoothing:antialiased}}
.s{{position:relative;width:{W}px;height:{H}px;overflow:hidden}}
.num{{position:absolute;top:72px;right:88px;font-family:'JetBrains Mono',monospace;font-size:26px;color:var(--muted)}}
.tag{{font-family:'JetBrains Mono',monospace;font-size:26px;color:var(--muted);letter-spacing:.01em;max-width:780px}}
h1{{font-family:Fraunces,serif;font-weight:600;line-height:1.02;letter-spacing:-.015em}}
h2{{font-family:Fraunces,serif;font-weight:600;font-size:58px;line-height:1.08;letter-spacing:-.012em;margin:14px 0 18px}}
.sub{{font-size:33px;line-height:1.36;color:var(--ink)}}
.navy{{background:var(--navy);color:var(--cream)}} .navy .tag,.navy .num{{color:#aab4c3}} .navy .sub{{color:#e6e9ee}}
/* photo cover */
.cover .photo{{position:absolute;inset:0;background:url('file://{PHOTOS}/fed_cover.png') center/cover no-repeat}}
.cover .panel{{position:absolute;left:0;right:0;bottom:0;background:var(--ink);color:var(--cream);padding:72px 88px 64px}}
.cover h1{{font-size:78px;margin:16px 0 24px}}
.cover .sub{{color:#d9d2c2;font-family:Fraunces,serif;font-style:italic;font-weight:400;font-size:34px}}
.cover .meta{{display:flex;justify-content:space-between;margin-top:40px;font-family:'JetBrains Mono',monospace;font-size:24px;color:#b9b2a3}}
.cover .credit{{position:absolute;top:72px;right:88px;font-family:'JetBrains Mono',monospace;font-size:22px;color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.6)}}
/* bignum */
.bignum{{padding:88px}}
.bignum .pair{{display:flex;gap:56px;align-items:flex-end;margin-top:140px}}
.bignum .n{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:250px;line-height:.9;letter-spacing:-.04em}}
.bignum .n.a{{color:var(--accent-l)}} .bignum .n.b{{color:#6f7d92}}
.bignum .l{{font-size:34px;color:#aab4c3;margin-top:22px;max-width:380px;line-height:1.3}}
.bignum .sub{{margin-top:110px;font-size:36px;max-width:860px}}
/* chart */
.chart .head{{padding:72px 88px 0;height:{H - 860}px}}
.chart .img{{position:absolute;left:60px;right:60px;bottom:40px;height:800px}}
.chart .img img{{width:960px;height:800px;display:block}}
.chart.tall .head{{height:{H - 980}px;padding-top:64px}} .chart.tall h2{{font-size:52px;margin-top:10px}} .chart.tall .img{{height:933px;bottom:40px}} .chart.tall .img img{{height:933px}}
/* split photo */
.split .photo{{position:absolute;left:0;top:0;bottom:0;width:470px;background:url('file://{PHOTOS}/sec_cover.png') center/cover no-repeat}}
.split .panel{{position:absolute;left:470px;top:0;bottom:0;right:0;background:var(--ink);color:var(--cream);padding:80px 72px 72px 64px}}
.split ol{{list-style:none;counter-reset:n;margin-top:30px}}
.split ol li{{counter-increment:n;font-size:30px;line-height:1.32;padding-left:58px;position:relative;margin-bottom:30px;color:#e9e2d2}}
.split ol li::before{{content:counter(n, decimal-leading-zero);position:absolute;left:0;top:4px;font-family:'JetBrains Mono',monospace;font-size:26px;color:var(--accent-l)}}
.split h2{{font-size:52px;color:var(--cream)}} .split .tag,.split .num{{color:#b9b2a3}}
.split .credit{{position:absolute;left:24px;bottom:24px;font-family:'JetBrains Mono',monospace;font-size:20px;color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.7)}}
/* statement */
.statement{{padding:88px;display:flex;flex-direction:column}}
.statement h1{{font-size:84px;margin-top:120px}}
.statement h1 em{{font-style:italic;font-weight:400;color:var(--accent)}}
.statement .sub{{margin-top:56px;font-size:33px;max-width:860px}}
.statement .foot{{position:absolute;left:88px;right:88px;bottom:72px;font-family:'JetBrains Mono',monospace;font-size:24px;color:var(--muted)}}
/* list */
.list{{padding:88px}}
.list ul{{list-style:none;margin-top:36px}}
.list ul li{{font-size:37px;line-height:1.36;margin-bottom:44px;padding-left:52px;position:relative}}
.list ul li::before{{content:'';position:absolute;left:0;top:20px;width:22px;height:4px;background:var(--accent)}}
"""


def render(sl: dict, n: int, N: int) -> str:
    t = sl["type"]; num = f'<div class="num">{n:02d} / {N:02d}</div>'
    if t == "photo_cover":
        body = f'<div class="photo"></div><div class="credit">{sl["credit"]}</div><div class="panel"><div class="tag">{sl["tag"]}</div><h1>{sl["title"]}</h1><div class="sub">{sl["sub"]}</div><div class="meta"><span>{sl["meta_l"]}</span><span>{sl["meta_r"]}</span></div></div>'
        cls = "s cover"
    elif t == "bignum":
        body = f'{num}<div class="tag">{sl["tag"]}</div><div class="pair"><div><div class="n a">{sl["a"]}</div><div class="l">{sl["a_l"]}</div></div><div><div class="n b">{sl["b"]}</div><div class="l">{sl["b_l"]}</div></div></div><div class="sub">{sl["sub"]}</div>'
        cls = "s bignum navy"
    elif t == "chart":
        body = f'{num}<div class="head"><div class="tag">{sl["tag"]}</div><h2>{sl["title"]}</h2><div class="sub">{sl.get("sub","")}</div></div><div class="img"><img src="file://{FIGS / sl["img"]}"></div>'
        cls = "s chart" + (" navy" if sl.get("navy") else "") + (" tall" if sl.get("tall") else "")
    elif t == "split_photo":
        items = "".join(f"<li>{x}</li>" for x in sl["steps"])
        body = f'<div class="photo"><div class="credit">{sl["credit"]}</div></div><div class="panel">{num}<div class="tag">{sl["tag"]}</div><h2>{sl["title"]}</h2><ol>{items}</ol></div>'
        cls = "s split"
    elif t == "statement":
        body = f'{num}<div class="tag">{sl["tag"]}</div><h1>{sl["title"]}</h1><div class="sub">{sl["sub"]}</div><div class="foot">{sl.get("foot","")}</div>'
        cls = "s statement"
    elif t == "list":
        items = "".join(f"<li>{x}</li>" for x in sl["items"])
        body = f'{num}<div class="tag">{sl["tag"]}</div><h2>{sl["title"]}</h2><ul>{items}</ul>'
        cls = "s list"
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='{cls}'>{body}</div></body></html>"


def main():
    slides = json.loads((HERE / "slides2.json").read_text()); N = len(slides)
    OUT.mkdir(exist_ok=True)
    from playwright.sync_api import sync_playwright
    pngs = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        for i, sl in enumerate(slides, 1):
            f = OUT / f"slide_{i:02d}.html"; f.write_text(render(sl, i, N)); pg.goto(f"file://{f}"); pg.wait_for_timeout(200)
            words = pg.evaluate("() => document.body.innerText.split(/\\s+/).filter(Boolean).length")
            ov = pg.evaluate("() => { const h=document.querySelector('.head'); return h ? h.scrollHeight > h.clientHeight : false }")
            png = OUT / f"slide_{i:02d}.png"; pg.screenshot(path=str(png)); pngs.append(png)
            print(f"slide {i:02d} {sl['type']:12s} words={words}{' HEAD OVERFLOW' if ov else ''}")
        b.close()
    from PIL import Image
    ims = [Image.open(x).convert("RGB") for x in pngs]
    ims[0].save(OUT / "carousel.pdf", save_all=True, append_images=ims[1:], resolution=96)
    print("pdf", (OUT / "carousel.pdf").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    sys.exit(main())
