"""v10 smoke — each new lens instantiates and has required attributes."""
import pytest, importlib

V10_LENS_MODULES = [
    ("services.ns.nss.lenses.v10.provenance_chain_lens",          "ProvenanceChainLens"),
    ("services.ns.nss.lenses.v10.differential_privacy_lens",      "DifferentialPrivacyLens"),
    ("services.ns.nss.lenses.v10.adversarial_robustness_lens",    "AdversarialRobustnessLens"),
    ("services.ns.nss.lenses.v10.temporal_coherence_lens",        "TemporalCoherenceLens"),
    ("services.ns.nss.lenses.v10.cross_source_triangulation_lens","CrossSourceTriangulationLens"),
    ("services.ns.nss.lenses.v10.legal_compliance_lens",          "LegalComplianceLens"),
    ("services.ns.nss.lenses.v10.bias_detection_lens",            "BiasDetectionLens"),
    ("services.ns.nss.lenses.v10.version_drift_lens",             "VersionDriftLens"),
    ("services.ns.nss.lenses.v10.citation_integrity_lens",        "CitationIntegrityLens"),
    ("services.ns.nss.lenses.v10.claim_novelty_lens",             "ClaimNoveltyLens"),
    ("services.ns.nss.lenses.v10.langchain_agentic_lens",         "LangChainAgenticLens"),
    ("services.ns.nss.lenses.v10.streaming_lens",                 "StreamingLens"),
    ("services.ns.nss.lenses.v10.embedding_drift_lens",           "EmbeddingDriftLens"),
    ("services.ns.nss.lenses.v10.cost_budget_lens",               "CostBudgetLens"),
    ("services.ns.nss.lenses.v10.schema_evolution_lens",          "SchemaEvolutionLens"),
    ("services.ns.nss.lenses.v10.multimodal_lens",                "MultiModalLens"),
    ("services.ns.nss.lenses.v10.federated_lens",                 "FederatedLens"),
]

@pytest.mark.parametrize("mod_path,cls_name", V10_LENS_MODULES)
def test_lens_has_required_attrs(mod_path, cls_name):
    mod = importlib.import_module(mod_path)
    cls = getattr(mod, cls_name)
    assert hasattr(cls, "name"),     f"{cls_name} missing .name"
    assert hasattr(cls, "team_id"),  f"{cls_name} missing .team_id"
    assert hasattr(cls, "contract"), f"{cls_name} missing .contract"
    assert cls.team_id != "unassigned", f"{cls_name}.team_id is still 'unassigned'"
