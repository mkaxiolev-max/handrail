"""v10 — every new lens has correct team_id."""
import pytest
import importlib, sys

EXPECTED = {
    "ProvenanceChainLens":          "validation_audit",
    "DifferentialPrivacyLens":      "validation_audit",
    "AdversarialRobustnessLens":    "validation_audit",
    "TemporalCoherenceLens":        "validation_audit",
    "CrossSourceTriangulationLens": "validation_audit",
    "LegalComplianceLens":          "validation_audit",
    "BiasDetectionLens":            "validation_audit",
    "VersionDriftLens":             "architecture",
    "CitationIntegrityLens":        "validation_audit",
    "ClaimNoveltyLens":             "math_phi",
    "LangChainAgenticLens":         "web_crawl",
    "StreamingLens":                "data_engineering",
    "EmbeddingDriftLens":           "math_phi",
    "CostBudgetLens":               "data_engineering",
    "SchemaEvolutionLens":          "architecture",
    "MultiModalLens":               "web_crawl",
    "FederatedLens":                "web_crawl",
}

@pytest.mark.parametrize("lens_name,expected_team", EXPECTED.items())
def test_lens_team_id(lens_name, expected_team):
    # Import from v10 module
    module_map = {
        "ProvenanceChainLens":          "services.ns.nss.lenses.v10.provenance_chain_lens",
        "DifferentialPrivacyLens":      "services.ns.nss.lenses.v10.differential_privacy_lens",
        "AdversarialRobustnessLens":    "services.ns.nss.lenses.v10.adversarial_robustness_lens",
        "TemporalCoherenceLens":        "services.ns.nss.lenses.v10.temporal_coherence_lens",
        "CrossSourceTriangulationLens": "services.ns.nss.lenses.v10.cross_source_triangulation_lens",
        "LegalComplianceLens":          "services.ns.nss.lenses.v10.legal_compliance_lens",
        "BiasDetectionLens":            "services.ns.nss.lenses.v10.bias_detection_lens",
        "VersionDriftLens":             "services.ns.nss.lenses.v10.version_drift_lens",
        "CitationIntegrityLens":        "services.ns.nss.lenses.v10.citation_integrity_lens",
        "ClaimNoveltyLens":             "services.ns.nss.lenses.v10.claim_novelty_lens",
        "LangChainAgenticLens":         "services.ns.nss.lenses.v10.langchain_agentic_lens",
        "StreamingLens":                "services.ns.nss.lenses.v10.streaming_lens",
        "EmbeddingDriftLens":           "services.ns.nss.lenses.v10.embedding_drift_lens",
        "CostBudgetLens":               "services.ns.nss.lenses.v10.cost_budget_lens",
        "SchemaEvolutionLens":          "services.ns.nss.lenses.v10.schema_evolution_lens",
        "MultiModalLens":               "services.ns.nss.lenses.v10.multimodal_lens",
        "FederatedLens":                "services.ns.nss.lenses.v10.federated_lens",
    }
    mod = importlib.import_module(module_map[lens_name])
    cls = getattr(mod, lens_name)
    assert cls.team_id == expected_team
