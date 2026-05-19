from pilot_signals import generate_pilot_signals
from lumoza_engine import LumozaEngine
from lundai_engine import LundaiEngine
from zentari_engine import ZentariEngine
from prospectus_generator import ProspectusGenerator
from policy import compute_planning_reserve


def test_zentari_output_explanation_fields():
    signals = generate_pilot_signals()
    patterns = LumozaEngine().process_signals(signals)
    planning_reserve = compute_planning_reserve(len(patterns))
    results = ZentariEngine().evaluate_coordination_confidence(patterns, planning_reserve=planning_reserve)

    assert results, "ZENTARI should produce at least one coordination confidence result"
    for result in results:
        explanation = result.get('explanation')
        assert isinstance(explanation, dict)
        assert explanation['why_accepted'], "Explain why the pattern was accepted"
        assert explanation['why_rejected'], "Explain why other patterns were rejected"
        assert explanation['reserve_explanation'], "Explain why the reserve was applied"
        assert explanation['action_allowed_explanation'], "Explain whether action is allowed"
        assert explanation['human_readable'], "Provide a human-readable explanation"
        assert result['trust']['action_allowed'] in (True, False)


def test_prospectus_patterns_are_explainable():
    signals = generate_pilot_signals()
    patterns = LumozaEngine().process_signals(signals)
    planning_reserve = compute_planning_reserve(len(patterns))
    lundai_analysis = LundaiEngine().analyze_settlement_context(patterns, planning_reserve=planning_reserve)
    confidence_results = ZentariEngine().evaluate_coordination_confidence(patterns, planning_reserve=planning_reserve)
    prospectus = ProspectusGenerator().generate_prospectus(
        confidence_results,
        lundai_analysis=lundai_analysis,
        metadata={"region": "Pilot Region", "period": "7-cycle window"},
        planning_reserve=planning_reserve,
    )

    assert 'coordination_patterns' in prospectus
    assert prospectus['coordination_patterns'], "Prospectus should contain coordination patterns"
    for pattern in prospectus['coordination_patterns']:
        explanation = pattern.get('explanation')
        assert isinstance(explanation, dict)
        assert explanation['why_accepted']
        assert explanation['why_rejected']
        assert explanation['reserve_explanation']
        assert explanation['action_allowed_explanation']
        assert explanation['human_readable']
