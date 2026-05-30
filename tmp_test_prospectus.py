import sys
import os
sys.path.insert(0, os.getcwd())
from core.prospectus.prospectus_generator import ProspectusGenerator
from policy import compute_planning_reserve

sample_pattern = {
    'activity_type': 'irrigation',
    'zone': 'MZUZU',
    'time_window': 'morning',
    'service_priority': 'productive',
    'pattern_persistence': 0.85,
    'pattern_stability': 0.8,
    'demand_rhythm': {'frequency': '6 of 7 cycles', 'stability_class': 'stable', 'time_window': 'morning'},
    'stability_score': 0.8,
    'validation_strength': 'strong',
    'validation_details': 'human and telemetry aligned',
    'integrity_score': 0.82,
    'confidence_class': 'high',
    'coordination_confidence': 0.82,
    'bankability_note': 'Bankable under pilot assumptions',
    'signal_count': 12,
    'validated_signals': 10,
    'unique_days': 5,
    'unique_senders': 8,
    'burst_ratio': 1.2,
    'anomaly_flag': False,
    'alignment_level': 'high',
    'rejected_signals': None,
    'trust': {'action_allowed': True},
    'confidence_score': 0.9,
    'persistence': 0.85,
    'flow_strength': 0.4,
    'explanation': {
        'why_accepted': 'Pattern meets persistence and validation thresholds.',
        'why_rejected': 'No upstream pattern rejection.',
        'reserve_explanation': '25% planning reserve applied for critical communal loads.',
        'action_allowed_explanation': 'Action allowed because trust score exceeds threshold.',
        'human_readable': 'High-confidence coordination pattern for irrigation in Mzuzu morning window.'
    }
}
planning_reserve = compute_planning_reserve(12)
print('planning_reserve', planning_reserve)

g = ProspectusGenerator()
prospectus = g.generate_prospectus(
    [sample_pattern],
    lundai_analysis={'flow_graph': {'nodes': [], 'edges': []}, 'zone_analyses': {}},
    metadata={'region': 'MZUZU', 'period': '7-cycle window', 'is_sample': False},
    planning_reserve=planning_reserve,
)
print('success', type(prospectus), len(prospectus))
print(list(prospectus.keys())[:10])
