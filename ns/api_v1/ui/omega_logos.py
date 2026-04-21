"""GET /api/v1/ui/omega_logos — AXIOLEV Holdings LLC © 2026"""
from fastapi import APIRouter
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from tools.scoring.master import CURRENT, score_i6  # type: ignore

router = APIRouter()

@router.get("/omega_logos")
def omega_logos():
    i6 = next(i for i in CURRENT if i.id=="I6")
    composite = score_i6(i6.subs)
    return {
        "composite": composite,
        "sub": [{"key": s.key, "name": s.name, "score": s.score, "weight": s.weight} for s in i6.subs],
        "ceilings": {"engineering": 93.2, "external_gated": 94.4, "theoretical": 100},
    }
