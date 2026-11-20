#!/usr/bin/env python3
"""Compare saved IPC-compatible WIPO profiles across the three paper models.

This is a post-processing step over an existing K=8 run. It does not fit or
reassign clusters. Outputs are a long-form profile CSV, pairwise similarity
CSV, two SVG heatmaps, and a short interpretation note.
"""
from __future__ import annotations

import argparse
import csv
import html
import itertools
import math
from pathlib import Path

MODELS = [
    ("qwen3-embedding-4b", "Qwen 4B"),
    ("sbert-adapt-ub", "SBERT"),
    ("pat-specter", "Pat-SPECTER"),
]


def load_profiles(run_dir: Path, cohort: str, k: int):
    profiles = {}
    field_names = {}
    long_rows = []
    for model, display in MODELS:
        path = run_dir / "profiles" / f"{cohort}__{model}__k{k}__wipo_profiles.csv"
        matrix = {}
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row["wipo_profile_type"] != "ipc_compatible":
                    continue
                cluster = int(row["cluster"])
                field_num = int(row["wipo_field_number"])
                prevalence = float(row["cluster_share"])
                matrix.setdefault(cluster, {})[field_num] = prevalence
                field_names[field_num] = row["wipo_field_name"]
                long_rows.append({
                    "model": display,
                    "cluster": cluster,
                    "wipo_field_number": field_num,
                    "wipo_field_name": row["wipo_field_name"],
                    "patents_with_compatible_field": int(row["n_patents"]),
                    "share_of_cluster_percent": round(prevalence * 100, 4),
                    "lift_vs_cohort": round(float(row["lift"]), 6),
                })
        profiles[display] = matrix
    return profiles, field_names, long_rows


def weighted_jaccard(a, b, fields):
    numerator = sum(min(a.get(f, 0.0), b.get(f, 0.0)) for f in fields)
    denominator = sum(max(a.get(f, 0.0), b.get(f, 0.0)) for f in fields)
    return numerator / denominator if denominator else 0.0


def cosine(a, b, fields):
    dot = sum(a.get(f, 0.0) * b.get(f, 0.0) for f in fields)
    na = math.sqrt(sum(a.get(f, 0.0) ** 2 for f in fields))
    nb = math.sqrt(sum(b.get(f, 0.0) ** 2 for f in fields))
    return dot / (na * nb) if na and nb else 0.0


