"""Perception layer — semantic clustering + background hypothesis.
AXIOLEV Holdings LLC © 2026. (Maps to I₆.C1 — hypothesis_generation_density.)"""
from typing import Dict, List
from collections import defaultdict

def cluster(tabs: List[Dict]) -> Dict[str, List[int]]:
    """Cluster tabs by coarse semantic family. Returns family -> [tab_index]."""
    KEYS = {
        "finance": ("stock", "earnings", "revenue", "sec", "market", "ticker"),
        "code":    ("github", "pull", "commit", ".py", ".ts", "stackoverflow"),
        "docs":    ("notion", "docs.google", "confluence", "readme", "spec"),
        "ui":      ("figma", "dribbble", "tailwind", "component", "design"),
    }
    out = defaultdict(list)
    for i, tab in enumerate(tabs):
        url = (tab.get("url", "") + " " + tab.get("title", "")).lower()
        placed = False
        for fam, keys in KEYS.items():
            if any(k in url for k in keys):
                out[fam].append(i); placed = True; break
        if not placed:
            out["other"].append(i)
    return dict(out)

def background_hypotheses(context: Dict, max_n: int = 3) -> List[str]:
    """Generate hypothesis strings from context keywords (stub, deterministic)."""
    keys = list(context.keys())[:max_n]
    return [f"hypothesis: relation between '{k}' and '{context[k]}' observed" for k in keys]
