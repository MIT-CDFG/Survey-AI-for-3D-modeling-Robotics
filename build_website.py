#!/usr/bin/env python3
"""
Website generator for Frontier 3D & Robotics Survey (MIT CSAIL CDFG):
1. Native academic English layout matching SIGGRAPH / ACM publication standards.
2. Direct embedding of LaTeX paper sections, figures, and benchmark comparisons.
3. Multi-view interface: Full Survey Reader, Empirical Benchmarks, and Visual Case Archive.
4. Interactive evidence filtering by 3-tier empirical verification protocols.
"""

import os
import re
import glob
import json
import subprocess
import time
import urllib.request

WEBSITE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(WEBSITE_DIR)

# Feature flag: Temporarily disable PDF download/viewer on website
ENABLE_PDF_DOWNLOAD = False

# Formal monochrome academic SVG line icons (Feather / Lucide line design)
ICON_PAPER = '<svg class="btn-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>'
ICON_STATS = '<svg class="btn-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
ICON_GALLERY = '<svg class="btn-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
ICON_PDF = '<svg class="btn-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>'
ICON_DOWNLOAD = '<svg class="btn-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>'
ICON_BIBTEX = '<svg class="btn-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>'


def clean_desc_text(text):
    if not text:
        return ""
    text = text.replace(r"\astra{}", "Astra").replace(r"\astra", "Astra")
    text = text.replace(r"\_", "_")
    text = text.strip()
    if text.startswith("["):
        m = re.match(r"^\[(.*?)\](.*)$", text)
        if m:
            text = m.group(1).strip() + m.group(2)
        else:
            text = text.lstrip("[").rstrip("]")
    text = text.replace("]", "").replace("[", "")
    return text.strip()

def parse_bib_urls():
    bib_urls = {}
    current_key = None
    bib_path = os.path.join(WORKSPACE, "posts.bib")
    if os.path.exists(bib_path):
        with open(bib_path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"@\w+\{([^,]+),", line)
                if m:
                    current_key = m.group(1).strip()
                if current_key:
                    um = re.search(r"url\s*=\s*\{([^}]+)\}", line)
                    if um:
                        bib_urls[current_key] = um.group(1).strip()
    return bib_urls

def parse_case_index(bib_urls=None):
    if bib_urls is None:
        bib_urls = parse_bib_urls()

    # Parse tiles.json for key mappings
    tiles = {}
    tiles_path = os.path.join(WORKSPACE, "figures/gallery/tiles.json")
    if os.path.exists(tiles_path):
        with open(tiles_path, encoding="utf-8") as f:
            tiles = json.load(f)

    extra_code_urls = {
        "M28": "https://github.com/emollick/abyssal-living-deep",
        "M42": "https://github.com/per-simmons/blender-production",
        "M48": "https://github.com/openretriever/retriever",
        "R01": "https://github.com/robocurve/inspect-robots",
        "R03": "https://github.com/NVlabs/ENPIRE",
        "R04": "https://github.com/robocurve/stationerybench",
        "R07": "https://github.com/RoboDojo-Benchmark/RoboDojo",
        "R08": "https://github.com/huggingface/lerobot",
        "R13": "https://github.com/robocurve/roboharm",
        "R14": "https://github.com/allenai/molmoact2/tree/main/sim_eval",
        "R18": "https://github.com/Hu-xiao-max/dexgpt",
        "R29": "https://github.com/anonymous-report-421/GPT-as-Policy",
        "R30": "https://github.com/nftechie/misalignment/tree/main/experiments/001",
    }

    # Parse sec/a_case_index.tex
    cases = {}
    index_path = os.path.join(WORKSPACE, "sec/a_case_index.tex")
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^\s*([MIRX\w]+)\s*&\s*(.*?)\s*&\s*([CFSR])\s*&\s*([^&]+)\s*&\s*([^&]+)\s*&\s*([^&]+)\s*&\s*([^&]+)\s*&\s*\\citep\{([^}]+)\}\s*&\s*(.*?)\s*(?:\\\\|$)', line)
                if m:
                    gid, rank_raw, ptype, desc, author, platform, date, key, code_col = m.groups()
                    gid = gid.strip()
                    key = key.strip()
                    if gid not in cases:
                        url = bib_urls.get(key) or bib_urls.get(tiles.get(gid, {}).get("key")) or "#"
                        code_m = re.search(r"\\href\{([^}]+)\}\{([^}]+)\}", code_col)
                        code_url = code_m.group(1) if code_m else extra_code_urls.get(gid, "")
                        cases[gid] = {
                            "id": gid,
                            "key": key,
                            "rank_raw": rank_raw.strip(),
                            "desc": clean_desc_text(desc),
                            "author": author.strip().replace(r"\_", "_"),
                            "platform": platform.strip(),
                            "date": date.strip(),
                            "url": url,
                            "code_url": code_url
                        }
                        
    # Fallback for any tile from tiles.json not in case_index
    for gid, tinfo in tiles.items():
        if gid not in cases:
            key = tinfo.get("key")
            url = bib_urls.get(key, "#")
            cases[gid] = {
                "id": gid,
                "key": key,
                "desc": f"Case study {gid}",
                "author": "Community Contributor",
                "platform": "Showcase",
                "date": "2026",
                "url": url,
                "code_url": extra_code_urls.get(gid, "")
            }
            
    # For any cases in cases that still don't have url, try tiles key
    for gid, c in cases.items():
        if not c.get("url") or c.get("url") == "#":
            key = tiles.get(gid, {}).get("key")
            if key and key in bib_urls:
                c["url"] = bib_urls[key]
        if not c.get("code_url") and gid in extra_code_urls:
            c["code_url"] = extra_code_urls[gid]
                
    return cases


# Ground-truth mapping extracted directly from main.aux
LABEL_DATA = {
    # Figures
    "fig:roadmap": ("Figure", "1"),
    "fig:loop": ("Figure", "2"),
    "fig:gallery-3d": ("Figure", "3"),
    "fig:gallery-3d-b": ("Figure", "4"),
    "fig:detail-3d": ("Figure", "5"),
    "fig:gallery-cad": ("Figure", "6"),
    "fig:detail-cad": ("Figure", "7"),
    "fig:gallery-robot": ("Figure", "8"),
    "fig:detail-robot": ("Figure", "9"),
    
    # Tables
    "tab:agentic-tools": ("Table", "1"),
    "tab:workflow-comparison": ("Table", "2"),
    "tab:eval-3d": ("Table", "3"),
    "tab:eval-robot": ("Table", "4"),
    "tab:speed": ("Table", "5"),
    "tab:eval-protocols": ("Table", "6"),
    "tab:index": ("Table", "7"),
    
    # Sections
    "sec:summary": ("Executive Summary", ""),
    "sec:intro": ("Section", "1"),
    "sec:intro-observation": ("Section", "1"),
    "sec:intro-overview": ("Section", "1"),
    "sec:intro-related": ("Section", "1.1"),
    "sec:technology": ("Section", "2"),
    "sec:tech-applications": ("Section", "2.1"),
    "sec:tech-computer-use": ("Section", "2.1"),
    "sec:tech-robot-interfaces": ("Section", "2.2"),
    "sec:tech-icl": ("Section", "2.3"),
    "sec:tech-regimes": ("Section", "2.4"),
    "sec:capabilities": ("Section", "3"),
    "sec:cap-3d": ("Section", "3.1"),
    "sec:cap-cad": ("Section", "3.2"),
    "sec:cap-robot": ("Section", "3.3"),
    "sec:cap-animation": ("Section", "3.4"),
    "sec:evaluation": ("Section", "4"),
    "sec:eval-3d": ("Section", "4.1"),
    "sec:eval-robot": ("Section", "4.2"),
    "sec:eval-demonstrations": ("Section", "4.3"),
    "sec:eval-generations": ("Section", "4.4"),
    "sec:eval-field": ("Section", "4.5"),
    "sec:eval-attribution": ("Section", "4.6"),
    "sec:opportunities": ("Section", "5"),
    "sec:opp-artifacts": ("Section", "5.1"),
    "sec:opp-realtosim": ("Section", "5.2"),
    "sec:opp-offline": ("Section", "5.3"),
    "sec:opp-evaluation": ("Section", "5.4"),
    "sec:opp-access": ("Section", "5.5"),
    "sec:risks": ("Section", "6"),
    "sec:risk-reliability": ("Section", "6.1"),
    "sec:risk-speed": ("Section", "6.2"),
    "sec:risk-engineering": ("Section", "6.3"),
    "sec:risk-safety": ("Section", "6.4"),
    "sec:risk-provenance": ("Section", "6.5"),
    "sec:risk-ethics": ("Section", "6.6"),
    "sec:risk-assessment": ("Section", "6.7"),
    "sec:recommendations": ("Section", "7"),
    "sec:conclusion": ("Section", "8"),
    "sec:intro-scope": ("Section", "9"),
    "sec:intro-methods": ("Section", "9"),
    
    # Appendices
    "app:eval-protocols": ("Appendix", "A"),
    "app:archive-notes": ("Appendix", "B"),
    "app:cases": ("Appendix", "C"),
}

PLURAL_NOUNS = {
    "Figure": "Figures",
    "Table": "Tables",
    "Section": "Sections",
    "Appendix": "Appendices",
}

def format_refs(keys_str, preceding_text=""):
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    if not keys:
        return ""
    clean_prec = re.sub(r"[\s\u00a0]+", " ", preceding_text).strip()
    has_preceding_noun = False
    for noun in ["Figure", "Table", "Section", "Appendix"]:
        if re.search(r"\b" + noun + r"s?$", clean_prec, re.IGNORECASE):
            has_preceding_noun = True
            break
            
    by_noun = []
    curr_noun = None
    curr_items = []
    for k in keys:
        info = LABEL_DATA.get(k)
        if not info:
            noun, num = "Reference", k
        else:
            noun, num = info
        if noun == curr_noun:
            curr_items.append((k, num))
        else:
            if curr_items:
                by_noun.append((curr_noun, curr_items))
            curr_noun = noun
            curr_items = [(k, num)]
    if curr_items:
        by_noun.append((curr_noun, curr_items))
        
    noun_phrases = []
    for noun, items in by_noun:
        links = [f'<a href="#{k}" class="academic-ref-link">{num}</a>' if num else f'<a href="#{k}" class="academic-ref-link">{noun}</a>' for k, num in items]
        if len(links) == 1:
            item_noun = noun
            links_str = links[0]
        elif len(links) == 2:
            item_noun = PLURAL_NOUNS.get(noun, noun + "s")
            links_str = f"{links[0]} and {links[1]}"
        else:
            item_noun = PLURAL_NOUNS.get(noun, noun + "s")
            links_str = ", ".join(links[:-1]) + f", and {links[-1]}"
            
        if has_preceding_noun and len(by_noun) == 1:
            noun_phrases.append(links_str)
        else:
            if all(num == "" for _, num in items):
                noun_phrases.append(links_str)
            else:
                noun_phrases.append(f"{item_noun} {links_str}")
            
    if len(noun_phrases) == 1:
        return noun_phrases[0]
    elif len(noun_phrases) == 2:
        return f"{noun_phrases[0]} and {noun_phrases[1]}"
    else:
        return ", ".join(noun_phrases[:-1]) + f", and {noun_phrases[-1]}"

def resolve_latex_refs(html):
    # 1. Transform Pandoc reference tags
    tag_pattern = re.compile(r'<a\s+[^>]*href=\"[^\"]*\"[^>]*data-reference=\"([^\"]+)\"[^>]*>.*?</a>', re.DOTALL)
    pos = 0
    res = []
    for m in tag_pattern.finditer(html):
        start, end = m.span()
        res.append(html[pos:start])
        keys = m.group(1)
        preceding = html[max(0, start - 40):start]
        replacement = format_refs(keys, preceding)
        res.append(replacement)
        pos = end
    res.append(html[pos:])
    html = "".join(res)
    
    # 2. Catch any stray unlinked raw brackets like [fig:foo] or [sec:bar]
    def replace_stray_bracket(m):
        keys = m.group(1)
        return format_refs(keys, "")
    html = re.sub(r'\[((?:fig|tab|sec|app):[^\]]+)\]', replace_stray_bracket, html)
    
    # 3. Clean up Table captions to ensure bold numbering
    table_captions = {
        "tab:agentic-tools": "Table 1",
        "tab:workflow-comparison": "Table 2",
        "tab:eval-3d": "Table 3",
        "tab:eval-robot": "Table 4",
        "tab:speed": "Table 5",
        "tab:eval-protocols": "Table 6",
        "tab:index": "Table 7",
    }
    for tab_id, tab_label in table_captions.items():
        pattern = re.compile(rf'(<div id="{tab_id}"[^>]*>\s*<table[^>]*>\s*<caption>)(.*?)</caption>', re.DOTALL)
        m = pattern.search(html)
        if m:
            open_tag = m.group(1)
            cap_body = m.group(2).strip()
            if not cap_body.startswith(f"<strong>{tab_label}:</strong>") and not cap_body.startswith(f"{tab_label}:"):
                new_cap = f"{open_tag}<strong>{tab_label}:</strong> {cap_body}</caption>"
                html = html[:m.start()] + new_cap + html[m.end():]
                
    # 4. Standardize appendix headings
    html = re.sub(
        r'<h1[^>]*id="app:eval-protocols"[^>]*>\s*<span class="header-section-number">[^<]+</span>\s*(.*?)</h1>',
        r'<h1 id="app:eval-protocols"><span class="header-section-number">Appendix A ·</span> \1</h1>',
        html
    )
    html = re.sub(
        r'<h1[^>]*id="app:archive-notes"[^>]*>\s*<span class="header-section-number">[^<]+</span>\s*(.*?)</h1>',
        r'<h1 id="app:archive-notes"><span class="header-section-number">Appendix B ·</span> \1</h1>',
        html
    )
    
    return html