def interpolate(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def blue(value, vmax):
    t = max(0.0, min(1.0, value / vmax)) if vmax else 0.0
    pale, mid, dark = (247, 251, 255), (107, 174, 214), (8, 48, 107)
    color = interpolate(pale, mid, t * 2) if t < .5 else interpolate(mid, dark, (t - .5) * 2)
    return "#%02x%02x%02x" % color


def orange(value):
    t = max(0.0, min(1.0, value))
    pale, mid, dark = (255, 247, 236), (253, 174, 107), (127, 39, 4)
    color = interpolate(pale, mid, t * 2) if t < .5 else interpolate(mid, dark, (t - .5) * 2)
    return "#%02x%02x%02x" % color


def write_profile_heatmap(path, profiles, field_names, k):
    fields = list(range(1, 33))
    vals = [v for matrix in profiles.values() for row in matrix.values() for v in row.values()]
    vmax = max(.1, math.ceil(max(vals, default=0.0) * 10) / 10)
    left, top, cw, ch = 180, 120, 29, 23
    gap = 18
    row_positions = {}
    y = top
    for model, _ in MODELS:
        for cluster in range(k):
            row_positions[(model, cluster)] = y
            y += ch
        y += gap
    width = left + cw * len(fields) + 230
    height = y + 90
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    out += ['<rect width="100%" height="100%" fill="white"/>',
            '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#263238}.small{font-size:10px}.tiny{font-size:9px}.title{font-size:20px;font-weight:700}.subtitle{font-size:12px;fill:#52616b}</style>']
    out.append(f'<text x="{left}" y="35" class="title">Compatibilità WIPO nei cluster — corpus completo, K={k}</text>')
    out.append(f'<text x="{left}" y="58" class="subtitle">Quota di brevetti del cluster associata a ciascun campo WIPO compatibile via IPC; campi multi-label.</text>')
    for idx, field in enumerate(fields):
        x = left + idx * cw + cw / 2
        out.append(f'<text x="{x}" y="{top-12}" text-anchor="middle" class="tiny">{field:02d}</text>')
    for mi, (model, display) in enumerate(MODELS):
        group_y = row_positions[(model, 0)] - 8
        out.append(f'<text x="18" y="{group_y}" class="small" font-weight="700">{html.escape(display)}</text>')
        for cluster in range(k):
            yy = row_positions[(model, cluster)]
            out.append(f'<text x="150" y="{yy+15}" text-anchor="end" class="small">C{cluster}</text>')
            row = profiles[display][cluster]
            for fi, field in enumerate(fields):
                value = row.get(field, 0.0)
                x = left + fi * cw
                out.append(f'<rect x="{x}" y="{yy}" width="{cw-1}" height="{ch-1}" fill="{blue(value,vmax)}"><title>{html.escape(display)} cluster {cluster}; WIPO {field:02d} {html.escape(field_names.get(field,''))}: {value*100:.1f}%</title></rect>')
        if mi < len(MODELS) - 1:
            yy = row_positions[(model, k-1)] + ch + gap / 2
            out.append(f'<line x1="12" y1="{yy}" x2="{left+cw*len(fields)}" y2="{yy}" stroke="#cbd5e1"/>')
    lx, ly = left + cw * len(fields) + 36, top + 28
    out.append(f'<text x="{lx}" y="{ly-10}" class="small" font-weight="700">Prevalenza</text>')
    for i in range(51):
        value = vmax * i / 50
        out.append(f'<rect x="{lx}" y="{ly+i*5}" width="20" height="6" fill="{blue(value,vmax)}"/>')
    for pct in (0, .25, .5, .75, 1):
        yy = ly + pct * 250
        out.append(f'<text x="{lx+28}" y="{yy+4}" class="tiny">{vmax*pct*100:.0f}%</text>')
    out.append(f'<text x="{lx}" y="{ly+285}" class="tiny">WIPO field numbers</text>')
    out.append(f'<text x="{left}" y="{height-35}" class="tiny">Legenda dei campi: docs/wipo-technology-fields.csv. Le quote non sommano necessariamente a 100%, perché un brevetto può essere compatibile con più campi.</text>')
    out.append('</svg>')
    path.write_text('\n'.join(out), encoding='utf-8')


def write_similarity_heatmap(path, profiles, k):
    pairs = list(itertools.combinations([d for _, d in MODELS], 2))
    cw, left, top, gap = 42, 48, 85, 86
    panel_w = left + cw * k + 20
    width = panel_w * len(pairs) + 30
    height = 560
    fields = list(range(1, 33))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#263238}.small{font-size:11px}.tiny{font-size:10px}.title{font-size:20px;font-weight:700}.subtitle{font-size:12px;fill:#52616b}</style>',
           f'<text x="30" y="32" class="title">Sovrapposizione dei profili WIPO compatibili</text>',
           f'<text x="30" y="55" class="subtitle">Weighted Jaccard sulle prevalenze dei 32 campi; ogni cella confronta due cluster, senza forzare un abbinamento 1:1.</text>']
    for pi, (ma, mb) in enumerate(pairs):
        x0 = 25 + pi * panel_w
        out.append(f'<text x="{x0+left+cw*k/2}" y="{top-42}" text-anchor="middle" class="small" font-weight="700">{html.escape(ma)} × {html.escape(mb)}</text>')
        for cb in range(k):
            out.append(f'<text x="{x0+left+cb*cw+cw/2}" y="{top-12}" text-anchor="middle" class="tiny">{cb}</text>')
        for ca in range(k):
            out.append(f'<text x="{x0+left-8}" y="{top+ca*cw+cw*.65}" text-anchor="end" class="tiny">{ca}</text>')
            for cb in range(k):
                sim = weighted_jaccard(profiles[ma][ca], profiles[mb][cb], fields)
                xx, yy = x0 + left + cb*cw, top + ca*cw
                out.append(f'<rect x="{xx}" y="{yy}" width="{cw-1}" height="{cw-1}" fill="{orange(sim)}"><title>{html.escape(ma)} cluster {ca} vs {html.escape(mb)} cluster {cb}: weighted Jaccard {sim:.3f}</title></rect>')
                color = '#ffffff' if sim > .68 else '#263238'
                out.append(f'<text x="{xx+cw/2}" y="{yy+cw*.62}" text-anchor="middle" class="tiny" style="fill:{color}">{sim:.2f}</text>')
        out.append(f'<text x="{x0+left+cw*k/2}" y="{top+cw*k+26}" text-anchor="middle" class="tiny">cluster {html.escape(mb)}</text>')
        out.append(f'<text x="{x0+left-36}" y="{top+cw*k/2}" text-anchor="middle" transform="rotate(-90 {x0+left-36} {top+cw*k/2})" class="tiny">cluster {html.escape(ma)}</text>')
    out.append(f'<text x="30" y="{height-18}" class="tiny">Profilo = percentuale di brevetti nel cluster con ciascun campo compatibile. WIPO è multi-label; valori e somiglianze sono descrittivi.</text>')
    out.append('</svg>')
    path.write_text('\n'.join(out), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, default=Path('analysis/results/run_20261118T132255Z'))
    parser.add_argument('--cohort', default='full')
    parser.add_argument('--k', type=int, default=8)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir
    out_dir = args.output_dir or (run_dir / 'comparison')
    out_dir.mkdir(parents=True, exist_ok=True)
    profiles, field_names, rows = load_profiles(run_dir, args.cohort, args.k)
    fields = list(range(1, 33))
    with (out_dir / f'wipo_cluster_profiles_{args.cohort}_k{args.k}.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    sims = []
    for ma, mb in itertools.combinations([d for _, d in MODELS], 2):
        for ca, a in profiles[ma].items():
            for cb, b in profiles[mb].items():
                sims.append({
                    'model_a': ma, 'cluster_a': ca, 'model_b': mb, 'cluster_b': cb,
                    'weighted_jaccard': round(weighted_jaccard(a,b,fields),6),
                    'cosine_similarity': round(cosine(a,b,fields),6),
                })
    with (out_dir / f'wipo_cluster_similarity_{args.cohort}_k{args.k}.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=sims[0].keys())
        w.writeheader(); w.writerows(sims)
    profile_svg = out_dir / f'wipo_cluster_profiles_{args.cohort}_k{args.k}.svg'
    sim_svg = out_dir / f'wipo_cluster_overlap_{args.cohort}_k{args.k}.svg'
    write_profile_heatmap(profile_svg, profiles, field_names, args.k)
    write_similarity_heatmap(sim_svg, profiles, args.k)
    note_path = out_dir / f'wipo_cluster_comparison_{args.cohort}_k{args.k}.md'
    lines = [
        f'# Confronto dei profili WIPO nei cluster — {args.cohort}, K={args.k}', '',
        '## Materiali', '',
        f'- Heatmap prevalenza WIPO: [`{profile_svg.name}`]({profile_svg.name})',
        f'- Heatmap similarità profili: [`{sim_svg.name}`]({sim_svg.name})',
        f'- Prevalenze per cluster e campo: [`wipo_cluster_profiles_{args.cohort}_k{args.k}.csv`](wipo_cluster_profiles_{args.cohort}_k{args.k}.csv)',
        f'- Similarità per coppia di cluster: [`wipo_cluster_similarity_{args.cohort}_k{args.k}.csv`](wipo_cluster_similarity_{args.cohort}_k{args.k}.csv)', '',
        '## Come leggere il confronto', '',
        'La prevalenza è la quota di brevetti del cluster con almeno un IPC compatibile con il campo WIPO. I campi sono multi-label, quindi le quote per riga non sommano a 100%. La similarità tra due profili usa il weighted Jaccard sulle 32 prevalenze: 0 indica nessuna prevalenza condivisa, 1 profili identici. Le matrici non forzano una corrispondenza 1:1 tra cluster.', '',
        'Questa è una comparazione descrittiva dei profili WIPO. Non misura direttamente se gli stessi brevetti siano raggruppati insieme: per l’accordo sulle assegnazioni va letto insieme all’ARI tra modelli. La coorte è stratificata per field WIPO, quindi l’allineamento ai campi non è una validazione indipendente.', '',
        '## Coppie con maggiore sovrapposizione', '',
        '| Modelli | Cluster | Weighted Jaccard | Campi con prevalenza alta in entrambi (A / B) |',
        '|---|---:|---:|---|',
    ]
    for ma, mb in itertools.combinations([d for _, d in MODELS], 2):
        group = [r for r in sims if r['model_a']==ma and r['model_b']==mb]
        for r in sorted(group,key=lambda x:x['weighted_jaccard'],reverse=True)[:3]:
            a=profiles[ma][r['cluster_a']]; b=profiles[mb][r['cluster_b']]
            common=sorted(fields,key=lambda f:min(a.get(f,0),b.get(f,0)),reverse=True)[:3]
            names=', '.join(f'{field_names[f]} ({a.get(f,0)*100:.1f}% / {b.get(f,0)*100:.1f}%)' for f in common)
            lines.append(f"| {ma} × {mb} | {r['cluster_a']} ↔ {r['cluster_b']} | {r['weighted_jaccard']:.3f} | {names} |")
    lines += ['', '## Accordo sulle assegnazioni', '', 'Il weighted Jaccard confronta la forma dei profili WIPO, mentre l’ARI confronta quali brevetti finiscono insieme nei due clustering. Sono misure diverse: profili WIPO simili possono coesistere con un accordo più limitato sulle assegnazioni.', '', '| Modelli | ARI (seed 42) |', '|---|---:|']
    ari_path = run_dir / "metrics" / "cross_model_ari_reference_seed.csv"
    ari_rows = []
    with ari_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["cohort"] == args.cohort and int(row["k"]) == args.k and row["seed"] == "42":
                ari_rows.append(row)
    model_ids = {display: model for model, display in MODELS}
    for ma, mb in itertools.combinations([d for _, d in MODELS], 2):
        wanted = {model_ids[ma], model_ids[mb]}
        match = next((r for r in ari_rows if {r["model_a"], r["model_b"]} == wanted), None)
        if match:
            lines.append(f"| {ma} × {mb} | {float(match['ARI']):.3f} |")
    lines += ['', '## Fonti', '', f'- Profili salvati nel run: `profiles/{args.cohort}__<model>__k{args.k}__wipo_profiles.csv`.', '- Glossario dei campi: [`../../../../docs/wipo-technology-fields.csv`](../../../../docs/wipo-technology-fields.csv).', '- Metriche ARI tra modelli: `metrics/cross_model_ari_reference_seed.csv`.', '']
    note_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {profile_svg}, {sim_svg}, {note_path}')


if __name__ == '__main__':
    main()
