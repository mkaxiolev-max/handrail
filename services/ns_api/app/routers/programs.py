"""Programs router — /api/v1/programs/*"""
from fastapi import APIRouter, HTTPException
from shared.models.programs import ProgramSummary, TransitionProposal, BindingVerification
from shared.models.enums import ProgramState, ProgramNamespace, RiskTier
from shared.receipts.generator import get_generator
from shared.models.enums import ReceiptType

router = APIRouter(prefix="/api/v1/programs", tags=["programs"])

SEED_PROGRAMS: list[ProgramSummary] = [
    ProgramSummary(id="prog_commercial", namespace=ProgramNamespace.COMMERCIAL,
                   name="Commercial Operations", state=ProgramState.ACTIVE,
                   description="Revenue-generating commercial ops", ops_count=7),
    ProgramSummary(id="prog_fundraising", namespace=ProgramNamespace.FUNDRAISING,
                   name="Fundraising", state=ProgramState.DRAFT,
                   description="Capital raise pipeline", ops_count=7),
    ProgramSummary(id="prog_hiring", namespace=ProgramNamespace.HIRING,
                   name="Hiring", state=ProgramState.DRAFT,
                   description="Talent acquisition pipeline", ops_count=7),
    ProgramSummary(id="prog_partnership", namespace=ProgramNamespace.PARTNERSHIP,
                   name="Partnership", state=ProgramState.DRAFT,
                   description="Strategic partnership development", ops_count=7),
    ProgramSummary(id="prog_ma", namespace=ProgramNamespace.MA,
                   name="M&A", state=ProgramState.DRAFT,
                   description="Mergers & acquisitions pipeline", ops_count=7),
    ProgramSummary(id="prog_advisor_san", namespace=ProgramNamespace.ADVISOR_SAN,
                   name="Advisor / SAN", state=ProgramState.DRAFT,
                   description="Advisor board and SAN territory ops", ops_count=6),
    ProgramSummary(id="prog_customer_success", namespace=ProgramNamespace.CUSTOMER_SUCCESS,
                   name="Customer Success", state=ProgramState.DRAFT,
                   description="Customer lifecycle and success ops", ops_count=7),
    ProgramSummary(id="prog_product_feedback", namespace=ProgramNamespace.PRODUCT_FEEDBACK,
                   name="Product Feedback", state=ProgramState.DRAFT,
                   description="Feedback ingestion and semantic binder", ops_count=7),
    ProgramSummary(id="prog_governance", namespace=ProgramNamespace.GOVERNANCE,
                   name="Governance", state=ProgramState.ACTIVE,
                   description="Constitutional governance, policy decisions", ops_count=7),
    ProgramSummary(id="prog_knowledge_ingestion", namespace=ProgramNamespace.KNOWLEDGE_INGESTION,
                   name="Knowledge Ingestion", state=ProgramState.ACTIVE,
                   description="Ether ingest, canon promotion, knowledge ops", ops_count=8),
]

_program_index = {p.id: p for p in SEED_PROGRAMS}


@router.get("", response_model=list[ProgramSummary])
async def list_programs():
    return SEED_PROGRAMS


@router.get("/{program_id}", response_model=ProgramSummary)
async def get_program(program_id: str):
    prog = _program_index.get(program_id)
    if not prog:
        raise HTTPException(status_code=404, detail=f"Program {program_id} not found")
    return prog


@router.post("/{program_id}/propose-transition")
async def propose_transition(program_id: str, proposal: TransitionProposal):
    prog = _program_index.get(program_id)
    if not prog:
        raise HTTPException(status_code=404, detail=f"Program {program_id} not found")

    # ma.close_transaction requires approval_ref
    if prog.namespace == ProgramNamespace.MA and proposal.to_state == ProgramState.COMPLETE:
        if not proposal.approval_ref:
            raise HTTPException(status_code=422, detail="ma close_transaction requires approval_ref")

    gen = get_generator()
    receipt = gen.issue_receipt(
        receipt_type=ReceiptType.PROGRAM,
        payload=proposal.model_dump(mode="json"),
        op=f"{prog.namespace.value}.propose_transition",
        risk_tier=proposal.risk_tier,
    )
    return {"proposed": True, "receipt_id": receipt.receipt_id, "proposal": proposal.model_dump(mode="json")}


@router.post("/{program_id}/verify-binding")
async def verify_binding(program_id: str, verification: BindingVerification):
    gen = get_generator()
    receipt = gen.issue_receipt(
        receipt_type=ReceiptType.PROGRAM,
        payload=verification.model_dump(mode="json"),
        op="program.verify_binding",
    )
    return {"verified": True, "receipt_id": receipt.receipt_id}
