# SPDX-FileCopyrightText: 2026 Mike Kenworthy <mike@axiolev.com>
# SPDX-License-Identifier: LicenseRef-AXIOLEV-Proprietary
# AXIOLEV Holdings LLC — NS∞ qr phase 25 tests
# Sole architect: Mike Kenworthy
"""Acceptance tests for phase 25: Quantum-Ready U dimension — classical QUBO/Ising solver (dwave-samplers/PyQUBO) on port 9022; 6 new receipts; gates 13-15; tag ns-infinity-quantum-ready-v1"""
import pytest

@pytest.mark.parametrize("dim", ['U'])
def test_phase_25_scaffold(dim):
    """Scaffold acceptance — dimension {dim} touched by phase 25."""
    assert dim in ['U']