def build_appendix_c_html(bib_urls, gallery_items=None):
    if gallery_items is None:
        gallery_path = os.path.join(WORKSPACE, "website/assets/gallery.json")
        if os.path.exists(gallery_path):
            with open(gallery_path, encoding="utf-8") as f:
                gallery_items = json.load(f)
        else:
            gallery_items = []
    rows = []
    index_path = os.path.join(WORKSPACE, "sec/a_case_index.tex")
    
    rank1_gids = {"M28", "M42", "M48", "R01", "R03", "R04", "R07", "R08", "R13", "R14", "R18", "R29", "R30"}
    rank2_gids = {"I01", "I09", "M29", "M36", "M44", "M50", "M63", "M64", "M75", "M76", "M78", "M82"}
    extra_code_urls = {
        "M28": "https://github.com/emollick/abyssal-living-deep",
        "M42": "https://github.com/per-simmons/blender-production",
        "M48": "https://github.com/openretriever/retriever",
        "R01": "https://github.com/robocurve/inspect-robots",
        "R03": "https://github.com/NVlabs/ENPIRE",
        "R04": "https://github.com/robocurve/stationerybench",
        "R07": "https://github.com/RoboDojo-Benchmark/RoboDojo",
        "R08": "https://github.com/huggingface/lerobot",
        "R13": "https://github.com/robocurve/roboharm",
        "R14": "https://github.com/allenai/molmoact2/tree/main/sim_eval",
        "R18": "https://github.com/Hu-xiao-max/dexgpt",
        "R29": "https://github.com/anonymous-report-421/GPT-as-Policy",
        "R30": "https://github.com/nftechie/misalignment/tree/main/experiments/001",
    }
    
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\s*([MIRX\w]+)\s*&\s*(.*?)\s*&\s*([CFSR])\s*&\s*([^&]+)\s*&\s*([^&]+)\s*&\s*([^&]+)\s*&\s*([^&]+)\s*&\s*\\citep\{([^}]+)\}\s*&\s*(.*?)\s*(?:\\\\|$)", line)
                if m:
                    gid, rank_raw, ptype, desc, author, platform, date, cite_key, code_col = m.groups()
                    gid = gid.strip()
                    url = bib_urls.get(cite_key, "#")
                    code_match = re.search(r"\\href\{([^}]+)\}\{([^}]+)\}", code_col)
                    code_url = code_match.group(1) if code_match else extra_code_urls.get(gid, "")
                    code_label = code_match.group(2) if code_match else ("code" if code_url else "")
                    
                    if "1" in rank_raw or gid in rank1_gids:
                        rank_num = 1
                        rank_badge = '<span class="badge-rank rank-1" title="Rank 1: Full Reproducibility (Demo + Implementation Code)">Rank 1 · Code</span>'
                    elif "2" in rank_raw or gid in rank2_gids:
                        rank_num = 2
                        rank_badge = '<span class="badge-rank rank-2" title="Rank 2: Interactive Verification (Demo + Interactive Web Link)">Rank 2 · Interactive</span>'
                    else:
                        rank_num = 3
                        rank_badge = '<span class="badge-rank rank-3" title="Rank 3: Demonstration Only (Demonstration Media Only)">Rank 3 · Demo Only</span>'

                    rows.append({
                        "group": gid,
                        "rank_num": rank_num,
                        "rank_badge": rank_badge,
                        "type": ptype.strip(),
                        "desc": clean_desc_text(desc),
                        "author": author.strip().replace(r"\_", "_"),
                        "platform": platform.strip(),
                        "date": date.strip(),
                        "cite_key": cite_key.strip(),
                        "code_url": code_url,
                        "code_label": code_label,
                        "url": url
                    })

    table_rows_html = []
    for r in rows:
        gid = r["group"]
        rank_badge = r["rank_badge"]
        ptype = r["type"]
        desc = r["desc"]
        author = r["author"]
        plat = r["platform"]
        date = r["date"]
        url = r["url"]
        code_url = r["code_url"]
        code_label = r["code_label"]
        rank_num = r["rank_num"]

        if url and url != "#":
            desc_html = f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="post-link" title="Open source post">{desc} ↗</a>'
            plat_html = f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="post-platform-link">{plat}</a>'
        else:
            desc_html = desc
            plat_html = plat

        if code_url:
            code_html = f'<a href="{code_url}" target="_blank" rel="noopener noreferrer" class="post-code-link" title="Open verified repository">{code_label or "code"} ↗</a>'
        elif rank_num == 2:
            code_html = f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="post-interactive-link" title="Open interactive web application">interactive demo ↗</a>'
        else:
            code_html = '<span class="text-muted">— (post only)</span>'

        table_rows_html.append(f"""
        <tr>
          <td class="post-gid"><strong>{gid}</strong></td>
          <td class="post-rank">{rank_badge}</td>
          <td class="post-type"><span class="badge-type type-{ptype.lower()}">{ptype}</span></td>
          <td class="post-desc">{desc_html}</td>
          <td class="post-author">{author}</td>
          <td class="post-plat">{plat_html}</td>
          <td class="post-date">{date}</td>
          <td class="post-code">{code_html}</td>
        </tr>
        """)

    tbody = "\n".join(table_rows_html)

    return f"""
    <section class="appendix-section" id="app:cases">
      <h1 class="appendix-heading"><span class="header-section-number">Appendix C ·</span> Index of archived posts</h1>
      <p><a href="#tab:index" class="academic-ref-link">Table 7</a> lists the 190 archived posts in source-list order, systematically classified under our <strong>Evidence Ranking &amp; Reproducibility Hierarchy</strong> across three audit tiers:
      <strong>Rank 1 (Full Reproducibility · Demo + Implementation Code, 26 posts / 13 groups)</strong>,
      <strong>Rank 2 (Interactive Verification · Demo + Interactive Web Link, 12 posts / 12 groups)</strong>, and
      <strong>Rank 3 (Demonstration Only · Recorded Media Only, 152 posts / 120 groups)</strong>.
      The third column, Type, designates the post role: C = core entry, F = technical follow-up, S = supplementary entry, R = repost or commentary. The Code / Demo column provides direct links to verified code repositories or interactive web applications where released.</p>

      <div class="gallery-callout-panel">
        <div class="callout-header">
          <span class="callout-tag">Interactive Archive Explorer</span>
          <h4>Explore All {len(gallery_items)} Showcases Filtered by Evidence Rank</h4>
        </div>
        <p>In addition to the printed registry below, the web portal provides an interactive tile gallery with instant filtering by Evidence Rank (Rank 1 Code, Rank 2 Interactive, Rank 3 Demo Only), domain scope (3D, CAD, Robotics, Animation), keyword search, and media lightboxes. All primary demonstration media, runnable reproduction harnesses, and benchmark datasets are publicly archived and continuously maintained in the companion open-source repository: <a href="https://github.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics" target="_blank" rel="noopener noreferrer" style="color: var(--mit-red); font-weight: 600; text-decoration: underline;">Frank-ZY-Dou/awesome-ai-3d-modeling-robotics ↗</a>.</p>
        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.75rem;">
          <button class="btn-callout-switch" onclick="switchView('view-gallery');">
            <span>Explore Showcases in Interactive Gallery →</span>
          </button>
          <a href="https://github.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics" target="_blank" rel="noopener noreferrer" class="btn-callout-switch" style="background: transparent; color: var(--ink-primary); border: 1px solid var(--border-line); text-decoration: none;">
            <span>Open Repository on GitHub ↗</span>
          </a>
        </div>
      </div>

      <div class="academic-table-card" id="tab:index">
        <div class="table-caption"><strong>Table 7: Index of the 190 archived posts, classified by Evidence Ranking.</strong> Type: C = core entry, F = technical follow-up, S = supplementary entry, R = repost or commentary. Total 190 records spanning 145 archival groups.</div>
        <div class="table-scroll-container">
          <table class="academic-table post-index-table">
            <thead>
              <tr>
                <th style="width: 65px;">Group</th>
                <th style="width: 135px;">Evidence Rank</th>
                <th style="width: 55px;">Type</th>
                <th>Post Description / Excerpt</th>
                <th style="width: 150px;">Author</th>
                <th style="width: 90px;">Platform</th>
                <th style="width: 95px;">Date</th>
                <th style="width: 110px;">Code / Demo</th>
              </tr>
            </thead>
            <tbody>
              {tbody}
            </tbody>
          </table>
        </div>
      </div>
    </section>
    """

