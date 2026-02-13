#!/usr/bin/env python3
"""
Comparador de PDFs (original vs traducido) orientado a maquetación.

Métricas por página:
- Bloques / Líneas / Spans de texto
- Tamaños de fuente (promedio, min, max)
- Familias de fuente detectadas
- Imágenes por página

Uso:
  python compare_pdfs.py <original.pdf> <traducido.pdf>

Opcional:
  --max-pages N   Limitar cantidad de páginas analizadas
"""

import argparse
import os
import sys
from typing import Dict, Any, Tuple, List, Set

import fitz  # PyMuPDF


def analyze_page(page: fitz.Page) -> Dict[str, Any]:
    d = page.get_text("dict")
    blocks = 0
    lines = 0
    spans = 0
    font_sizes: List[float] = []
    fonts: Set[str] = set()
    for b in d.get("blocks", []):
        if b.get("type") != 0:
            continue
        blocks += 1
        for ln in b.get("lines", []):
            lines += 1
            for sp in ln.get("spans", []):
                spans += 1
                size = float(sp.get("size", 0))
                if size > 0:
                    font_sizes.append(size)
                f = str(sp.get("font", "")).strip()
                if f:
                    fonts.add(f)

    avg = sum(font_sizes) / len(font_sizes) if font_sizes else 0.0
    mn = min(font_sizes) if font_sizes else 0.0
    mx = max(font_sizes) if font_sizes else 0.0
    images = len(page.get_images(full=True))
    # Márgenes aproximados (usando todos los spans de texto)
    xs0: List[float] = []
    xs1: List[float] = []
    ys0: List[float] = []
    ys1: List[float] = []
    for b in d.get("blocks", []):
        if b.get("type") != 0:
            continue
        for ln in b.get("lines", []):
            for sp in ln.get("spans", []):
                bb = sp.get("bbox")
                if not bb:
                    continue
                x0, y0, x1, y1 = bb
                xs0.append(x0)
                xs1.append(x1)
                ys0.append(y0)
                ys1.append(y1)

    page_rect = page.rect  # type: ignore[attr-defined]
    left_margin = float(min(xs0)) - float(page_rect.x0) if xs0 else 0.0
    right_margin = float(page_rect.x1) - float(max(xs1)) if xs1 else 0.0
    top_margin = float(min(ys0)) - float(page_rect.y0) if ys0 else 0.0
    bottom_margin = float(page_rect.y1) - float(max(ys1)) if ys1 else 0.0

    return {
        "blocks": blocks,
        "lines": lines,
        "spans": spans,
        "avg_size": round(avg, 2),
        "min_size": round(mn, 2),
        "max_size": round(mx, 2),
        "fonts": sorted(fonts),
        "images": images,
        "margins": {
            "left": round(left_margin, 2),
            "right": round(right_margin, 2),
            "top": round(top_margin, 2),
            "bottom": round(bottom_margin, 2),
            "width": round(float(page_rect.width), 2),
            "height": round(float(page_rect.height), 2),
        },
    }


def compare_pages(a: Dict[str, Any], b: Dict[str, Any]) -> Tuple[bool, List[str]]:
    ok = True
    reasons: List[str] = []
    for key in ("blocks", "lines", "spans", "images"):
        if a[key] != b[key]:
            ok = False
            reasons.append(f"{key}: {a[key]} -> {b[key]}")

    # Tolerancias suaves para tamaños de fuente
    for key, tol in (("avg_size", 0.6), ("min_size", 0.6), ("max_size", 0.6)):
        if abs(a[key] - b[key]) > tol:
            ok = False
            reasons.append(f"{key}: {a[key]} -> {b[key]} (±{tol})")

    # Márgenes (tolerancia en puntos)
    mtol = 2.0
    for side in ("left", "right", "top", "bottom"):
        aval = a["margins"][side]
        bval = b["margins"][side]
        if abs(aval - bval) > mtol:
            ok = False
            reasons.append(f"margin {side}: {aval} -> {bval} (±{mtol})")

    # Conjuntos de fuentes (solo informativo si cambian)
    if set(a["fonts"]) != set(b["fonts"]):
        reasons.append("fonts changed")

    return ok, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparar maquetación de PDFs original vs traducido")
    parser.add_argument("original", help="Ruta al PDF original")
    parser.add_argument("traducido", help="Ruta al PDF traducido")
    parser.add_argument("--max-pages", type=int, default=0, help="Limitar páginas a analizar")
    args = parser.parse_args()

    if not os.path.exists(args.original):
        print(f"ERROR: No existe original: {args.original}")
        return 1
    if not os.path.exists(args.traducido):
        print(f"ERROR: No existe traducido: {args.traducido}")
        return 1

    with fitz.open(args.original) as A, fitz.open(args.traducido) as B:
        pages = min(A.page_count, B.page_count)
        if args.max_pages:
            pages = min(pages, args.max_pages)

        print("=" * 80)
        print(f"Comparando: {os.path.basename(args.original)}  vs  {os.path.basename(args.traducido)}")
        print("=" * 80)

        all_ok = True
        for i in range(pages):
            a = analyze_page(A[i])
            b = analyze_page(B[i])
            ok, reasons = compare_pages(a, b)

            print(f"\nPágina {i+1}/{pages}")
            print(f"  Original -> blocks:{a['blocks']} lines:{a['lines']} spans:{a['spans']} img:{a['images']} sizes(avg/min/max): {a['avg_size']}/{a['min_size']}/{a['max_size']}")
            print(f"              margins L/R/T/B: {a['margins']['left']}/{a['margins']['right']}/{a['margins']['top']}/{a['margins']['bottom']}  page: {a['margins']['width']}x{a['margins']['height']}")
            print(f"  Traducido-> blocks:{b['blocks']} lines:{b['lines']} spans:{b['spans']} img:{b['images']} sizes(avg/min/max): {b['avg_size']}/{b['min_size']}/{b['max_size']}")
            print(f"              margins L/R/T/B: {b['margins']['left']}/{b['margins']['right']}/{b['margins']['top']}/{b['margins']['bottom']}  page: {b['margins']['width']}x{b['margins']['height']}")
            if ok:
                print("  RESULTADO: OK (estructura consistente)")
            else:
                all_ok = False
                print("  RESULTADO: DIFERENCIAS")
                for r in reasons:
                    print(f"    - {r}")

        print("\n" + ("OK: Estructura consistente en páginas analizadas" if all_ok else "ATENCIÓN: Se detectaron divergencias"))
        return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(main())
