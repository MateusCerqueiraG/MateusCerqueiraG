#!/usr/bin/env python3
"""Gera github-stats.svg com números reais do perfil (sem dependências externas).

Usa só a stdlib + a API pública do GitHub. Roda local ou no CI (usa GH_TOKEN se
houver, só pra evitar rate limit). Mantém o layout: KPIs + barra de linguagens,
na paleta do Lugia.
"""
import json
import os
import urllib.request
from collections import Counter

USER = os.getenv("STATS_USER", "MateusCerqueiraG")
TOKEN = os.getenv("GH_TOKEN", "")
MONTHS = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
PALETTE = ["#5fd0e6", "#9fb8d4", "#2aa7c4", "#6fcf97", "#f0a868", "#b28fd0"]


def api(url):
    req = urllib.request.Request(url)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def collect():
    prof = api(f"https://api.github.com/users/{USER}")
    repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100")
    active = [r for r in repos if not r.get("archived")]

    langs = Counter()
    for repo in active:
        try:
            for name, size in api(repo["languages_url"]).items():
                langs[name] += size
        except Exception:
            pass
    for markup in ("HTML", "CSS"):
        langs.pop(markup, None)

    total = sum(langs.values()) or 1
    top = [(name, round(100 * size / total, 1), PALETTE[i % len(PALETTE)])
           for i, (name, size) in enumerate(langs.most_common(4))]

    year, month = int(prof["created_at"][:4]), int(prof["created_at"][5:7])
    return {
        "repos": prof["public_repos"],
        "active": len(active),
        "followers": prof["followers"],
        "since": f"{MONTHS[month]} {year}",
        "langs": top,
    }


def render(data):
    W, H = 840, 224
    kpis = [
        (str(data["repos"]), "Repositórios"),
        (str(data["active"]), "Projetos ativos"),
        (str(data["followers"]), "Seguidores"),
        (data["since"], "Membro desde"),
    ]
    centers = [105, 315, 525, 735]
    s = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub Stats">']
    s.append('<defs>'
             '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0a2032"/><stop offset="1" stop-color="#103a4e"/></linearGradient>'
             '<linearGradient id="silver" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8fb0d0"/><stop offset="0.5" stop-color="#eef5fd"/><stop offset="1" stop-color="#8fb0d0"/></linearGradient>'
             '</defs>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="url(#bg)" stroke="#1f4b5e" stroke-width="1"/>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="6" rx="3" fill="#5fd0e6"/>')
    s.append('<text x="420" y="34" text-anchor="middle" font-family="\'Segoe UI\',Ubuntu,Helvetica,sans-serif" font-size="13" letter-spacing="6" fill="url(#silver)">G I T H U B   S T A T S</text>')
    s.append('<line x1="40" y1="48" x2="800" y2="48" stroke="#1f4b5e" stroke-width="1"/>')
    for x in (210, 420, 630):
        s.append(f'<line x1="{x}" y1="62" x2="{x}" y2="112" stroke="#1f4b5e" stroke-width="1"/>')
    s.append('<g text-anchor="middle" font-family="\'Segoe UI\',Ubuntu,Helvetica,sans-serif">')
    for (num, lab), cx in zip(kpis, centers):
        fs = 24 if len(num) > 3 else 28
        s.append(f'<text x="{cx}" y="90" font-size="{fs}" font-weight="800" fill="#7fe0f0">{num}</text>')
        s.append(f'<text x="{cx}" y="110" font-size="12" fill="#9fc0d6">{lab}</text>')
    s.append('</g>')
    s.append('<line x1="40" y1="128" x2="800" y2="128" stroke="#1f4b5e" stroke-width="1"/>')
    s.append('<text x="40" y="152" font-family="\'Segoe UI\',Ubuntu,Helvetica,sans-serif" font-size="11.5" letter-spacing="3" fill="#6f93a8">LINGUAGENS MAIS USADAS</text>')
    # barra empilhada
    bx, by, bw, bh = 40, 162, 760, 16
    total = sum(p for _, p, _ in data["langs"]) or 1
    s.append(f'<clipPath id="barclip"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="8"/></clipPath>')
    s.append('<g clip-path="url(#barclip)">')
    x = bx
    for _, pct, col in data["langs"]:
        w = bw * pct / total
        s.append(f'<rect x="{x:.1f}" y="{by}" width="{w+1:.1f}" height="{bh}" fill="{col}"/>')
        x += w
    s.append('</g>')
    # legenda
    s.append('<g font-family="\'Segoe UI\',Ubuntu,Helvetica,sans-serif" font-size="12.5" fill="#b3cfe0">')
    lx = 40
    for name, pct, col in data["langs"]:
        s.append(f'<circle cx="{lx+4}" cy="198" r="4" fill="{col}"/>')
        s.append(f'<text x="{lx+15}" y="202">{name} {pct}%</text>')
        lx += 20 + (len(name) + 6) * 8
    s.append('</g>')
    s.append('</svg>')
    return "\n".join(s)


if __name__ == "__main__":
    svg = render(collect())
    with open("github-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("github-stats.svg atualizado")