def fetch_awesome_readme():
    url = f"https://raw.githubusercontent.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics/main/README.md?_t={int(time.time())}"
    cached_path = os.path.join(WEBSITE_DIR, "awesome_readme.md")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            with open(cached_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Successfully fetched fresh README.md from awesome repository!")
            return content
    except Exception as e:
        print(f"Warning: Could not fetch remote README.md ({e}), falling back to local copy.")
        if os.path.exists(cached_path):
            with open(cached_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

def get_gallery_items(cases, readme_text=None):
    if not readme_text:
        readme_text = fetch_awesome_readme()
        if not readme_text:
            cached_path = os.path.join(WEBSITE_DIR, "awesome_readme.md")
            if os.path.exists(cached_path):
                with open(cached_path, 'r', encoding='utf-8') as f:
                    readme_text = f.read()

    RAW_GITHUB_PAGES = "https://frank-zy-dou.github.io/awesome-ai-3d-modeling-robotics/"
    RAW_GITHUB_BASE = "https://raw.githubusercontent.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics/main/"
    sections = re.split(r"\n##\s+", readme_text)
    items = []
    field_keys = ["Model:", "Code:", "Demo:", "Tools:", "Archived copy:"]

    for sec in sections:
        sec_lines = sec.strip().split("\n")
        sec_title = sec_lines[0].strip()
        domain = None
        if "3D Modeling" in sec_title:
            domain = "3d"
        elif "Industrial Design" in sec_title or "CAD" in sec_title:
            domain = "cad"
        elif "Robot Control" in sec_title:
            domain = "robotics"
        elif "Animation" in sec_title:
            domain = "animation"
        if not domain:
            continue

        # Subsections within the domain
        subsections = re.findall(r"(### [^\n]+)(.*?)(?=\n### |\n## |\Z)", sec, re.DOTALL)
        for sub_header, sub_body in subsections:
            sub_title = re.sub(r"^###\s+", "", sub_header).strip()
            rows = re.findall(r"^\|\s*<a name=\"case-([^\"]+)\"></a>\s*(.*?)\s*\|\s*(.*?)\s*\|$", sub_body, re.MULTILINE)
            for cid, preview_html, desc_cell in rows:
                gid = cid.upper()
                
                # 1. Preview media
                img_m = re.search(r"<img\s+src=\"([^\"]+)\"", preview_html)
                rel_img = img_m.group(1) if img_m else ""
                
                href_m = re.search(r"<a\s+href=\"([^\"]+)\"", preview_html)
                preview_href = href_m.group(1) if href_m else ""
                
                # 2. Parse desc_cell lines
                parts = [p.strip() for p in desc_cell.split("<br>") if p.strip()]
                title = re.sub(r"^\*\*(.*?)\*\*$", r"\1", parts[0]).strip() if parts else f"Case {gid}"
                
                author_raw = parts[1] if len(parts) > 1 else ""
                author_m = re.search(r"\[(.*?)\]\((.*?)\)", author_raw)
                if author_m:
                    author = author_m.group(1).strip()
                    source_url = author_m.group(2).strip()
                else:
                    author = author_raw.split(",")[0].strip() or "Community Contributor"
                    source_url = preview_href or "#"
                    
                platform = "X"
                if "linkedin.com" in source_url:
                    platform = "LinkedIn"
                elif "youtube.com" in source_url or "youtu.be" in source_url:
                    platform = "YouTube"
                elif "x.com" in source_url or "twitter.com" in source_url:
                    platform = "X"
                    
                # 3. Description text (the commentary / notes before the field line)
                desc = ""
                for p in parts[2:]:
                    if not any(k in p for k in ["Model:", "Code:", "Demo:", "Tools:", "Archived copy:", "Follow-up:", "Also shared by:", "Links:"]):
                        desc = p
                        break
                if not desc:
                    desc = title
                    
                # 4. Strict Field-Based Parsing (do NOT split by " · ")
                model_parts = [p for p in parts if "Model:" in p]
                model_line = model_parts[0] if model_parts else ""
                
                fields = {}
                if model_line:
                    found_keys = []
                    for k in field_keys:
                        pos = model_line.find(k)
                        if pos != -1:
                            found_keys.append((pos, k))
                    found_keys.sort(key=lambda x: x[0])
                    
                    for i, (pos, k) in enumerate(found_keys):
                        start = pos + len(k)
                        end = found_keys[i+1][0] if i + 1 < len(found_keys) else len(model_line)
                        raw_val = model_line[start:end].strip()
                        raw_val = re.sub(r"\s*·\s*$", "", raw_val).strip()
                        fields[k.rstrip(":")] = raw_val
                        
                # Extract code url & label
                code_url = ""
                code_label = "Code"
                code_val = fields.get("Code", "")
                if code_val:
                    cm = re.search(r"\[(.*?)\]\((.*?)\)", code_val)
                    if cm:
                        code_label = cm.group(1).strip()
                        code_url = cm.group(2).strip()
                        
                # Extract demo url & label
                demo_url = ""
                demo_label = "Interactive Demo"
                demo_val = fields.get("Demo", "")
                if demo_val:
                    dm = re.search(r"\[(.*?)\]\((.*?)\)", demo_val)
                    if dm:
                        demo_label = dm.group(1).strip()
                        demo_url = dm.group(2).strip()
                        
                model_name = fields.get("Model", "")
                tools_name = fields.get("Tools", "")
                archived_val = fields.get("Archived copy", "")
                
                # Extract video url
                video_url = ""
                if preview_href.endswith(".mp4"):
                    video_url = preview_href
                elif archived_val:
                    vm = re.search(r"\((https://[^\)]+\.mp4)\)", archived_val)
                    if vm:
                        video_url = vm.group(1).strip()
                        
                # Rank determination:
                # 有 Code: 是第一档，只有 Demo: 是第二档，两者都没有是第三档
                if code_url:
                    rank_num = 1
                    rank = "rank-1"
                    rank_label = "RANK 1 · CODE"
                    rank_title = "Rank 1: Demo + Implementation Code"
                elif demo_url:
                    rank_num = 2
                    rank = "rank-2"
                    rank_label = "RANK 2 · INTERACTIVE"
                    rank_title = "Rank 2: Demo + Interactive Web Link"
                else:
                    rank_num = 3
                    rank = "rank-3"
                    rank_label = "RANK 3 · DEMO ONLY"
                    rank_title = "Rank 3: Demonstration Media Only"
                    
                # Image handling
                local_img = f"assets/gallery/{cid.lower()}.jpg"
                if os.path.exists(os.path.join(WEBSITE_DIR, local_img)):
                    display_img = local_img
                elif rel_img:
                    display_img = RAW_GITHUB_PAGES + rel_img
                else:
                    display_img = "assets/gallery/m01.jpg"
                    
                remote_fallback_img = RAW_GITHUB_PAGES + rel_img if rel_img else display_img
                
                items.append({
                    "order_index": len(items),
                    "id": gid,
                    "domain": domain,
                    "subsection": sub_title,
                    "rank_num": rank_num,
                    "rank": rank,
                    "rank_label": rank_label,
                    "rank_title": rank_title,
                    "title": title,
                    "author": author,
                    "source_url": source_url,
                    "platform": platform,
                    "desc": desc,
                    "img_url": display_img,
                    "remote_img": remote_fallback_img,
                    "rel_img": rel_img,
                    "video_url": video_url,
                    "code_url": code_url,
                    "code_label": code_label,
                    "demo_url": demo_url,
                    "demo_label": demo_label,
                    "model": model_name,
                    "tools": tools_name
                })

    # Curated order preserved: "README 里每个小节的顺序已经是按档位排好的，网站照原顺序展示即可。"
    # DO NOT sort globally by rank_num.
    try:
        with open(os.path.join(WEBSITE_DIR, "assets/gallery.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
    except Exception as e:
        print("Warning: could not write gallery.json:", e)

    return items

def parse_benchmarks_section(readme_text):
    m = re.search(r'## Benchmarks\s*(.*?)(?=\n## |\Z)', readme_text, re.DOTALL)
    if not m:
        return "", "", "", ""
    
    bm_sec = m.group(1)
    subsecs = re.split(r'\n###\s+', bm_sec)
    intro_raw = subsecs[0].strip()
    intro = re.sub(r'with additions through \d{4}-\d{2}-\d{2}\.?', 'with additions from recent evaluations.', intro_raw)
    intro = re.sub(r'as of \d{4}-\d{2}-\d{2}', 'in recent evaluations', intro)

    def format_table(table_text):
        lines = [l.strip() for l in table_text.strip().split('\n') if l.strip().startswith('|')]
        if len(lines) < 3:
            return ""
        
        headers = [c.strip() for c in lines[0].split('|')[1:-1]]
        html = ['<table class="academic-table benchmark-table">']
        html.append('  <thead><tr>')
        for h in headers:
            html.append(f'    <th>{h}</th>')
        html.append('  </tr></thead>')
        html.append('  <tbody>')
        
        for row_line in lines[2:]:
            cols = [c.strip() for c in row_line.split('|')[1:-1]]
            if not cols:
                continue
            html.append('    <tr>')
            for idx, c in enumerate(cols):
                c_clean = re.sub(r'as of \d{4}-\d{2}-\d{2}', 'in recent evaluations', c)
                c_html = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer" class="academic-link">\1 ↗</a>', c_clean)
                if idx == 0:
                    html.append(f'      <td><strong>{c_html}</strong></td>')
                elif idx == 2:
                    html.append(f'      <td class="top-val">{c_html}</td>')
                elif idx == len(cols) - 1:
                    html.append(f'      <td class="benchmark-source-cell">{c_html}</td>')
                else:
                    html.append(f'      <td>{c_html}</td>')
            html.append('    </tr>')
            
        html.append('  </tbody>')
        html.append('</table>')
        return "\n".join(html)

    robotics_html = ""
    cad_html = ""
    notes_html = ""

    for s in subsecs[1:]:
        lines = s.strip().split('\n')
        sub_title = lines[0].strip()
        body = "\n".join(lines[1:])
        
        if "Robotics" in sub_title or "embodied" in sub_title:
            robotics_html = format_table(body)
        elif "3D" in sub_title or "CAD" in sub_title or "spatial" in sub_title:
            table_part = body
            if "Notes on coverage:" in body:
                parts = body.split("Notes on coverage:")
                table_part = parts[0]
                raw_notes = parts[1].strip()
                note_items = [re.sub(r'^\s*-\s*', '', l.strip()) for l in raw_notes.split('\n') if l.strip().startswith('-')]
                note_lis = []
                for ni in note_items:
                    ni_clean = re.sub(r'as of \d{4}-\d{2}-\d{2}', 'in recent evaluations', ni)
                    ni_html = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer" class="academic-link">\1 ↗</a>', ni_clean)
                    note_lis.append(f'<li>{ni_html}</li>')
                notes_html = "\n".join(note_lis)
            cad_html = format_table(table_part)

    return intro, robotics_html, cad_html, notes_html

def build_benchmarks_section_html(readme_text):
    intro, robotics_table, cad_table, notes_html = parse_benchmarks_section(readme_text)
    
    html = f'''
        <!-- Quantitative Benchmark Section -->
        <div id="benchmarks-section">
          <a id="benchmarks"></a>
          <h3 class="subsection-title" style="margin-top:2.5rem;">2. Quantitative Benchmark Leaderboards &amp; Standardized Evaluations</h3>
          <p class="panel-section-desc" style="margin-bottom: 1.5rem;">
            {intro}
          </p>

          <h4 style="font-family: var(--font-sans); font-size: 1.05rem; font-weight: 700; color: var(--ink-primary); margin: 1.5rem 0 0.75rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
            <span>2.1 Robotics &amp; Embodied Control Evaluations (17 Benchmark Suites)</span>
            <span style="font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 4px; background: #e0f2fe; color: #0369a1;">Isaac Sim · MuJoCo · Real Hardware</span>
          </h4>
          <div class="table-container" style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin-bottom: 2rem;">
            {robotics_table}
          </div>

          <h4 style="font-family: var(--font-sans); font-size: 1.05rem; font-weight: 700; color: var(--ink-primary); margin: 2.25rem 0 0.75rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
            <span>2.2 3D Reconstruction, CAD &amp; Spatial Intelligence (5 Benchmark Suites)</span>
            <span style="font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 4px; background: #fef3c7; color: #b45309;">CadQuery · B-rep · Spatial VQA</span>
          </h4>
          <div class="table-container" style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin-bottom: 2rem;">
            {cad_table}
          </div>

          <div class="benchmark-coverage-card" style="margin-top: 1.75rem; padding: 1.25rem 1.5rem; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-left: 4px solid var(--mit-red); border-radius: 6px;">
            <h5 style="margin: 0 0 0.5rem; font-size: 0.95rem; font-weight: 700; color: var(--ink-primary); font-family: var(--font-sans);">
              Coverage &amp; Evaluation Caveats
            </h5>
            <ul style="margin: 0; padding-left: 1.25rem; color: var(--ink-secondary); font-size: 0.88rem; line-height: 1.6;">
              {notes_html}
            </ul>
          </div>
        </div>
    '''
    return html

def remove_macro(text, name):
    target = "\\" + name + "{"
    while target in text:
        start = text.find(target)
        idx = start + len(target)
        depth = 1
        while idx < len(text) and depth > 0:
            if text[idx] == "{":
                depth += 1
            elif text[idx] == "}":
                depth -= 1
            idx += 1
        text = text[:start] + text[idx:]
    return text

def unwrap_macro(text, name):
    target = "\\" + name + "{"
    while target in text:
        start = text.find(target)
        idx = start + len(target)
        depth = 1
        inner_start = idx
        while idx < len(text) and depth > 0:
            if text[idx] == "{":
                depth += 1
            elif text[idx] == "}":
                depth -= 1
            idx += 1
        inner_content = text[inner_start:idx-1]
        text = text[:start] + inner_content + text[idx:]
    return text

def enhance_academic_tables(content):
    pattern = re.compile(
        r'<div id="(tab:[^"]+)">\s*<table[^>]*>(.*?)</table>\s*</div>(?:\s*<div class="minipage">\s*(<p><em>Human involvement[^<]+</em>.*?</p>)\s*</div>)?',
        re.DOTALL
    )

    def repl(m):
        tab_id = m.group(1)
        inner = m.group(2)
        note_html = m.group(3)
        caption_match = re.search(r'<caption>(.*?)</caption>', inner, re.DOTALL)
        caption_html = caption_match.group(1).strip() if caption_match else ""
        if caption_html and not re.match(r'^\s*<strong>Table', caption_html, re.I):
            label_info = LABEL_DATA.get(tab_id)
            if label_info:
                caption_html = f"<strong>{label_info[0]} {label_info[1]}:</strong> {caption_html}"
        inner = re.sub(r'<caption>.*?</caption>', '', inner, count=1, flags=re.DOTALL)
        inner = re.sub(r'<colgroup>.*?</colgroup>', '', inner, flags=re.DOTALL)
        inner = inner.strip()
        note_block = f'<div class="table-card-note">{note_html}</div>' if note_html else ''
        return f'''<div class="academic-table-card" id="{tab_id}">
  <div class="table-caption">{caption_html}</div>
  <div class="table-scroll-container">
    <table class="academic-table">
      {inner}
    </table>
  </div>
  {note_block}
</div>'''

    return pattern.sub(repl, content)

def build_latex_gallery_figure_html(fig_id, fig_num_str, title, tex_file, caption_text, domain_key, gallery_data_by_id):
    tex_path = os.path.join(WORKSPACE, tex_file)
    content = ""
    if os.path.exists(tex_path):
        with open(tex_path, encoding='utf-8') as f:
            content = f.read()

    imgs = re.findall(r'figures/gallery/([^}\s]+)', content)
    cards_html = []
    for img in imgs:
        gid = re.sub(r'\.(jpg|png)$', '', img, flags=re.I).upper()
        item = gallery_data_by_id.get(gid, {})
        author = item.get('author', '')
        title_text = item.get('title', '')
        author_short = author.split('(')[0].strip() if author else gid
        
        cards_html.append(f'''
        <div class="gallery-tile-card" onclick="switchView('view-gallery'); filterGallery('{domain_key}');" title="{gid}: {title_text}">
          <div class="gallery-tile-thumb-wrap">
            <img src="assets/gallery/{img}" alt="{gid}: {title_text}" loading="lazy" class="zoomable">
            <span class="gallery-tile-gid">{gid}</span>
          </div>
          <div class="gallery-tile-meta">
            <div class="gallery-tile-author">{author_short}</div>
            <div class="gallery-tile-title">{title_text}</div>
          </div>
        </div>''')

    cards_str = "\n".join(cards_html)
    return f'''
    <figure class="academic-figure figure-gallery-figure" id="{fig_id}">
      <div class="gallery-tiles-header">
        <div class="gallery-tiles-tag">Archived Case Panel · Figure {fig_num_str}</div>
        <div class="gallery-tiles-count">{len(imgs)} Archived Cases</div>
      </div>
      <div class="gallery-tiles-grid">
        {cards_str}
      </div>
      <figcaption>
        <strong>Figure {fig_num_str}: {title}.</strong> {caption_text}
      </figcaption>
      <div class="gallery-figure-actions">
        <button class="btn-callout-switch" onclick="switchView('view-gallery'); filterGallery('{domain_key}');">
          <span>Explore All {domain_key.upper()} Showcases in Interactive Gallery →</span>
        </button>
      </div>
    </figure>
    '''

def convert_paper_html(bib_urls=None):
    if bib_urls is None:
        bib_urls = parse_bib_urls()

    sections = [
        "sec/0_abstract.tex",
        "sec/0_summary.tex",
        "sec/1_intro.tex",
        "sec/2_interfaces.tex",
        "sec/3_capabilities.tex",
        "sec/4_evaluation.tex",
        "sec/5a_opportunities.tex",
        "sec/5_risks.tex",
        "sec/6_recommendations.tex",
        "sec/7_conclusion.tex",
        "sec/8_methods.tex",
        "sec/a_protocols.tex",
        "sec/a_archive_note.tex",
    ]
    
    combined = ""
    for s in sections:
        sp = os.path.join(WORKSPACE, s)
        with open(sp, encoding="utf-8") as f:
            content = f.read()
            for author in ["Frank", "Aki", "Anna", "Jamie", "Harrison", "Tianyu", "Minghao", "Ben"]:
                content = remove_macro(content, author)
            content = unwrap_macro(content, "revision")
            
            # Map input figures to unique replacement tokens
            content = content.replace(r"\input{figures/fig1_roadmap}", "\n\n@@FIG_ROADMAP@@\n\n")
            content = content.replace(r"\input{figures/fig_loop}", "\n\n@@FIG_LOOP@@\n\n")
            content = content.replace(r"\input{figures/gallery_3d}", "\n\n@@FIG_GALLERY_3D@@\n\n")
            content = content.replace(r"\input{figures/gallery_3d-b}", "\n\n@@FIG_GALLERY_3D_B@@\n\n")
            content = content.replace(r"\input{figures/detail_3d}", "\n\n@@FIG_DETAIL_3D@@\n\n")
            content = content.replace(r"\input{figures/gallery_cad}", "\n\n@@FIG_GALLERY_CAD@@\n\n")
            content = content.replace(r"\input{figures/detail_cad}", "\n\n@@FIG_DETAIL_CAD@@\n\n")
            content = content.replace(r"\input{figures/gallery_robot}", "\n\n@@FIG_GALLERY_ROBOT@@\n\n")
            content = content.replace(r"\input{figures/detail_robot}", "\n\n@@FIG_DETAIL_ROBOT@@\n\n")
            
            if s == "sec/0_abstract.tex":
                content = "\\section*{Abstract}\\label{abstract}\n" + content
                
            combined += f"\n\n% --- {s} ---\n\n" + content
            
    combined = combined.replace(r"\astra", "GPT-6 Astra")
    combined = combined.replace(r"\astra{}", "GPT-6 Astra")
    
    cmd = [
        "pandoc",
        "-f", "latex",
        "-t", "html5",
        "--number-sections",
        "--bibliography", os.path.join(WORKSPACE, "paper.bib"),
        "--bibliography", os.path.join(WORKSPACE, "posts.bib"),
        "--citeproc"
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=WORKSPACE)
    out, err = p.communicate(combined)
    if err:
        print("Pandoc messages:", err[:200])
        
    # Standardize image paths
    out = out.replace("figures/details/", "assets/figures/")
    out = out.replace("figures/gallery/", "assets/gallery/")
    out = out.replace("figures/", "assets/figures/")

    # Clean section numbers from paragraph headers (h4)
    out = re.sub(r'<h4[^>]*>\s*<span[^>]*class="header-section-number"[^>]*>[^<]+</span>\s*', '<h4>', out)
    # Enhance executive keybox callouts with prominent semantic title
    out = re.sub(r'<div class="keybox">\s*<p><span>(.*?)</span></p>', r'<div class="keybox">\n<h3 class="keybox-title">\1</h3>', out)
    # Ensure Section 9 methods anchor matches TOC and preserves sec:intro-scope
    out = out.replace('id="sec:intro-scope"', 'id="sec:intro-methods"><span id="sec:intro-scope"></span>')
    # Clean run-in lead paragraphs
    out = out.replace('<p><strong>Source scope.</strong>', '<p class="no-indent"><strong>Source scope.</strong>')
    
    gallery_json_path = os.path.join(WORKSPACE, "website/assets/gallery.json")
    gallery_data_by_id = {}
    if os.path.exists(gallery_json_path):
        try:
            with open(gallery_json_path, encoding="utf-8") as f:
                for item in json.load(f):
                    gallery_data_by_id[item.get("id")] = item
        except Exception as e:
            print("Notice: could not pre-load gallery.json:", e)

    # Define exact semantic HTML figure blocks matching the PDF
    fig_roadmap_html = """
    <figure class="academic-figure figure-main" id="fig:roadmap">
      <div class="figure-img-wrap">
        <img src="assets/figures/fig1_roadmap.svg" alt="Figure 1: Structure of this report" class="zoomable" loading="lazy">
      </div>
      <figcaption>
        <strong>Figure 1: Structure of this report.</strong> Section 2 describes the software interfaces the demonstrations depend on and the difference between offline development and online operation. Section 3 covers 3D modeling, industrial design and CAD, robot control, and animation/motion, outlined in the colors used for the four domains throughout the report. Section 4 presents reconstruction and CAD evaluations before robotics, including comparisons with earlier models and the community interpretations and open questions in Section 4.5; Section 5 sets out the opportunities, Section 6 the risks, limitations, research and ethics questions and the limits of this assessment, and Section 7 the recommendations; Section 9 at the end of the report describes how the archive was built and checked. Box numbers are section numbers.
      </figcaption>
    </figure>
    """

    fig_loop_html = """
    <figure class="academic-figure figure-main" id="fig:loop">
      <div class="figure-img-wrap">
        <img src="assets/figures/fig2_loop.svg" alt="Figure 2: The loop this report analyzes" class="zoomable" loading="lazy">
      </div>
      <figcaption>
        <strong>Figure 2: The loop this report analyzes.</strong> A task and its inputs reach the model, which either decides the next action or writes code; software or a controller executes that decision; and what the interface returns becomes the next input. The three colored boxes name the checks that feedback consists of in each domain, and the execution limits bound how long a loop may run. Whether the loop closes before deployment or during execution separates offline development from online operation, a distinction used throughout Sections 2, 3, and 4. A capability claim reaches only as far as the check that observed it, which is why a valid solid can still fail a design specification and an accurate scene can still be unsuitable for contact simulation.
      </figcaption>
    </figure>
    """

    fig_gallery_3d_html = build_latex_gallery_figure_html(
        "fig:gallery-3d", "3",
        "Gallery of archived 3D modeling groups (panel 1 of 2)",
        "figures/gallery_3d.tex",
        "Gallery of archived 3D modeling groups, panel 1 of 2: 43 tiles here, 90 of the 96 archival groups in this domain overall. One still per group; video frames sampled at 30% of each clip; posted images and YouTube thumbnails used directly; every tile cropped to 16:9. Each tile names the group identifier, the source post and the archive's short title. Stills identify reported outputs; they do not document complete runs or validate the artifacts, and the rights remain with their authors.",
        "3d",
        gallery_data_by_id
    )

    fig_gallery_3d_b_html = build_latex_gallery_figure_html(
        "fig:gallery-3d-b", "4",
        "Gallery of archived 3D modeling groups (panel 2 of 2)",
        "figures/gallery_3d-b.tex",
        "Gallery of archived 3D modeling groups, panel 2 of 2: 47 tiles here, completing the 90 groups shown in the two panels. Stills identify reported outputs; they do not document complete runs or validate the artifacts, and the rights remain with their authors.",
        "3d",
        gallery_data_by_id
    )

    fig_detail_3d_html = """
    <figure class="academic-figure figure-main" id="fig:detail-3d">
      <div class="figure-img-wrap">
        <img src="assets/figures/kitchen_input_output.png" alt="Figure 5: Input and output details from Dou's kitchen viewer" class="zoomable" loading="lazy" style="max-width: 720px;">
      </div>
      <figcaption>
        <strong>Figure 5: Input and output details from Dou’s kitchen viewer (M32)</strong> (Dou, 2026b). The phone-video inset at lower left and modeled scene let the reader compare the refrigerator, counters and island as retained scene objects. The view is cropped from one posted frame. This view does not establish dimensional agreement, complete room reconstruction or validated contact and physical parameters; the author's reported weaknesses in thin and shiny objects, draft objects and room shell remain.
      </figcaption>
    </figure>
    """

    fig_gallery_cad_html = build_latex_gallery_figure_html(
        "fig:gallery-cad", "6",
        "Gallery of archived industrial design and CAD groups",
        "figures/gallery_cad.tex",
        "Gallery of archived industrial design and CAD groups: 17 tiles here, 17 of the 18 archival groups in this domain overall. One still per group; video frames sampled at 30% of each clip; posted images and YouTube thumbnails used directly; every tile cropped to 16:9. Each tile names the group identifier, the source post and the archive's short title. Stills identify reported outputs; they do not document complete runs or validate the artifacts, and the rights remain with their authors.",
        "cad",
        gallery_data_by_id
    )

    fig_detail_cad_html = """
    <figure class="academic-figure figure-main" id="fig:detail-cad">
      <div class="figure-subfigures-grid">
        <div class="subfigure">
          <img src="assets/figures/turbofan_front.jpg" alt="Fan and nacelle" class="zoomable" loading="lazy">
          <div class="subcaption">(a) Fan and nacelle</div>
        </div>
        <div class="subfigure">
          <img src="assets/figures/turbofan_hot_section.jpg" alt="Hot-section cutaway" class="zoomable" loading="lazy">
          <div class="subcaption">(b) Hot-section cutaway</div>
        </div>
      </div>
      <figcaption>
        <strong>Figure 7: A turbofan built as a solid B-rep model from one prompt (I04)</strong> (Varghese, 2026). Varghese connected a GPT-6 Astra (medium) session to the CGM modeling kernel through James Gray's MCP server and asked for a detailed turbofan; he reports “511 solid bodies”, “11,200 faces” and “2,296 blades and vanes”, export to XCGM and STEP, and that “all the bodies pass CGM's BREP checker”, in under 30 minutes. The two images are among the presentation renders the author says the model also produced, so they show the model's own depiction of its output rather than a kernel view. He calls it “an illustrative model, not an OEM design”; B-rep validity and the selected clearance checks he ran do not establish aerodynamic function or manufacturability, and the figures are author-reported.
      </figcaption>
    </figure>
    """

    fig_gallery_robot_html = build_latex_gallery_figure_html(
        "fig:gallery-robot", "8",
        "Gallery of archived robot control groups",
        "figures/gallery_robot.tex",
        "Gallery of archived robot control groups: 29 tiles here, 29 of the 31 archival groups in this domain overall. One still per group; video frames sampled at 30% of each clip; posted images and YouTube thumbnails used directly; every tile cropped to 16:9. Each tile names the group identifier, the source post and the archive's short title. Stills identify reported outputs; they do not document complete runs or validate the artifacts, and the rights remain with their authors.",
        "robotics",
        gallery_data_by_id
    )

    fig_detail_robot_html = """
    <figure class="academic-figure figure-main" id="fig:detail-robot">
      <div class="figure-subfigures-grid">
        <div class="subfigure">
          <img src="assets/figures/enpire_demo.png" alt="Human demonstration" class="zoomable" loading="lazy">
          <div class="subcaption">(a) Human demonstration</div>
        </div>
        <div class="subfigure">
          <img src="assets/figures/enpire_exec.png" alt="Robot execution" class="zoomable" loading="lazy">
          <div class="subcaption">(b) Robot execution, played at 8×</div>
        </div>
      </div>
      <figcaption>
        <strong>Figure 9: Physical in-context learning through the ENPIRE harness (R03)</strong> (Zhang, 2026b). (a) A person places a yellow cup on the table in front of the bimanual arms; (b) the arms reproduce the task, with the source's 8× playback overlay visible. The authors state that the model “outputs target EE and the harness does the IK”, and that the cameras run at 30 Hz while “GPT-6 is queried much less often than that”; the long waits were edited out of the clip. The pair shows the input and the reported output of one run. It does not show the complete run, the number of attempts, or a completion count, and the edited timing means the clip cannot be used to measure model decision latency.
      </figcaption>
    </figure>
    """

    for token, rep in [
        ("@@FIG_ROADMAP@@", fig_roadmap_html),
        ("@@FIG_LOOP@@", fig_loop_html),
        ("@@FIG_GALLERY_3D@@", fig_gallery_3d_html),
        ("@@FIG_GALLERY_3D_B@@", fig_gallery_3d_b_html),
        ("@@FIG_DETAIL_3D@@", fig_detail_3d_html),
        ("@@FIG_GALLERY_CAD@@", fig_gallery_cad_html),
        ("@@FIG_DETAIL_CAD@@", fig_detail_cad_html),
        ("@@FIG_GALLERY_ROBOT@@", fig_gallery_robot_html),
        ("@@FIG_DETAIL_ROBOT@@", fig_detail_robot_html),
    ]:
        out = out.replace(f"<p>{token}</p>", rep)
        out = out.replace(token, rep)

    # Ensure References heading and numbered references list
    if '<div id="refs"' in out:
        ref_matches = list(re.finditer(r'<div id="(ref-[^"]+)" class="csl-entry"[^>]*>', out))
        num_refs = len(ref_matches)

        cite_map = {}
        for i, m in enumerate(ref_matches, 1):
            full_id = m.group(1)
            k = full_id.replace('ref-', '')
            cite_map[k] = i
            cite_map[full_id] = i

        refs_heading = f'<h1 class="unnumbered" id="references">References <span class="ref-count-badge">{num_refs} Citations</span></h1>\n'
        out = out.replace('<div id="refs"', refs_heading + '<div id="refs"')

        ref_counter = 0
        def add_ref_number(match):
            nonlocal ref_counter
            ref_counter += 1
            full_tag = match.group(0)
            return f'{full_tag}\n<span class="csl-num">[{ref_counter}]</span>'

        out = re.sub(r'<div id="ref-[^"]+" class="csl-entry"[^>]*>', add_ref_number, out)

        # Convert in-text citation spans to clickable links jumping to the reference
        pos = 0
        res = []
        while True:
            idx = out.find('<span class="citation"', pos)
            if idx == -1:
                res.append(out[pos:])
                break
            res.append(out[pos:idx])
            
            tag_close = out.find('>', idx)
            if tag_close == -1:
                res.append(out[idx:])
                break
            tag_header = out[idx:tag_close+1]
            cites_match = re.search(r'data-cites="([^"]+)"', tag_header)
            
            content_start = tag_close + 1
            curr = content_start
            depth = 1
            while depth > 0 and curr < len(out):
                next_open = out.find('<span', curr)
                next_close = out.find('</span>', curr)
                if next_close == -1:
                    break
                if next_open != -1 and next_open < next_close:
                    depth += 1
                    curr = next_open + 5
                else:
                    depth -= 1
                    if depth == 0:
                        content_end = next_close
                        curr = next_close + 7
                        break
                    curr = next_close + 7
            
            if depth == 0 and cites_match:
                content = out[content_start:content_end]
                keys = cites_match.group(1).split()
                first_key = keys[0]
                matched_nums = [str(cite_map[k]) for k in keys if k in cite_map]
                if matched_nums:
                    num_label = f"[{', '.join(matched_nums)}]"
                    target_id = f"ref-{first_key}" if not first_key.startswith('ref-') else first_key
                    res.append(f'<a href="#{target_id}" class="citation-link" title="{num_label} View in References">{content}</a>')
                else:
                    res.append(out[idx:curr])
                pos = curr
            else:
                res.append(out[idx:tag_close+1])
                pos = tag_close + 1

        out = "".join(res)
        
    # Append Appendix C before References
    appendix_c_html = build_appendix_c_html(bib_urls)
    if '<div id="refs"' in out:
        out = out.replace('<div id="refs"', appendix_c_html + '\n\n<div id="refs"')
    else:
        out += "\n\n" + appendix_c_html

    # Enhance academic tables to full-width responsive cards with top captions
    out = enhance_academic_tables(out)

    # Resolve all LaTeX cleveref/ref links and human-readable numbers
    out = resolve_latex_refs(out)
    return out

DOMAINS_CONFIG = [
    {
        "id": "3d",
        "badge": "Domain 01",
        "title": "3D Modeling & Spatial Synthesis",
        "short_title": "3D Modeling",
        "desc": "93 community and research showcases exploring automated asset generation, architectural reconstruction, character and material synthesis, world-building, and generative 3D workflows.",
        "sub_short_names": {
            "Architecture and real-world reconstruction": "Architecture & Recon",
            "Vehicles, products and environments": "Vehicles & Environments",
            "Characters and materials": "Characters & Materials",
            "Game assets and playable worlds": "Game Assets & Worlds",
            "Workflows and tooling": "Workflows & Tooling"
        }
    },
    {
        "id": "cad",
        "badge": "Domain 02",
        "title": "Industrial Design & Parametric CAD",
        "short_title": "Industrial Design & CAD",
        "desc": "19 archived showcases covering B-rep solid modeling, feature trees, industrial design drafting, and algorithmic CAD kernel execution.",
        "sub_short_names": {
            "Parametric CAD and solid modeling": "Parametric Solid Modeling",
            "Product design and prototypes": "Product Design & Prototypes",
            "BIM drafting": "BIM Drafting"
        }
    },
    {
        "id": "robotics",
        "badge": "Domain 03",
        "title": "Embodied Robotics & Physical Interaction",
        "short_title": "Embodied Robotics",
        "desc": "33 archived showcases spanning high-precision manipulation, dexterous multi-finger hands, real-to-sim transfer, physics simulation control, and physical safety evaluations.",
        "sub_short_names": {
            "Manipulation evaluations": "Manipulation Evaluations",
            "Personal arms, dexterous hands and unseen robots": "Dexterous Arms & Hands",
            "Learning from demonstration and real-to-sim": "Demo & Real-to-Sim",
            "Simulation control and training, painting, drones and full evaluations": "Simulation & Control",
            "Safety evaluations and claims": "Safety Evaluations"
        }
    },
    {
        "id": "animation",
        "badge": "Domain 04",
        "title": "Animation & Motion Dynamics",
        "short_title": "Animation",
        "desc": "27 archived showcases focusing on character rigging, procedural motion graphics, interactive shaders, and animation-to-video previsualization workflows.",
        "sub_short_names": {
            "Rigging and character animation": "Rigging & Character Motion",
            "Procedural animation and motion graphics": "Procedural Motion Graphics",
            "Interactive and shader animation": "Interactive Shaders",
            "Previsualization and animation-to-video workflows": "Previs & Video Workflows"
        }
    }
]

def slugify(text):
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def render_tile_html(item):
    domain_class = f"cat-{item['domain']}"
    source_url = item.get("source_url", "#")
    has_link = source_url and source_url != "#"
    code_url = item.get("code_url", "")
    demo_url = item.get("demo_url", "")
    video_url = item.get("video_url", "")
    rank_num = item["rank_num"]
    rank_class = item["rank"]
    sub_text = item.get("subsection", "")
    sub_badge = f'<span class="tile-subcat-badge" title="{sub_text}">{sub_text}</span>' if sub_text else ""
    
    if has_link:
        author_html = f'<a href="{source_url}" target="_blank" rel="noopener noreferrer" class="tile-author-link" title="Open original post on {item["platform"]}">{item["author"]} <span class="tile-platform">· {item["platform"]} ↗</span></a>'
        desc_html = f'<a href="{source_url}" target="_blank" rel="noopener noreferrer" class="tile-desc-link" title="Open original post on {item["platform"]}">{item["title"]}</a>'
    else:
        author_html = f'{item["author"]} <span class="tile-platform">· {item["platform"]}</span>'
        desc_html = f'{item["title"]}'

    if sub_badge:
        author_html = f'{author_html} <span class="tile-subcat-sep">·</span> {sub_badge}'

    # Action Buttons per Rank
    if rank_num == 1:
        actions_html = f'''
        <div class="tile-action-btns">
          <a href="{code_url or source_url}" target="_blank" rel="noopener noreferrer" class="tile-btn btn-code" title="View implementation code repository on GitHub">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
            <span>Code</span> ↗
          </a>
          <a href="{source_url}" target="_blank" rel="noopener noreferrer" class="tile-btn btn-post" title="Open source post on {item['platform']}">
            <span>Post</span> ↗
          </a>
        </div>
        '''
    elif rank_num == 2:
        actions_html = f'''
        <div class="tile-action-btns">
          <a href="{demo_url or source_url}" target="_blank" rel="noopener noreferrer" class="tile-btn btn-interactive" title="Inspect interactive 3D web application / viewer">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
            <span>Interactive Demo</span> ↗
          </a>
          <a href="{source_url}" target="_blank" rel="noopener noreferrer" class="tile-btn btn-post" title="Open source post on {item['platform']}">
            <span>Post</span> ↗
          </a>
        </div>
        '''
    else:
        actions_html = f'''
        <div class="tile-action-btns">
          <a href="{source_url}" target="_blank" rel="noopener noreferrer" class="tile-btn btn-post" title="View recorded demonstration on {item['platform']}">
            <span>View Post</span> ↗
          </a>
        </div>
        '''

    safe_title = item['title'].replace("'", "\\'").replace('"', '&quot;')
    safe_desc = item['desc'].replace("'", "\\'").replace('"', '&quot;')
    safe_author = item['author'].replace("'", "\\'").replace('"', '&quot;')
    safe_source = source_url.replace("'", "\\'")
    safe_platform = item['platform'].replace("'", "\\'")
    safe_code = code_url.replace("'", "\\'")
    safe_demo = demo_url.replace("'", "\\'")
    safe_video = video_url.replace("'", "\\'")
    safe_rank_lbl = item['rank_label'].replace("'", "\\'")
    safe_model = item.get('model', '').replace("'", "\\'")
    safe_tools = item.get('tools', '').replace("'", "\\'")
    safe_sub = sub_text.replace("'", "\\'")

    video_badge = '<span class="tile-badge-video" title="Direct video playback available">▶ Video</span>' if video_url else ''
    onclick_js = f"openShowcaseModal('{item['img_url']}', '{item['id']}', '{safe_title}', '{safe_author}', '{safe_source}', '{safe_platform}', '{safe_rank_lbl}', '{rank_class}', '{safe_code}', '{safe_demo}', '{safe_video}', '{safe_model}', '{safe_tools}', '{safe_sub}')"

    remote_fallback = item.get('remote_img', '')
    rel_img_val = item.get('rel_img', '')
    onerror_attr = f' onerror="if(this.src.indexOf(\\\'frank-zy-dou.github.io\\\')===-1 && \\\'{rel_img_val}\\\'){{this.src=\\\'{remote_fallback}\\\';}}"' if rel_img_val else ''

    return f"""
    <div class="gallery-tile {domain_class} {rank_class}" data-domain="{item['domain']}" data-rank="{item['rank']}" data-rank-num="{item['rank_num']}" data-order="{item['order_index']}" data-id="{item['id']}" data-author="{item['author']}" data-desc="{item['title']} {item['desc']}">
      <div class="tile-img-wrap" onclick="{onclick_js}">
        <img src="{item['img_url']}" alt="{item['id']}" loading="lazy"{onerror_attr}>
        <div class="tile-badges-overlay">
          <span class="tile-badge-id">{item['id']}</span>
          <span class="tile-badge-rank {item['rank']}">{item['rank_label']}</span>
        </div>
        {video_badge}
      </div>
      <div class="tile-meta">
        <div class="tile-author">{author_html}</div>
        <div class="tile-desc">{desc_html}</div>
        <div class="tile-footer">{actions_html}</div>
      </div>
    </div>
    """

def build_gallery_sidebar_html(gallery_items):
    grouped = {}
    for item in gallery_items:
        d = item['domain']
        sub = item['subsection']
        grouped.setdefault(d, {}).setdefault(sub, []).append(item)

    sidebar_html = []
    sidebar_html.append('''
    <aside class="gallery-toc-sidebar" id="gallery-toc-sidebar">
      <div class="sidebar-header">
        <div class="sidebar-tag">Showcase Directory</div>
        <div class="sidebar-title">Archive Directory</div>
      </div>
      <a href="#view-gallery" class="sidebar-overview-link" onclick="jumpToGalleryOverview(event)" title="Jump to top filters and overview">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        <span>Overview &amp; Filters</span>
      </a>
      <nav class="sidebar-nav">
    ''')

    for d_cfg in DOMAINS_CONFIG:
        d_id = d_cfg['id']
        d_title = d_cfg['short_title']
        sub_dict = grouped.get(d_id, {})
        d_total = sum(len(items) for items in sub_dict.values())

        sidebar_html.append(f'''
        <div class="sidebar-domain-group" data-domain="{d_id}" id="nav-group-{d_id}">
          <a href="#domain-{d_id}" class="sidebar-domain-head" data-domain="{d_id}" onclick="handleSidebarJump(event, 'domain-{d_id}')">
            <span>{d_title}</span>
            <span class="sidebar-domain-count" id="badge-domain-{d_id}">{d_total}</span>
          </a>
          <ul class="sidebar-sub-list">
        ''')

        for sub_title, items in sub_dict.items():
            slug = slugify(sub_title)
            short_label = d_cfg['sub_short_names'].get(sub_title, sub_title)
            count = len(items)
            sidebar_html.append(f'''
            <li>
              <a href="#sub-{slug}" class="sidebar-sub-link" data-sub-slug="sub-{slug}" data-domain="{d_id}" onclick="handleSidebarJump(event, 'sub-{slug}')">
                <span class="sub-name" title="{sub_title}">{short_label}</span>
                <span class="sub-cnt" id="badge-sub-{slug}">{count}</span>
              </a>
            </li>
            ''')

        sidebar_html.append('''
          </ul>
        </div>
        ''')

    sidebar_html.append('''
      </nav>
      <div class="sidebar-extra-section" style="margin-top: 1.25rem; padding-top: 0.85rem; border-top: 1px solid var(--border-subtle);">
        <a href="#benchmarks" class="sidebar-domain-head" onclick="switchView('view-stats', false); setTimeout(function(){ var el = document.getElementById('benchmarks-section') || document.getElementById('view-stats'); if(el) el.scrollIntoView({behavior:'smooth'}); }, 100); return false;" style="color: var(--mit-red); display: flex; align-items: center; justify-content: space-between; text-decoration: none; font-weight: 600;">
          <span>Quantitative Benchmarks ↗</span>
          <span class="sidebar-domain-count">22 Suites</span>
        </a>
      </div>
    </aside>
    ''')
    return "\n".join(sidebar_html)

def build_gallery_sections_html(gallery_items):
    grouped = {}
    for item in gallery_items:
        d = item['domain']
        sub = item['subsection']
        grouped.setdefault(d, {}).setdefault(sub, []).append(item)

    html = []
    for d_cfg in DOMAINS_CONFIG:
        d_id = d_cfg['id']
        d_badge = d_cfg['badge']
        d_title = d_cfg['title']
        d_desc = d_cfg['desc']
        sub_dict = grouped.get(d_id, {})
        d_total = sum(len(items) for items in sub_dict.values())

        html.append(f'''
        <section class="gallery-domain-section" id="domain-{d_id}" data-domain="{d_id}">
          <div class="gallery-domain-header">
            <div class="domain-header-left">
              <span class="domain-label-badge">{d_badge}</span>
              <h3 class="gallery-domain-title">{d_title}</h3>
            </div>
            <span class="domain-count-badge" id="domain-head-cnt-{d_id}">
              <span class="domain-visible-cnt" id="cnt-domain-{d_id}">{d_total}</span> Showcases
            </span>
          </div>
          <p class="domain-header-desc">{d_desc}</p>
        ''')

        for sub_title, items in sub_dict.items():
            slug = slugify(sub_title)
            tiles_html = [render_tile_html(it) for it in items]
            html.append(f'''
          <div class="gallery-subsection-block" id="sub-{slug}" data-domain="{d_id}" data-sub-slug="sub-{slug}" data-sub="{sub_title}">
            <div class="gallery-subsection-header">
              <h4 class="gallery-subsection-title">{sub_title}</h4>
              <span class="gallery-subsection-badge">
                <span class="sub-visible-cnt" id="cnt-sub-{slug}">{len(items)}</span> cases
              </span>
            </div>
            <div class="gallery-tiles-grid" id="grid-sub-{slug}">
              {"".join(tiles_html)}
            </div>
          </div>
            ''')

        html.append('''
        </section>
        ''')

    return "\n".join(html)

def build_full_html():
    readme_text = fetch_awesome_readme()
    if not readme_text:
        cached_path = os.path.join(WEBSITE_DIR, "awesome_readme.md")
        if os.path.exists(cached_path):
            with open(cached_path, 'r', encoding='utf-8') as f:
                readme_text = f.read()

    bib_urls = parse_bib_urls()
    cases = parse_case_index(bib_urls)
    gallery_items = get_gallery_items(cases, readme_text)
    gallery_sidebar_html = build_gallery_sidebar_html(gallery_items)
    gallery_sections_html = build_gallery_sections_html(gallery_items)
    paper_html = convert_paper_html(bib_urls)
    benchmarks_section_html = build_benchmarks_section_html(readme_text)
    
    total_count = len(gallery_items)
    r1_count = len([x for x in gallery_items if x["rank"] == "rank-1"])
    r2_count = len([x for x in gallery_items if x["rank"] == "rank-2"])
    r3_count = len([x for x in gallery_items if x["rank"] == "rank-3"])
    m_count = len([x for x in gallery_items if x["domain"] == "3d"])
    cad_count = len([x for x in gallery_items if x["domain"] == "cad"])
    robot_count = len([x for x in gallery_items if x["domain"] == "robotics"])
    anim_count = len([x for x in gallery_items if x["domain"] == "animation"])
    
    meta_pdf_citation = '<meta name="citation_pdf_url" content="assets/paper.pdf">' if ENABLE_PDF_DOWNLOAD else ''

    nav_pdf_tab = f'''<button class="view-tab-btn" data-view="view-pdf" role="tab" aria-selected="false">
          {ICON_PDF}
          <span class="tab-label-text"><span class="tab-label-full">Original PDF</span><span class="tab-label-short">PDF</span></span>
        </button>''' if ENABLE_PDF_DOWNLOAD else ''

    nav_pdf_download = f'''<a href="assets/paper.pdf" download="Frontier_3D_Robotics_Paper_MIT.pdf" class="btn-nav-download" title="Download Paper PDF">
          {ICON_DOWNLOAD}
          <span class="nav-btn-text">Download PDF</span>
        </a>''' if ENABLE_PDF_DOWNLOAD else ''

    hero_pdf_pill = f'''<a href="assets/paper.pdf" class="pill-btn primary" download="Frontier_3D_Robotics_Paper_MIT.pdf">
            {ICON_DOWNLOAD}
            <span>Download PDF (76pp)</span>
          </a>''' if ENABLE_PDF_DOWNLOAD else ''

    hero_read_pill_class = "pill-btn" if ENABLE_PDF_DOWNLOAD else "pill-btn primary"

    pdf_section_view = f'''    <!-- ====================================================================
         VIEW 4: PDF READER
         ==================================================================== -->
    <section id="view-pdf" class="view-panel">
      <div class="pdf-container">
        <h2 class="panel-section-title">Full Paper PDF Document & Direct Download</h2>
        <div class="pdf-download-bar">
          <div>
            <strong>Frontier_3D_Robotics_Paper_MIT.pdf</strong>
            <span style="color: var(--ink-muted); margin-left: 0.5rem;">(76 Pages · Complete Survey Draft)</span>
          </div>
          <a href="assets/paper.pdf" download="Frontier_3D_Robotics_Paper_MIT.pdf" class="btn-pill btn-pill-primary">
            {ICON_DOWNLOAD}
            <span>Download Complete PDF</span>
          </a>
        </div>

        <div class="pdf-frame-wrapper">
          <iframe src="assets/paper.pdf" title="Paper PDF Viewer" class="pdf-iframe"></iframe>
        </div>
      </div>
    </section>''' if ENABLE_PDF_DOWNLOAD else ''

    footer_pdf_link = '<a href="assets/paper.pdf" download="Frontier_3D_Robotics_Paper_MIT.pdf">Paper PDF</a> · ' if ENABLE_PDF_DOWNLOAD else ''

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>On the Opportunities and Risks of Frontier Models for 3D Modeling, Computational Design and Robotics | MIT CSAIL</title>
  
  <!-- Academic Citation Metadata -->
  <meta name="citation_title" content="On the Opportunities and Risks of Frontier Models for 3D Modeling, Computational Design and Robotics">
  <meta name="citation_author" content="Dou, Zhiyang">
  <meta name="citation_author" content="Watanabe, Akihisa">
  <meta name="citation_author" content="Deng, Anna">
  <meta name="citation_author" content="Huang, Tianyu">
  <meta name="citation_author" content="Meindl, Jamison">
  <meta name="citation_author" content="Sadalski, Igor">
  <meta name="citation_author" content="Liang, Harrison">
  <meta name="citation_author" content="Guo, Minghao">
  <meta name="citation_author" content="Jones, Benjamin Tod">
  <meta name="citation_author" content="Matusik, Wojciech">
  <meta name="citation_publication_date" content="2026/09/22">
  {meta_pdf_citation}
  
  <meta name="description" content="A systematic empirical survey analyzing over 190 community demonstrations, technical reports, and benchmark evaluations of frontier multimodal models in 3D modeling, parametric CAD, and embodied robotics.">

  <!-- Cloudflare Web Analytics (Optional: paste beacon token from dash.cloudflare.com) -->
  <!-- <script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "YOUR_CLOUDFLARE_BEACON_TOKEN"}}'></script> -->

  <!-- Live Readers & Visitor Counter -->
  <script src="js/reads-counter.js" defer></script>
  
  <!-- SIGGRAPH Font Set (ACM SIGGRAPH / acmart style: Linux Libertine, Linux Biolinum, Inconsolata) -->
  <link rel="preload" href="fonts/LibertinusSerif-Regular.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="fonts/LibertinusSans-Regular.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="fonts/LibertinusSans-Bold.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@400;500;600;700&family=Libertinus+Sans:ital,wght@0,400;0,700;1,400&family=Libertinus+Serif:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">

  <link rel="stylesheet" href="css/style.css?v={int(time.time())}">
</head>
<body id="top">

  <!-- Subtle Reading Progress Bar -->
  <div id="reading-progress"></div>

  <!-- Sticky Top Navigation Bar -->
  <header class="top-nav-bar">
    <div class="nav-inner">
      <div class="nav-brand">
        <a href="#abstract" class="brand-link" title="MIT CSAIL CDFG · Frontier 3D &amp; Robotics Survey">
          <svg class="mit-brand-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 54 28" height="24" width="46" aria-label="MIT Logo">
            <rect x="0" y="0" width="6" height="28" fill="#A31F34"/>
            <rect x="9.6" y="9.6" width="6" height="18.4" fill="#A31F34"/>
            <rect x="19.2" y="0" width="6" height="28" fill="#A31F34"/>
            <rect x="28.8" y="0" width="6" height="8" fill="#A31F34"/>
            <rect x="28.8" y="9.6" width="6" height="18.4" fill="#8A8B8C"/>
            <rect x="38.4" y="0" width="15.6" height="8" fill="#A31F34"/>
            <rect x="38.4" y="9.6" width="6" height="18.4" fill="#A31F34"/>
          </svg>
          <img src="assets/logos/csail_logo_cropped.png" alt="CSAIL" class="csail-brand-logo" height="24">
          <span class="brand-divider"></span>
          <div class="brand-text-lockup">
            <span class="brand-lab-badge">CDFG RESEARCH</span>
            <span class="brand-site-title">Frontier 3D &amp; Robotics Survey</span>
          </div>
        </a>
      </div>

      <!-- Main View Tabs (PDF / HTML / Statistics / Gallery) -->
      <nav class="view-switcher" role="tablist">
        <button class="view-tab-btn active" data-view="view-html" role="tab" aria-selected="true">
          {ICON_PAPER}
          <span class="tab-label-text"><span class="tab-label-full">Full Paper</span><span class="tab-label-short">Paper</span></span>
        </button>
        <button class="view-tab-btn" data-view="view-stats" role="tab" aria-selected="false">
          {ICON_STATS}
          <span class="tab-label-text"><span class="tab-label-full">Benchmark</span><span class="tab-label-short">Benchmark</span></span>
        </button>
        <button class="view-tab-btn" data-view="view-gallery" role="tab" aria-selected="false">
          {ICON_GALLERY}
          <span class="tab-label-text"><span class="tab-label-full">Case Archive</span><span class="tab-label-short">Archive</span></span> <span class="badge-count">{len(gallery_items)}</span>
        </button>
        {nav_pdf_tab}
      </nav>

      <div class="nav-right">
        <div class="nav-reads-badge" id="nav-reads-badge" title="Live Verified Readers of Living Survey">
          <span class="reads-live-dot"></span>
          <span class="reads-num" id="nav-reads-count">0</span>
          <span class="reads-label">Reads</span>
        </div>
        <a href="https://github.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics" target="_blank" rel="noopener noreferrer" class="btn-nav-github" title="Awesome AI for 3D Modeling & Robotics (GitHub)">
          <svg height="15" width="15" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
          <span class="nav-btn-text">GitHub</span>
        </a>
        {nav_pdf_download}
      </div>
    </div>
  </header>

  <!-- Page Main Container -->
  <main class="page-body">

    <!-- ====================================================================
         VIEW 1: HTML FULL PAPER (Unabridged LaTeX Content in HTML5)
         ==================================================================== -->
    <section id="view-html" class="view-panel active">

      <!-- Paper Header Block (Scoped strictly to Full Paper View) -->
      <header class="academic-header">
        <div class="header-pre-tag">MIT CSAIL CDFG · Research Survey Report · Living Survey</div>
        <h1 class="main-paper-title">
          On the Opportunities and Risks of Frontier Models for 3D Modeling, Computational Design and Robotics
        </h1>

        <div class="affiliation-row">
          <span><strong>Computational Design and Fabrication Group (CDFG)</strong> · MIT CSAIL</span>
          <span class="affil-divider">|</span>
          <span class="status-badge">Working Draft & Empirical Horizon Scan</span>
          <span class="affil-divider">|</span>
          <span class="hero-reads-badge" id="hero-reads-badge" title="Empirical Horizon Scan Verified Readers">
            <span class="reads-live-dot"></span>
            <span class="reads-num" id="hero-reads-count">0</span>
            <span>Reads</span>
          </span>
        </div>

        <div class="action-pills-row">
          <a href="https://github.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics" target="_blank" rel="noopener noreferrer" class="pill-btn github-btn" title="Open Repository on GitHub">
            <svg height="15" width="15" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
            <span>GitHub Repository</span>
          </a>
          <button class="{hero_read_pill_class}" onclick="switchView('view-html')">
            {ICON_PAPER}
            <span>Read Full Paper</span>
          </button>
          {hero_pdf_pill}
          <button class="pill-btn" onclick="switchView('view-stats')">
            {ICON_STATS}
            <span>Benchmark Dashboard</span>
          </button>
          <button class="pill-btn" onclick="switchView('view-gallery')">
            {ICON_GALLERY}
            <span>Case Archive ({len(gallery_items)})</span>
          </button>
          <button class="pill-btn" onclick="copyBibtex()">
            {ICON_BIBTEX}
            <span>Copy BibTeX</span>
          </button>
        </div>

        <!-- Core Methodological Framework: Three Foundational Tenets -->
        <section class="core-mission-container">
          <div class="core-mission-header">
            <div class="mission-title-row">
              <div class="mission-title-left">
                <span class="mission-badge">Methodological Scope</span>
                <h2 class="mission-title">Three Core Tenets Guiding This Survey & Archive</h2>
              </div>
              <div class="mission-live-tag" title="This empirical survey and community showcase index are actively maintained and updated.">
                <span class="live-dot"></span>
                <span>Continuously Updated</span>
              </div>
            </div>
            <p class="mission-header-desc">
              This report and content index are continuously updated as frontier foundation model capabilities and community showcases evolve.
            </p>
          </div>

          <div class="mission-pillars-grid">
            <!-- Pillar 1 -->
            <div class="mission-pillar-card">
              <div class="pillar-header">
                <span class="pillar-num">01</span>
                <h4>Platform Motivation</h4>
              </div>
              <div class="pillar-tagline">Horizon Scanning Beyond Publication Lag</div>
              <p>
                In an era where frontier foundation model capabilities evolve so rapidly that traditional academic publishing cycles often lag behind public community breakthroughs, this platform establishes a centralized, high-velocity empirical synthesis repository. We aggregate distributed findings to provide researchers and engineers with timely, comprehensive visibility into ongoing developments across 3D generation, parametric CAD, and embodied robotics—anchoring these observations in rigorous, objective evaluations of strategic opportunities and critical safety boundaries.
              </p>
            </div>

            <!-- Pillar 2 -->
            <div class="mission-pillar-card">
              <div class="pillar-header">
                <span class="pillar-num">02</span>
                <h4>Methodological Stance</h4>
              </div>
              <div class="pillar-tagline">Demonstrations as a Distributed User Study</div>
              <p>
                Rather than treating community posts as anecdotal marketing demonstrations, we analyze the corpus of over 190 publicly documented showcases and developer reports as an extensive, distributed "crowdsourced user study." This framing captures how models operate when prompted across diverse geometry kernels (CGM, Open CASCADE), DCC software (Blender), physics simulators (Isaac Sim, MuJoCo, Genesis), and physical robot hardware—revealing real-world workflow friction, prompt overhead, and boundary failures that static benchmarks miss.
              </p>
            </div>

            <!-- Pillar 3 -->
            <div class="mission-pillar-card">
              <div class="pillar-header">
                <span class="pillar-num">03</span>
                <h4>Objective Evaluation</h4>
              </div>
              <div class="pillar-tagline">Ranking Samples by Open Verifiability</div>
              <p>
                For researchers focused on rigorous empirical evaluation, we conduct an in-depth audit of the openness and reproducibility of each archived post. We rank and stratify samples based on concrete verifiability: whether model weights and codebases are deposited, whether interactive web environments or execution logs are accessible, and whether inference telemetry is disclosed. This grounds our four-tier evidentiary taxonomy (Tier 1–4), cleanly demarcating verified, repeatable milestones from isolated demonstration clips.
              </p>
              <div class="pillar-caveat-note">
                <strong>Empirical Scope &amp; Caveat</strong>
                <span>Through this curated evidence, we aim to provide readers with an immediate window into the latest progress of community developers; nonetheless, comprehensive, fine-grained practical verification warrants further systematic investigation.</span>
              </div>
            </div>
          </div>
        </section>
      </header>
      <div class="html-reader-layout">
        <!-- Floating / Sticky Table of Contents -->
        <aside class="toc-pane">
          <div class="toc-title">Table of Contents</div>
          <ul class="toc-links">
            <li><a href="#abstract">Abstract</a></li>
            <li><a href="#sec:summary">Executive Summary</a></li>
            <li><a href="#sec:intro">1. Introduction</a></li>
            <li><a href="#sec:technology">2. Interfaces & Feedback</a></li>
            <li><a href="#sec:capabilities">3. Emerging Capabilities</a></li>
            <li><a href="#sec:evaluation">4. Empirical Evaluation</a></li>
            <li><a href="#sec:opportunities">5. Strategic Opportunities</a></li>
            <li><a href="#sec:risks">6. Risks & Limitations</a></li>
            <li><a href="#sec:recommendations">7. Recommendations</a></li>
            <li><a href="#sec:conclusion">8. Conclusion</a></li>
            <li><a href="#sec:intro-methods">9. Materials & Methods</a></li>
            <li><a href="#app:eval-protocols">Appendix A: Protocols</a></li>
            <li><a href="#app:archive-notes">Appendix B: Archive Notes</a></li>
            <li><a href="#app:cases">Appendix C: Post Index</a></li>
            <li><a href="#references">References</a></li>
            <li><a href="#citation-box">BibTeX Citation</a></li>
          </ul>
        </aside>

        <!-- Main Full Paper Body (Strictly Centered Measure) -->
        <article class="paper-article">
          <div class="latex-content-body">
            {paper_html}
          </div>
        </article>
      </div>
    </section>

    <!-- ====================================================================
         VIEW 2: STATISTICS DASHBOARD
         ==================================================================== -->
    <section id="view-stats" class="view-panel">
      <div class="stats-container">
        <h2 class="panel-section-title">Empirical Benchmark & Corpus Statistics Dashboard</h2>
        <p class="panel-section-desc">
          A systematic quantitative synthesis summarizing empirical evaluations across 190+ community reports, a four-tier evidentiary classification matrix, and standardized benchmark comparisons in 3D reconstruction, parametric CAD, and embodied robotics.
        </p>

        <!-- Metric Summary Cards -->
        <div class="stat-summary-grid">
          <div class="stat-card">
            <div class="stat-val">172+</div>
            <div class="stat-desc">Archived Technical Showcases &amp; Reports</div>
          </div>
          <div class="stat-card">
            <div class="stat-val">4 Domains</div>
            <div class="stat-desc">3D, CAD, Robotics, and Animation</div>
          </div>
          <div class="stat-card">
            <div class="stat-val">95.9%</div>
            <div class="stat-desc">BenchCAD Mean Voxel IoU (with tools)</div>
          </div>
          <div class="stat-card">
            <div class="stat-val">0.902</div>
            <div class="stat-desc">RoboPianist Twinkle Bimanual Note F1 Score</div>
          </div>
          <div class="stat-card">
            <div class="stat-val">28.97</div>
            <div class="stat-desc">RoboDojo-Sim Score (vs 1.13 GPT-5.5)</div>
          </div>
          <div class="stat-card">
            <div class="stat-val">73.3</div>
            <div class="stat-desc">PhysBrain 1.5 Average Across 28 Embodied Tasks</div>
          </div>
        </div>

        <!-- Domain Distribution Table -->
        <h3 class="subsection-title">1. Domain Coverage &amp; Evidentiary Tier Distribution</h3>
        <table class="academic-table">
          <thead>
            <tr>
              <th>Research Domain</th>
              <th>Showcases</th>
              <th>Share</th>
              <th>Representative Targets / Workflows</th>
              <th>Primary Evidentiary Tier</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>3D Scene &amp; Mesh Modeling</strong></td>
              <td>{m_count} Showcases</td>
              <td>{(m_count / total_count * 100):.1f}%</td>
              <td>Procedural Blender scripts, NeRF/3DGS representations, architectural scans (M01–M88)</td>
              <td><span class="badge-tier tier-1">Tier 1 &amp; 2 (Established / Partial)</span></td>
            </tr>
            <tr>
              <td><strong>Industrial Design &amp; Parametric CAD</strong></td>
              <td>{cad_count} Showcases</td>
              <td>{(cad_count / total_count * 100):.1f}%</td>
              <td>FreeCAD / SolidWorks / Onshape feature trees, 511-solid turbofan assembly (I01–I19)</td>
              <td><span class="badge-tier tier-2">Tier 2 (Code Verified; DFM Pending)</span></td>
            </tr>
            <tr>
              <td><strong>Embodied Robot Control</strong></td>
              <td>{robot_count} Showcases</td>
              <td>{(robot_count / total_count * 100):.1f}%</td>
              <td>Isaac Sim / MuJoCo controllers, SO-101 desktop manipulation, bimanual piano (R01–R32)</td>
              <td><span class="badge-tier tier-2">Tier 2 &amp; 4 (Simulation Parity; Latency Bound)</span></td>
            </tr>
            <tr>
              <td><strong>Animation &amp; Dynamic Workflows</strong></td>
              <td>{anim_count} Showcases</td>
              <td>{(anim_count / total_count * 100):.1f}%</td>
              <td>Character rigging, procedural motion graphics, interactive shaders, previs (A01–A09, M20–M83)</td>
              <td><span class="badge-tier tier-1">Tier 1 &amp; 3 (Interactive / Video Previs)</span></td>
            </tr>
          </tbody>
        </table>

        <!-- Benchmark Comparison Section (Dynamically generated from README) -->
        {benchmarks_section_html}

        <!-- 4-Tier Evidentiary Taxonomy -->
        <h3 class="subsection-title" style="margin-top:2.5rem;">3. Four-Tier Evidentiary Classification Matrix</h3>
        <div class="tier-matrix-grid">
          <div class="tier-card t1">
            <div class="tier-badge">Tier 1 · Established</div>
            <h4>Independently Reproduced with Open Code</h4>
            <p>Verified by independent academic teams with open model weights, fixed API seeds, and deterministic evaluation scripts providing multi-seed confidence intervals (e.g., BVB, Parametric CAD Bench v2).</p>
          </div>
          <div class="tier-card t2">
            <div class="tier-badge">Tier 2 · Partial</div>
            <h4>Technical Reports & Disclosed Telemetry</h4>
            <p>Conducted on standardized benchmarks and reported in vendor whitepapers or closed dashboards, but lacking full end-to-end rollouts or raw environment traces (e.g., PhysBrain 1.5, Blueprint-Bench 2).</p>
          </div>
          <div class="tier-card t3">
            <div class="tier-badge">Tier 3 · Not Established</div>
            <h4>Single Social Media Demonstration Clips</h4>
            <p>Curated single-take screen recordings lacking full prompt histories, retry attempts, and complete execution toolchains, subject to significant survivor and selection bias.</p>
          </div>
          <div class="tier-card t4">
            <div class="tier-badge">Tier 4 · Absent / Refuted</div>
            <h4>Physical Transfer Failures & Safety Boundaries</h4>
            <p>Direct deployment to physical hardware encountering operational bottlenecks: joint overheating, mechanical collisions, DFM tolerance failures, and RoboHarm physical safety refusal failures.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ====================================================================
         VIEW 3: VISUAL CASE ARCHIVE ({total_count} Verified Showcases)
         ==================================================================== -->
    <section id="view-gallery" class="view-panel">
      <div class="gallery-page-layout">
        <!-- Sticky Showcase Directory Sidebar (目录侧栏) -->
        {gallery_sidebar_html}

        <div class="gallery-container">
          <h2 class="panel-section-title">Visual Case Archive ({total_count} Verified Showcases)</h2>
        <p class="panel-section-desc">
          A systematic visual registry compiling all {total_count} multi-domain generation showcases documented across the survey appendix. The underlying dataset and raw demonstration media are actively maintained in the open-source repository: <a href="https://github.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics" target="_blank" rel="noopener noreferrer" style="color: var(--mit-red); font-weight: 600; text-decoration: underline;">Frank-ZY-Dou/awesome-ai-3d-modeling-robotics ↗</a>.
        </p>

        <!-- Evidence Ranking & Reproducibility Protocol -->
        <div class="ranking-protocol-section">
          <div class="ranking-protocol-header">
            <h3 class="subsection-title" style="margin-bottom: 0.35rem;">Evidence Ranking &amp; Reproducibility Hierarchy</h3>
            <p class="ranking-protocol-desc">A three-tier empirical audit protocol categorizing all {total_count} archive showcases by verification depth, code availability, and runtime inspectability. Click any card below to filter the archive directly.</p>
          </div>
          
          <div class="ranking-rules-grid">
            <!-- TIER 1 -->
            <div class="ranking-tier-card tier-1" onclick="setRankFilter('rank-1')" title="Click to filter by Rank 1 showcases">
              <div class="tier-card-header">
                <span class="tier-pill-badge pill-t1">RANK 1 · HIGHEST</span>
                <span class="tier-tag-pill">Full Reproducibility</span>
              </div>
              <h4 class="tier-card-title">Demo + Implementation Code</h4>
              <p class="tier-card-desc">Showcases providing both an execution demo and verified source code, Python scripts, CAD kernel harnesses, or GitHub repositories for end-to-end auditability and execution.</p>
              <ul class="tier-criteria-list">
                <li><span class="check-icon">✓</span> Publicly accessible code repository / script</li>
                <li><span class="check-icon">✓</span> Runnable CAD kernel or robot control harness</li>
                <li><span class="check-icon">✓</span> End-to-end reproducible pipeline</li>
              </ul>
            </div>

            <!-- TIER 2 -->
            <div class="ranking-tier-card tier-2" onclick="setRankFilter('rank-2')" title="Click to filter by Rank 2 showcases">
              <div class="tier-card-header">
                <span class="tier-pill-badge pill-t2">RANK 2 · INTERMEDIATE</span>
                <span class="tier-tag-pill">Interactive Verification</span>
              </div>
              <h4 class="tier-card-title">Demo + Interactive Web Link</h4>
              <p class="tier-card-desc">Showcases providing an execution demo accompanied by a live, inspectable web application, 3D interactive viewer, or public cloud CAD project link (e.g. Onshape, Godot, Three.js) for runtime inspection.</p>
              <ul class="tier-criteria-list">
                <li><span class="check-icon">✓</span> Publicly reachable interactive URL / viewer</li>
                <li><span class="check-icon">✓</span> Online model inspection or live interaction</li>
                <li><span class="check-icon">✓</span> Direct user-driven runtime verification</li>
              </ul>
            </div>

            <!-- TIER 3 -->
            <div class="ranking-tier-card tier-3" onclick="setRankFilter('rank-3')" title="Click to filter by Rank 3 showcases">
              <div class="tier-card-header">
                <span class="tier-pill-badge pill-t3">RANK 3 · BASELINE</span>
                <span class="tier-tag-pill">Demonstration Only</span>
              </div>
              <h4 class="tier-card-title">Demonstration Media Only</h4>
              <p class="tier-card-desc">Showcases providing recorded video clips, animations, or screen captures without public code repositories or hosted interactive runtime environments. Retained for empirical capability scanning.</p>
              <ul class="tier-criteria-list">
                <li><span class="check-icon">✓</span> High-fidelity recorded demonstration media</li>
                <li><span class="cross-icon">✗</span> No public code repository released</li>
                <li><span class="cross-icon">✗</span> No hosted interactive environment available</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Dual Filter & Instant Search Control Card -->
        <div class="gallery-controls-card">
          <!-- Row 1: Evidence Ranking Hierarchy Filter -->
          <div class="filter-row" style="margin-bottom: 0.85rem; padding-bottom: 0.85rem; border-bottom: 1px solid var(--border-subtle);">
            <div class="filter-label">Evidence Rank:</div>
            <div class="filter-pills" role="tablist">
              <button class="filter-pill rank-pill active" data-rank="all" onclick="setRankFilter('all')">
                All Ranks ({total_count})
              </button>
              <button class="filter-pill rank-pill pill-r1" data-rank="rank-1" onclick="setRankFilter('rank-1')">
                <span class="rank-dot dot-r1"></span>
                <span>Rank 1 · Code Released ({r1_count})</span>
              </button>
              <button class="filter-pill rank-pill pill-r2" data-rank="rank-2" onclick="setRankFilter('rank-2')">
                <span class="rank-dot dot-r2"></span>
                <span>Rank 2 · Interactive Demo ({r2_count})</span>
              </button>
              <button class="filter-pill rank-pill pill-r3" data-rank="rank-3" onclick="setRankFilter('rank-3')">
                <span class="rank-dot dot-r3"></span>
                <span>Rank 3 · Demonstration Only ({r3_count})</span>
              </button>
            </div>
          </div>

          <!-- Row 2: Research Domain Filter -->
          <div class="filter-row">
            <div class="filter-label">Domain Scope:</div>
            <div class="filter-pills" role="tablist">
              <button class="filter-pill domain-pill active" data-domain="all" onclick="setDomainFilter('all')">
                All Domains ({total_count})
              </button>
              <button class="filter-pill domain-pill" data-domain="3d" onclick="setDomainFilter('3d')">
                3D Modeling &amp; Scenes ({m_count})
              </button>
              <button class="filter-pill domain-pill" data-domain="cad" onclick="setDomainFilter('cad')">
                Parametric CAD ({cad_count})
              </button>
              <button class="filter-pill domain-pill" data-domain="robotics" onclick="setDomainFilter('robotics')">
                Embodied Robotics ({robot_count})
              </button>
              <button class="filter-pill domain-pill" data-domain="animation" onclick="setDomainFilter('animation')">
                Animation &amp; Motion ({anim_count})
              </button>
            </div>
          </div>

          <!-- Search Input, Sort Selector & Live Counter Row -->
          <div class="gallery-search-wrap">
            <div class="search-input-wrap">
              <input type="text" id="gallery-search" placeholder="Search by ID (e.g. M28, R08, I04), author, platform, or keyword..." oninput="searchGallery()">
            </div>
            <div class="gallery-sort-wrap" style="display: flex; align-items: center; gap: 0.5rem; font-family: var(--font-sans); font-size: 0.85rem;">
              <label for="gallery-sort" style="color: var(--ink-secondary); font-weight: 600;">Sort:</label>
              <select id="gallery-sort" onchange="sortGallery()" style="padding: 0.35rem 0.65rem; border-radius: 4px; border: 1px solid var(--border-subtle); background: var(--bg-surface); color: var(--ink-primary); font-family: var(--font-sans); font-size: 0.85rem; cursor: pointer;">
                <option value="default">Curated Archive Order</option>
                <option value="rank">Evidence Rank (Rank 1 → 2 → 3)</option>
                <option value="id">Case ID (A–Z)</option>
              </select>
            </div>
            <div class="filter-status-text">
              Showing <strong id="gallery-visible-count">{total_count}</strong> of {total_count} showcases
            </div>
          </div>
        </div>

        <!-- Archival Sections Grouped by Domain and Subsection -->
        {gallery_sections_html}
      </div>
    </div>
  </section>

{pdf_section_view}

    <!-- BibTeX Citation Card -->
    <section class="citation-section" id="citation-box">
      <div class="bibtex-box">
        <div class="bibtex-header">
          <span class="bibtex-label">astra_paper_mit_2026.bib</span>
          <button class="btn-copy" onclick="copyBibtex()">Copy BibTeX Citation</button>
        </div>
        <pre class="bibtex-code" id="bibtex-code">@article{{dou2026frontier3drobotics,
  title={{On the Opportunities and Risks of Frontier Models for 3D Modeling, Computational Design and Robotics}},
  author={{Dou, Zhiyang and Watanabe, Akihisa and Deng, Anna and Huang, Tianyu and Meindl, Jamison and Sadalski, Igor and Liang, Harrison and Guo, Minghao and Jones, Benjamin Tod and Matusik, Wojciech}},
  journal={{MIT CSAIL Research Report}},
  year={{2026}},
  month={{September}},
  institution={{Computational Design and Fabrication Group (CDFG), MIT CSAIL}},
  url={{https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/}},
  note={{Working draft, living survey}}
}}</pre>
      </div>
    </section>

    <!-- Minimalist Academic Footer -->
    <footer class="academic-footer">
      <p>
        <strong>Computational Design and Fabrication Group (CDFG)</strong> · MIT CSAIL · Cambridge, MA, USA
      </p>
      <p style="margin-top: 0.4rem;">
        <a href="https://cdfg.csail.mit.edu/" target="_blank">Group Homepage</a> · 
        <a href="https://github.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics" target="_blank" rel="noopener noreferrer">GitHub Repository</a> · 
        {footer_pdf_link}
        <a href="#top" onclick="switchView('view-html')">Back to Top</a>
      </p>
      <p style="margin-top: 0.6rem; font-size: 0.8rem; color: var(--ink-muted);">
        Curated survey dataset & video archive open-sourced at <a href="https://github.com/Frank-ZY-Dou/awesome-ai-3d-modeling-robotics" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: underline;">Frank-ZY-Dou/awesome-ai-3d-modeling-robotics</a>. © 2026 MIT CSAIL CDFG.
      </p>
      <div class="footer-stats-strip">
        <span class="reads-live-dot"></span>
        <span>Empirical Survey Readers: <strong id="footer-reads-count" class="reads-num">0</strong></span>
        <span style="opacity: 0.35;">·</span>
        <span>Global Research Horizon Scan</span>
      </div>
    </footer>

  </main>

  <!-- Fullscreen Lightbox Modal -->
  <div class="modal" id="lightbox-modal">
    <button class="modal-close" onclick="closeLightbox()">&times;</button>
    <div class="modal-inner">
      <video id="lightbox-video" controls autoplay loop playsinline style="display: none; max-width: 100%; max-height: 68vh; border-radius: 6px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);"></video>
      <img src="" alt="Full view" id="lightbox-img" style="max-width: 100%; max-height: 68vh; border-radius: 6px; object-fit: contain;">
      <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-top: 0.75rem;">
        <span class="tile-badge-id" id="lightbox-id-badge" style="display: none;"></span>
        <span class="tile-badge-rank" id="lightbox-rank-badge" style="display: none;"></span>
      </div>
      <div class="modal-caption" id="lightbox-caption" style="text-align: center; margin-top: 0.5rem;"></div>
      <div class="modal-meta" id="lightbox-meta" style="margin-top: 0.35rem; font-size: 0.85rem; color: var(--ink-secondary); text-align: center;"></div>
      <div class="modal-actions" id="lightbox-actions">
        <a id="lightbox-code-link" href="#" target="_blank" rel="noopener noreferrer" class="btn-lightbox-code" style="display:none;" title="View Implementation Code on GitHub">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
          <span>View Implementation Code ↗</span>
        </a>
        <a id="lightbox-demo-link" href="#" target="_blank" rel="noopener noreferrer" class="btn-lightbox-source btn-interactive" style="display:none;" title="Open Interactive Demo">
          <span>Launch Interactive Demo ↗</span>
        </a>
        <a id="lightbox-source-link" href="#" target="_blank" rel="noopener noreferrer" class="btn-lightbox-source">
          <span>Open Original Post ↗</span>
        </a>
      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast">BibTeX copied to clipboard!</div>

  <!-- Main View Switcher & Gallery Search Logic -->
  <script>
    function switchView(viewId, updateHash, skipScrollTop) {{
      document.querySelectorAll('.view-panel').forEach(function(el) {{
        el.classList.remove('active');
      }});
      var target = document.getElementById(viewId);
      if (target) {{
        target.classList.add('active');
      }}

      document.querySelectorAll('.view-tab-btn').forEach(function(btn) {{
        if (btn.getAttribute('data-view') === viewId) {{
          btn.classList.add('active');
          btn.setAttribute('aria-selected', 'true');
        }} else {{
          btn.classList.remove('active');
          btn.setAttribute('aria-selected', 'false');
        }}
      }});

      if (updateHash !== false) {{
        if (history.replaceState) {{
          history.replaceState(null, null, '#' + viewId);
        }} else {{
          window.location.hash = viewId;
        }}
      }}
      
      if (!skipScrollTop) {{
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
      }}
      setTimeout(updateScrollspy, 60);
    }}

    document.querySelectorAll('.view-tab-btn').forEach(function(btn) {{
      btn.addEventListener('click', function() {{
        var v = this.getAttribute('data-view');
        switchView(v);
      }});
    }});

    var activeDomain = 'all';
    var activeRank = 'all';

    function setRankFilter(rank) {{
      activeRank = rank;
      document.querySelectorAll('.filter-pill.rank-pill').forEach(function(p) {{
        if (p.getAttribute('data-rank') === rank) {{
          p.classList.add('active');
        }} else {{
          p.classList.remove('active');
        }}
      }});
      applyGalleryFilters();
    }}

    function setDomainFilter(domain) {{
      activeDomain = domain;
      document.querySelectorAll('.filter-pill.domain-pill').forEach(function(p) {{
        if (p.getAttribute('data-domain') === domain) {{
          p.classList.add('active');
        }} else {{
          p.classList.remove('active');
        }}
      }});
      applyGalleryFilters();
    }}

    function searchGallery() {{
      applyGalleryFilters();
    }}

    function sortGallery() {{
      var sortBy = document.getElementById('gallery-sort').value;
      document.querySelectorAll('.gallery-tiles-grid').forEach(function(grid) {{
        var tiles = Array.from(grid.querySelectorAll('.gallery-tile'));

        tiles.sort(function(a, b) {{
          if (sortBy === 'rank') {{
            var rA = parseInt(a.getAttribute('data-rank-num') || '3', 10);
            var rB = parseInt(b.getAttribute('data-rank-num') || '3', 10);
            if (rA !== rB) return rA - rB;
            var oA = parseInt(a.getAttribute('data-order') || '0', 10);
            var oB = parseInt(b.getAttribute('data-order') || '0', 10);
            return oA - oB;
          }} else if (sortBy === 'id') {{
            var idA = a.getAttribute('data-id') || '';
            var idB = b.getAttribute('data-id') || '';
            return idA.localeCompare(idB);
          }} else {{
            var oA = parseInt(a.getAttribute('data-order') || '0', 10);
            var oB = parseInt(b.getAttribute('data-order') || '0', 10);
            return oA - oB;
          }}
        }});

        tiles.forEach(function(t) {{
          grid.appendChild(t);
        }});
      }});
    }}

    function applyGalleryFilters() {{
      var q = (document.getElementById('gallery-search').value || '').toLowerCase().trim();
      var tiles = document.querySelectorAll('.gallery-tile');
      var visibleCount = 0;
      var subCounts = {{}};
      var domainCounts = {{}};

      tiles.forEach(function(t) {{
        var d = t.getAttribute('data-domain');
        var r = t.getAttribute('data-rank');
        var id = (t.getAttribute('data-id') || '').toLowerCase();
        var author = (t.getAttribute('data-author') || '').toLowerCase();
        var desc = (t.getAttribute('data-desc') || '').toLowerCase();

        var matchesDomain = (activeDomain === 'all' || d === activeDomain);
        var matchesRank = (activeRank === 'all' || r === activeRank);
        var matchesSearch = (!q || id.indexOf(q) !== -1 || author.indexOf(q) !== -1 || desc.indexOf(q) !== -1);

        if (matchesDomain && matchesRank && matchesSearch) {{
          t.style.display = 'flex';
          visibleCount++;
          var parentBlock = t.closest('.gallery-subsection-block');
          if (parentBlock) {{
            var slug = parentBlock.getAttribute('data-sub-slug');
            subCounts[slug] = (subCounts[slug] || 0) + 1;
          }}
          domainCounts[d] = (domainCounts[d] || 0) + 1;
        }} else {{
          t.style.display = 'none';
        }}
      }});

      // Update subsection blocks & sidebar links
      document.querySelectorAll('.gallery-subsection-block').forEach(function(block) {{
        var slug = block.getAttribute('data-sub-slug');
        var blockDomain = block.getAttribute('data-domain');
        var count = subCounts[slug] || 0;
        var badge = document.getElementById('cnt-' + slug);
        var sideBadge = document.getElementById('badge-' + slug);

        if (activeDomain !== 'all' && blockDomain !== activeDomain) {{
          block.style.display = 'none';
        }} else if (count > 0) {{
          block.style.display = '';
        }} else {{
          block.style.display = 'none';
        }}

        if (badge) badge.innerText = count;
        if (sideBadge) {{
          sideBadge.innerText = count;
          var link = sideBadge.closest('.sidebar-sub-link');
          if (link) {{
            if (count === 0) {{
              link.style.opacity = '0.35';
              link.style.pointerEvents = 'none';
            }} else {{
              link.style.opacity = '1';
              link.style.pointerEvents = 'auto';
            }}
          }}
        }}
      }});

      // Update domain sections & sidebar domain groups
      document.querySelectorAll('.gallery-domain-section').forEach(function(sec) {{
        var d = sec.getAttribute('data-domain');
        var dCount = domainCounts[d] || 0;
        var dBadge = document.getElementById('cnt-domain-' + d);
        var sideGroup = document.getElementById('nav-group-' + d);
        var sideDomainBadge = document.getElementById('badge-domain-' + d);

        if (activeDomain !== 'all' && d !== activeDomain) {{
          sec.style.display = 'none';
          if (sideGroup) sideGroup.style.display = 'none';
        }} else if (dCount > 0) {{
          sec.style.display = '';
          if (sideGroup) sideGroup.style.display = '';
        }} else {{
          sec.style.display = 'none';
          if (sideGroup) sideGroup.style.display = 'none';
        }}

        if (dBadge) dBadge.innerText = dCount;
        if (sideDomainBadge) sideDomainBadge.innerText = dCount;
      }});

      var countEl = document.getElementById('gallery-visible-count');
      if (countEl) {{
        countEl.innerText = visibleCount;
      }}
    }}

    function openShowcaseModal(imgUrl, id, title, author, sourceUrl, platform, rankLabel, rankClass, codeUrl, demoUrl, videoUrl, model, tools, subsection) {{
      var m = document.getElementById('lightbox-modal');
      var img = document.getElementById('lightbox-img');
      var video = document.getElementById('lightbox-video');
      var cap = document.getElementById('lightbox-caption');
      var meta = document.getElementById('lightbox-meta');
      var badge = document.getElementById('lightbox-rank-badge');
      var idBadge = document.getElementById('lightbox-id-badge');
      var codeLink = document.getElementById('lightbox-code-link');
      var demoLink = document.getElementById('lightbox-demo-link');
      var sourceLink = document.getElementById('lightbox-source-link');

      if (videoUrl && videoUrl !== '') {{
        video.src = videoUrl;
        video.style.display = 'block';
        img.style.display = 'none';
        video.play().catch(function(e) {{
          console.log('Video autoplay deferred:', e);
        }});
      }} else {{
        if (video) {{
          video.pause();
          video.src = '';
          video.style.display = 'none';
        }}
        img.src = imgUrl;
        img.style.display = 'block';
      }}

      if (badge && rankLabel) {{
        badge.innerText = rankLabel;
        badge.className = 'tile-badge-rank ' + (rankClass || '');
        badge.style.display = 'inline-block';
      }}
      if (idBadge && id) {{
        idBadge.innerText = id;
        idBadge.style.display = 'inline-block';
      }}

      var authorLine = author;
      if (platform) authorLine += ' · ' + platform;
      if (subsection) authorLine += ' · <span style="color:var(--mit-red); font-weight:600;">' + subsection + '</span>';

      cap.innerHTML = '<strong style="font-size:1.05rem;">' + title + '</strong><div style="font-size:0.88rem; color:var(--ink-secondary); margin-top:0.2rem;">' + authorLine + '</div>';
      
      var metaStr = '';
      if (model) metaStr += '<span><strong>Model:</strong> ' + model + '</span>';
      if (tools) metaStr += (metaStr ? ' · ' : '') + '<span><strong>Tools:</strong> ' + tools + '</span>';
      if (meta) {{
        meta.innerHTML = metaStr;
        meta.style.display = metaStr ? 'block' : 'none';
      }}

      if (codeLink) {{
        if (codeUrl && codeUrl !== '') {{
          codeLink.href = codeUrl;
          codeLink.style.display = 'inline-flex';
        }} else {{
          codeLink.style.display = 'none';
        }}
      }}

      if (demoLink) {{
        if (demoUrl && demoUrl !== '') {{
          demoLink.href = demoUrl;
          demoLink.style.display = 'inline-flex';
        }} else {{
          demoLink.style.display = 'none';
        }}
      }}

      if (sourceLink) {{
        if (sourceUrl && sourceUrl !== '#' && sourceUrl !== '') {{
          sourceLink.href = sourceUrl;
          sourceLink.innerHTML = '<span>Open Original Post on ' + (platform || 'Source') + ' ↗</span>';
          sourceLink.style.display = 'inline-flex';
        }} else {{
          sourceLink.style.display = 'none';
        }}
      }}

      m.classList.add('active');
    }}

    function openLightbox(src, caption, url, platform, rankLabel, codeUrl, rankClass) {{
      openShowcaseModal(src, '', caption, '', url, platform, rankLabel, rankClass, codeUrl, '', '', '', '', '');
    }}

    function closeLightbox() {{
      var v = document.getElementById('lightbox-video');
      if (v) {{
        v.pause();
        v.src = '';
        v.style.display = 'none';
      }}
      document.getElementById('lightbox-modal').classList.remove('active');
    }}

    document.getElementById('lightbox-modal').addEventListener('click', function(e) {{
      if (e.target === this) closeLightbox();
    }});

    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape') closeLightbox();
    }});

    // Precise Anchor Navigation & Scrollspy Management
    var isManualJumping = false;

    function highlightSidebarTarget(targetId) {{
      var targetEl = document.getElementById(targetId);
      var slug = targetId;
      var domain = null;

      if (targetEl) {{
        if (targetEl.classList.contains('gallery-subsection-block')) {{
          slug = targetEl.getAttribute('data-sub-slug');
          domain = targetEl.getAttribute('data-domain');
        }} else if (targetEl.classList.contains('gallery-domain-section')) {{
          domain = targetEl.getAttribute('data-domain');
          var firstSub = targetEl.querySelector('.gallery-subsection-block');
          if (firstSub) slug = firstSub.getAttribute('data-sub-slug');
        }}
      }}

      document.querySelectorAll('.sidebar-sub-link').forEach(function(link) {{
        if (slug && link.getAttribute('data-sub-slug') === slug) {{
          link.classList.add('active');
        }} else {{
          link.classList.remove('active');
        }}
      }});

      document.querySelectorAll('.sidebar-domain-head').forEach(function(head) {{
        if (domain && head.getAttribute('data-domain') === domain) {{
          head.classList.add('active');
        }} else {{
          head.classList.remove('active');
        }}
      }});
    }}

    function handleSidebarJump(e, targetId) {{
      if (e && e.preventDefault) e.preventDefault();
      var el = document.getElementById(targetId);
      if (!el) return;

      var nav = document.querySelector('.top-nav-bar');
      var navHeight = nav ? nav.offsetHeight : 54;
      var rect = el.getBoundingClientRect();
      var targetY = Math.round(rect.top + window.pageYOffset - navHeight - 12);
      if (targetY < 0) targetY = 0;

      isManualJumping = true;
      highlightSidebarTarget(targetId);

      window.scrollTo({{
        top: targetY,
        behavior: 'smooth'
      }});

      if (history.replaceState) {{
        history.replaceState(null, null, '#' + targetId);
      }}

      setTimeout(function() {{
        isManualJumping = false;
        highlightSidebarTarget(targetId);
      }}, 750);
    }}

    function jumpToGalleryOverview(e) {{
      if (e && e.preventDefault) e.preventDefault();
      var container = document.querySelector('.gallery-container');
      var nav = document.querySelector('.top-nav-bar');
      var navHeight = nav ? nav.offsetHeight : 54;
      var targetY = container ? Math.round(container.getBoundingClientRect().top + window.pageYOffset - navHeight - 12) : 0;
      if (targetY < 0) targetY = 0;

      isManualJumping = true;
      document.querySelectorAll('.sidebar-sub-link, .sidebar-domain-head').forEach(function(el) {{
        el.classList.remove('active');
      }});
      var ov = document.querySelector('.sidebar-overview-link');
      if (ov) ov.classList.add('active');

      window.scrollTo({{
        top: targetY,
        behavior: 'smooth'
      }});

      if (history.replaceState) {{
        history.replaceState(null, null, '#view-gallery');
      }}

      setTimeout(function() {{
        isManualJumping = false;
        updateScrollspy();
      }}, 750);
    }}

    // Dual Scrollspy for Showcase Directory Sidebar and Paper TOC Sidebar
    var scrollspyTicking = false;
    function updateScrollspy() {{
      if (isManualJumping) return;

      var nav = document.querySelector('.top-nav-bar');
      var navHeight = nav ? nav.offsetHeight : 54;
      var refY = navHeight + 50; // Reference reading focus line

      // 1. Showcase Directory Sidebar in Gallery View
      var galleryView = document.getElementById('view-gallery');
      if (galleryView && galleryView.classList.contains('active')) {{
        var allVisibleSubs = Array.from(document.querySelectorAll('.gallery-subsection-block')).filter(function(b) {{
          return b.style.display !== 'none';
        }});

        if (allVisibleSubs.length === 0) return;

        var activeSub = null;
        var activeDomain = null;

        // Check if scrolled near the very bottom of page
        var atBottom = (window.innerHeight + window.pageYOffset >= document.documentElement.scrollHeight - 60);

        if (atBottom) {{
          activeSub = allVisibleSubs[allVisibleSubs.length - 1];
          activeDomain = activeSub.getAttribute('data-domain');
        }} else {{
          // Find the active domain section first
          var domainSections = Array.from(document.querySelectorAll('.gallery-domain-section')).filter(function(ds) {{
            return ds.style.display !== 'none';
          }});

          var curDomainSec = null;
          for (var d = 0; d < domainSections.length; d++) {{
            var ds = domainSections[d];
            var dr = ds.getBoundingClientRect();
            // A domain section is active if its bottom is below refY and its top is <= refY + 40
            if (dr.top <= refY + 40 && dr.bottom > refY) {{
              curDomainSec = ds;
              break;
            }}
          }}

          if (curDomainSec) {{
            activeDomain = curDomainSec.getAttribute('data-domain');
            var subsInDomain = Array.from(curDomainSec.querySelectorAll('.gallery-subsection-block')).filter(function(b) {{
              return b.style.display !== 'none';
            }});

            if (subsInDomain.length > 0) {{
              // Default to the first subsection in this domain when viewing domain header
              activeSub = subsInDomain[0];

              // Check if any subsequent subsection header has scrolled past refY
              for (var s = 0; s < subsInDomain.length; s++) {{
                var sb = subsInDomain[s];
                var sr = sb.getBoundingClientRect();
                if (sr.top <= refY + 10) {{
                  activeSub = sb;
                }} else {{
                  break;
                }}
              }}
            }}
          }} else {{
            // Check if above all domain sections (at overview / ranking criteria)
            var firstSec = domainSections[0];
            if (firstSec && firstSec.getBoundingClientRect().top > refY) {{
              document.querySelectorAll('.sidebar-sub-link, .sidebar-domain-head').forEach(function(el) {{
                el.classList.remove('active');
              }});
              var overviewLink = document.querySelector('.sidebar-overview-link');
              if (overviewLink) overviewLink.classList.add('active');
              return;
            }}
          }}
        }}

        if (activeSub) {{
          var slug = activeSub.getAttribute('data-sub-slug');
          var dId = activeDomain || activeSub.getAttribute('data-domain');

          document.querySelectorAll('.sidebar-sub-link').forEach(function(link) {{
            if (link.getAttribute('data-sub-slug') === slug) {{
              link.classList.add('active');
            }} else {{
              link.classList.remove('active');
            }}
          }});

          document.querySelectorAll('.sidebar-domain-head').forEach(function(head) {{
            if (head.getAttribute('data-domain') === dId) {{
              head.classList.add('active');
            }} else {{
              head.classList.remove('active');
            }}
          }});

          var ov = document.querySelector('.sidebar-overview-link');
          if (ov) ov.classList.remove('active');
        }}
      }}

      // 2. Paper Reader TOC Sidebar in Full Paper View
      var htmlView = document.getElementById('view-html');
      if (htmlView && htmlView.classList.contains('active')) {{
        var headings = Array.from(document.querySelectorAll('.paper-article h1, .paper-article h2, .paper-article h3, .paper-article section[id], .paper-article div[id]'));
        var activeId = null;
        for (var j = 0; j < headings.length; j++) {{
          var h = headings[j];
          var id = h.getAttribute('id');
          if (!id) continue;
          var hRect = h.getBoundingClientRect();
          if (hRect.top <= navHeight + 70) {{
            activeId = id;
          }}
        }}

        if (activeId) {{
          document.querySelectorAll('.toc-links a').forEach(function(a) {{
            var href = a.getAttribute('href') || '';
            if (href === '#' + activeId) {{
              a.classList.add('active');
            }} else {{
              a.classList.remove('active');
            }}
          }});
        }}
      }}

      scrollspyTicking = false;
    }}

    window.addEventListener('DOMContentLoaded', function() {{
      var h = window.location.hash;
      if (h) {{
        var cleanId = h.replace(/^#/, '');
        if (cleanId === 'benchmarks' || cleanId === 'benchmark') {{
          switchView('view-stats', false);
          setTimeout(function() {{
            var el = document.getElementById('benchmarks-section') || document.getElementById('view-stats');
            if (el) el.scrollIntoView({{behavior: 'smooth'}});
          }}, 120);
        }} else if (cleanId.startsWith('sub-') || cleanId.startsWith('domain-')) {{
          switchView('view-gallery', false, true);
          setTimeout(function() {{
            handleSidebarJump(null, cleanId);
          }}, 120);
        }} else if (document.getElementById(cleanId)) {{
          switchView(cleanId, false);
        }}
      }}
      setTimeout(updateScrollspy, 100);
    }});

    window.addEventListener('hashchange', function() {{
      var h = window.location.hash;
      if (h) {{
        var cleanId = h.replace(/^#/, '');
        if (cleanId === 'benchmarks' || cleanId === 'benchmark') {{
          switchView('view-stats', false);
          setTimeout(function() {{
            var el = document.getElementById('benchmarks-section') || document.getElementById('view-stats');
            if (el) el.scrollIntoView({{behavior: 'smooth'}});
          }}, 120);
        }}
      }}
    }});

    function copyBibtex() {{
      var code = document.getElementById('bibtex-code').innerText;
      navigator.clipboard.writeText(code).then(function() {{
        var toast = document.getElementById('toast');
        toast.classList.add('show');
        setTimeout(function() {{ toast.classList.remove('show'); }}, 2500);
      }});
    }}

    // Reading progress bar and scrollspy throttle
    window.addEventListener('scroll', function() {{
      var docH = document.documentElement.scrollHeight - window.innerHeight;
      var scrolled = (window.scrollY / (docH || 1)) * 100;
      var prog = document.getElementById('reading-progress');
      if (prog) prog.style.width = scrolled + '%';

      if (!scrollspyTicking) {{
        window.requestAnimationFrame(updateScrollspy);
        scrollspyTicking = true;
      }}
    }});
  </script>
</body>
</html>
"""

    out_file = os.path.join(WEBSITE_DIR, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    print("index.html successfully written!")

if __name__ == "__main__":
    build_full_html()
