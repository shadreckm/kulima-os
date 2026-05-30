"""
System API endpoints for system identity and metadata
"""
from fastapi import APIRouter
from typing import Dict

router = APIRouter()

# System Identity Definition
SYSTEM_IDENTITY = {
    "name": "KULIMA OS",
    "version": "1.0.0",
    "type": "coordination-first infrastructure planning system",
    "description": "A coordination-first infrastructure planning system that transforms real-world activity into decision-grade intelligence without relying on identity or assumptions.",
    "positioning": "Epistemic Digital Public Infrastructure (DPI) for infrastructure planning",
    "architectural_philosophy": "Planning based on observed coordination patterns across time, space, and sectors — not assumptions or individual data.",
    "invariants": {
        "zero_pii": "Operates only on aggregated patterns (never raw signals or individual data)",
        "coordination_over_identity": "Analyzes collective patterns, not individual behaviors",
        "semantic_guard": "Designed for infrastructure planning, not surveillance or profiling",
        "epistemic_reliability": "Truth from repetition, not reporting or assumptions"
    },
    "core_principles": [
        "Identity-free coordination intelligence",
        "Coordination-driven decision making",
        "Temporally grounded analysis",
        "Decision-oriented outputs"
    ],
    "forbidden_operations": [
        "Track individuals",
        "Infer identity",
        "Perform behavioral prediction",
        "Enable surveillance"
    ],
    "system_objective": "Enable planning based on observed coordination patterns across time, space, and sectors — not assumptions or individual data."
}


@router.get("/system/info")
async def get_system_info() -> Dict:
    """
    Return system identity and metadata.
    
    Response:
    {
      "name": "KULIMA OS",
      "version": "1.0.0",
      "type": "coordination-first infrastructure planning system",
      "description": "...",
      "invariants": {...},
      "core_principles": [...]
    }
    """
    return {
        "success": True,
        "status": "success",
        "data": SYSTEM_IDENTITY
    }


@router.get("/system/invariants")
async def get_system_invariants() -> Dict:
    """
    Return system invariants and constraints.
    
    Response:
    {
      "invariants": {...},
      "forbidden_operations": [...]
    }
    """
    return {
        "success": True,
        "status": "success",
        "data": {
            "invariants": SYSTEM_IDENTITY["invariants"],
            "forbidden_operations": SYSTEM_IDENTITY["forbidden_operations"]
        }
    }
