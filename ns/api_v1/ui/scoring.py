"""GET /api/v1/ui/scoring — AXIOLEV Holdings LLC © 2026"""
from fastapi import APIRouter
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from tools.scoring.master import report  # type: ignore

router = APIRouter()

@router.get("/scoring")
def scoring():
    r = report()
    r["v3_0"]["history"] = [82.0, 83.1, 84.17, 84.46, 85.77, r["v3_0"]["master"]]
    return r
