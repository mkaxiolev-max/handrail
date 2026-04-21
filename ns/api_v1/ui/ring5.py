"""GET /api/v1/ui/ring5 — AXIOLEV Holdings LLC © 2026"""
from fastapi import APIRouter
router = APIRouter()
@router.get("/ring5")
def ring5():
    return {"gates": [
        {"id":"G1","name":"Stripe LLC verification","status":"open"},
        {"id":"G2","name":"Live Stripe secret key","status":"open"},
        {"id":"G3","name":"ROOT/Handrail price IDs","status":"open"},
        {"id":"G4","name":"YubiKey slot 2 enrollment","status":"open"},
        {"id":"G5","name":"DNS CNAME root.axiolev.com","status":"open"},
    ]}
