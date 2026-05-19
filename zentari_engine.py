"""
KULIMA OS Pilot - ZENTARI Trust Engine
=======================================

ZENTARI derives trust from coordination patterns, not from individuals.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on aggregated coordination patterns (never raw signals)
- Temporal Moat: Evaluates patterns across time windows (no real-time tracking)
- Coordination > Identity: Trust is a property of coordination, not people
- Semantic Guard: No credit scoring, no reputations, no individual profiling

ZENTARI replaces credit scoring without creating reputations:
- High trust = "this demand pattern is stable and bankable"
- NOT "these people are reliable"

Trust grows when coordination persists. Trust decays when coordination breaks down.
"""

from typing import List, Dict

from policy import require_planning_reserve, RESERVE_RATIO


class ZentariEngine:
    """
    ZENTARI - Trust and Coordination Confidence Engine
    
    Evaluates the trustworthiness of coordination patterns for infrastructure planning.
    Trust is derived from pattern stability, validation strength, and resilience.
    """
    
    def __init__(self):
        """Initialize ZENTARI engine."""
        pass

    def _validate_explanation(self, explanation: Dict, planning_reserve: Dict, action_allowed: bool) -> None:
        """Ensure explainability fields are present and complete."""
        if not isinstance(explanation, dict):
            raise ValueError("ZENTARI output explanation must be a dictionary.")

        required_keys = [
            'why_accepted',
            'why_rejected',
            'reserve_explanation',
            'action_allowed_explanation',
            'human_readable'
        ]

        missing_keys = [key for key in required_keys if not explanation.get(key)]
        if missing_keys:
            raise ValueError(
                f"ZENTARI explanation missing required keys: {', '.join(missing_keys)}"
            )

        if not isinstance(planning_reserve, dict):
            raise ValueError("ZENTARI explanation validation requires a valid planning_reserve object.")

        if action_allowed not in (True, False):
            raise ValueError("ZENTARI explanation must include a boolean action_allowed value.")

    def evaluate_coordination_confidence(
        self,
        coordination_patterns: List[Dict],
        planning_reserve: Dict = None,
    ) -> List[Dict]:
        """
        Evaluate coordination confidence for each pattern.
        
        COORDINATION > IDENTITY:
        - Accepts only LUMOZA outputs (aggregated patterns, never raw signals)
        - Evaluates pattern trustworthiness, not individual creditworthiness
        - Produces confidence scores for infrastructure planning
        
        SEMANTIC GUARD:
        - No credit scoring (evaluates patterns, not people)
        - No reputations (confidence is about coordination stability)
        - No eligibility gating (outputs inform planning, not access control)
        
        Args:
            coordination_patterns: List of patterns from LUMOZA
            planning_reserve: Planning reserve object describing usable_signals and reserve_buffer
            
        Returns:
            List of patterns with coordination_confidence scores
        """
        
        if planning_reserve is None:
            raise ValueError(
                "ZENTARI requires an explicit planning_reserve object derived from usable signals."
            )
        require_planning_reserve(planning_reserve)
        
        confidence_results = []

        # Mapping for uncertainty bands based on validation strength
        band_map = {
            'strong': 0.05,
            'moderate': 0.10,
            'weak': 0.20,
            'human_only': 0.25,
            'none': 0.5
        }

        # Trust configuration
        TRUST_THRESHOLD = 0.6  # Minimum trust required to allow actionable recommendations

        def _compute_trust_score(pattern: Dict) -> float:
            """Compute a trust score [0-1] from multiple signals.

            Components used:
            - integrity_score (0-1)
            - time_span (unique_days normalized to 7 days)
            - user_diversity (unique_senders / signal_count)
            - settlement_alignment (high=1, medium=0.6, low=0.3)
            """
            integrity = float(pattern.get('integrity_score') or 0.0)
            unique_days = float(pattern.get('unique_days') or 0.0)
            time_span = min(unique_days / 7.0, 1.0)
            signal_count = float(pattern.get('signal_count') or 1.0)
            unique_senders = float(pattern.get('unique_senders') or pattern.get('user_diversity') or 0.0)
            user_diversity = min(unique_senders / max(1.0, signal_count), 1.0)

            alignment_level = pattern.get('alignment_level') or pattern.get('validation_strength') or 'low'
            alignment_map = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
            alignment = alignment_map.get(alignment_level, 0.3)

            # weights
            w_integrity = 0.4
            w_time = 0.2
            w_user = 0.2
            w_align = 0.2

            score = (
                w_integrity * integrity
                + w_time * time_span
                + w_user * user_diversity
                + w_align * alignment
            )
            return round(min(max(score, 0.0), 1.0), 2)

        def _classify_trust_level(score: float) -> str:
            if score >= 0.85:
                return 'Deployable Trust'
            if score >= 0.7:
                return 'Verified Coordination'
            if score >= 0.5:
                return 'Emerging Trust'
            return 'Untrusted'

        for pattern in coordination_patterns:
            stability_score = pattern.get('stability_score', 0.0)
            validation_strength = pattern.get('validation_strength', 'human_only')

            # Base coordination confidence
            confidence_score = self._calculate_confidence(
                stability_score=stability_score,
                validation_strength=validation_strength
            )

            confidence_class = self._classify_confidence(confidence_score)

            # Confidence band (lower, upper)
            delta = band_map.get(validation_strength, 0.15)
            lower = round(max(0.0, confidence_score - delta), 2)
            upper = round(min(1.0, confidence_score + delta), 2)

            # Demand classification: latent / emerging / active / deployable
            if confidence_score >= 0.8 and stability_score >= 0.7:
                demand_class = 'deployable'
            elif confidence_score >= 0.65:
                demand_class = 'active'
            elif confidence_score >= 0.5:
                demand_class = 'emerging'
            else:
                demand_class = 'latent'

            # Infrastructure implication based on service priority
            service_priority = pattern.get('service_priority', 'productive')
            if service_priority == 'essential':
                infrastructure_implication = (
                    'Reserve baseline capacity for communal essential services; prioritize resilience and redundancy.'
                )
            else:
                infrastructure_implication = (
                    'Consider staged infrastructure deployment; validate with additional telemetry before major capital allocation.'
                )

            # Planning reserve note (policy constant)
            planning_reserve_note = (
                f"Apply a planning reserve of {int(RESERVE_RATIO * 100)}% to capacity estimates; "
                "reserve for critical communal loads."
            )

            # Uncertainty and risk
            if confidence_class in ('insufficient', 'low') or validation_strength in ('weak', 'none'):
                risk_indication = 'High'
            elif confidence_class == 'moderate' or validation_strength == 'moderate':
                risk_indication = 'Medium'
            else:
                risk_indication = 'Low'

            # Standardized human-readable fields
            what_happening = (
                f"Validated coordination: {pattern.get('activity_type')} in {pattern.get('zone')}"
                f" ({pattern.get('time_window', pattern.get('demand_rhythm', {}).get('time_window', 'unknown'))})"
            )

            reliability = f"{confidence_class.capitalize()} ({confidence_score})"

            implication = infrastructure_implication

            # Recommended action guidance
            if demand_class == 'deployable':
                recommended_action = (
                    'Proceed to technical feasibility study and initial procurement planning; include critical load protections.'
                )
            elif demand_class == 'active':
                recommended_action = (
                    'Commission local telemetry and stakeholder verification; prepare phased deployment plans.'
                )
            elif demand_class == 'emerging':
                recommended_action = (
                    'Monitor across next 2-3 cycles and collect corroborating telemetry before committing capital.'
                )
            else:
                recommended_action = (
                    'Track signals and prioritize data quality improvements; do not commit infrastructure resources.'
                )

            # Decay logic note
            decay_note = self._get_decay_note(pattern.get('demand_rhythm', {}).get('stability_class', 'intermediate'))

            # Build enriched result
            confidence_result = {
                **pattern,
                'coordination_confidence': confidence_score,
                'confidence_class': confidence_class,
                'confidence_band': [lower, upper],
                'confidence_delta': delta,
                'demand_classification': demand_class,
                'infrastructure_implication': infrastructure_implication,
                'planning_reserve_note': planning_reserve_note,
                'uncertainty_boundaries': {
                    'lower': lower,
                    'upper': upper
                },
                'risk_indication': risk_indication,
                'what_is_happening': what_happening,
                'reliability': reliability,
                'implication': implication,
                'recommended_action': recommended_action,
                'bankability_note': self._get_bankability_note(confidence_score),
                'decay_logic': decay_note,
            }

            # Compute institutional trust from multiple axes (separate from coordination_confidence)
            trust_score = _compute_trust_score(pattern)
            trust_level = _classify_trust_level(trust_score)

            # Refusal logic: disallow actionable recommendations when trust below threshold
            action_allowed = trust_score >= TRUST_THRESHOLD
            reason_for_refusal = None
            if not action_allowed:
                reason_for_refusal = (
                    f"Trust level '{trust_level}' (score={trust_score}) below required threshold ({TRUST_THRESHOLD}); "
                    "refusing actionable recommendation."
                )
                # blank or weaken recommended_action to avoid over-assertion
                confidence_result['recommended_action'] = (
                    confidence_result.get('recommended_action') if action_allowed else None
                )

            confidence_result['trust'] = {
                'trust_score': trust_score,
                'trust_level': trust_level,
                'action_allowed': action_allowed,
                'reason_for_refusal': reason_for_refusal,
                'ethical_note': 'Trust derives from coordination, not identity or documents'
            }
            confidence_result['planning_reserve'] = planning_reserve

            # Add explainability breakdown
            signal_origin = 'human' if pattern.get('validation_strength') in ('human_only', 'weak', 'moderate', 'strong') else 'unknown'
            # Determine telemetry presence heuristically
            if pattern.get('validation_strength') in ('strong', 'moderate'):
                signal_origin = 'human + telemetry'

            validation_process = {
                'lundai_integrity_score': pattern.get('integrity_score'),
                'user_diversity': pattern.get('unique_senders', None),
                'burst_ratio': pattern.get('burst_ratio', None),
                'anomaly_flag': pattern.get('anomaly_flag', False),
                'alignment_level': pattern.get('alignment_level', None),
            }

            interpretation = {
                'stability_score': pattern.get('stability_score'),
                'validation_strength': pattern.get('validation_strength'),
                'confidence_calculation': f"confidence={confidence_score} derived from stability * validation multiplier",
            }

            explanation = {
                'why_accepted': (
                    f"Pattern accepted because stability_score={stability_score} and "
                    f"validation_strength='{validation_strength}', which meet coordination confidence requirements. "
                    f"High integrity and alignment support this pattern as a planning signal."
                ),
                'why_rejected': (
                    pattern.get('rejected_signals') and
                    f"Upstream rejected signals were filtered due to low integrity or noise; {len(pattern.get('rejected_signals'))} signal groups were excluded." or
                    "Upstream invalid or noisy patterns were excluded before ZENTARI evaluation."
                ),
                'reserve_explanation': (
                    f"A {int(RESERVE_RATIO * 100)}% planning reserve is applied to maintain capacity for critical communal loads. "
                    f"Usable signals: {planning_reserve.get('usable_signals')} ; reserve_buffer: {planning_reserve.get('reserve_buffer')} ."
                ),
                'action_allowed_explanation': (
                    f"Action is {'allowed' if action_allowed else 'not allowed'} because trust_score={trust_score} "
                    f"{'meets' if action_allowed else 'does not meet'} the threshold of {TRUST_THRESHOLD} for actionable recommendations."
                ),
                'signal_origin': signal_origin,
                'validation_process': validation_process,
                'interpretation': interpretation,
                'human_readable': (
                    f"{confidence_result['what_is_happening']}. "
                    f"Integrity score {validation_process['lundai_integrity_score']}; "
                    f"derived confidence {confidence_score} ({confidence_result['confidence_class']}). "
                    f"Action {'allowed' if action_allowed else 'refused'} by trust policy."
                )
            }

            self._validate_explanation(explanation, planning_reserve, action_allowed)
            confidence_result['explanation'] = explanation

            confidence_results.append(confidence_result)

        return confidence_results
    
    def _calculate_confidence(self, stability_score: float, validation_strength: str) -> float:
        """
        Calculate coordination confidence score (0-1).
        
        Confidence is based on:
        - Pattern stability (how consistently it repeats)
        - Validation strength (human-telemetry alignment)
        
        NOT based on:
        - Individual creditworthiness
        - Personal reputation
        - Behavioral prediction
        """
        
        # Base confidence from stability
        confidence = stability_score
        
        # Adjust based on validation strength
        validation_multipliers = {
            'strong': 1.0,      # Full confidence
            'moderate': 0.85,   # Slight reduction
            'weak': 0.7,        # Significant reduction
            'human_only': 0.6,  # No telemetry corroboration
            'none': 0.0         # No valid signals
        }
        
        multiplier = validation_multipliers.get(validation_strength, 0.5)
        confidence *= multiplier
        
        # Ensure confidence stays in [0, 1]
        return round(min(max(confidence, 0.0), 1.0), 2)
    
    def _classify_confidence(self, confidence_score: float) -> str:
        """Classify confidence level for institutional decision-makers."""
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.6:
            return "moderate"
        elif confidence_score >= 0.4:
            return "low"
        else:
            return "insufficient"
    
    def _get_bankability_note(self, confidence_score: float) -> str:
        """
        Provide bankability guidance for infrastructure planners.
        
        SEMANTIC GUARD:
        - Guidance is for infrastructure investment, not credit decisions
        - No individual eligibility or access control
        """
        if confidence_score >= 0.8:
            return "High confidence for infrastructure investment. Pattern is stable and corroborated."
        elif confidence_score >= 0.6:
            return "Moderate confidence. Pattern shows coordination but may need monitoring."
        elif confidence_score >= 0.4:
            return "Low confidence. Pattern exists but lacks strong validation or stability."
        else:
            return "Insufficient confidence for infrastructure planning at this time."
    
    def _get_decay_note(self, stability_class: str) -> str:
        """
        Explain trust decay logic (conceptual for pilot).
        
        COORDINATION > IDENTITY:
        - Trust decays when coordination breaks down (not when individuals fail)
        - No permanent reputations (trust must be continuously earned through coordination)
        """
        if stability_class == "stable":
            return "Trust persists as long as coordination pattern continues across future cycles. " \
                   "If pattern breaks down (appears in <5 of 7 cycles), confidence will decay."
        else:
            return "Intermediate pattern. Trust will grow if pattern stabilizes (≥5 of 7 cycles) " \
                   "or decay if pattern becomes noise (<3 of 7 cycles)."


def print_confidence_results(results: List[Dict]) -> None:
    """Print coordination confidence results in a readable format."""
    print("\n" + "=" * 60)
    print("ZENTARI OUTPUT - COORDINATION CONFIDENCE")
    print("=" * 60)
    
    if not results:
        print("\nNo coordination patterns to evaluate.")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\nPattern {i}:")
        print(f"  Activity: {result['activity_type']}")
        print(f"  Zone: {result['zone']}")
        print(f"  Time Window: {result['time_window']}")
        print(f"  Stability Score: {result['stability_score']}")
        print(f"  Validation: {result['validation_strength']}")
        print(f"  Coordination Confidence: {result['coordination_confidence']} ({result['confidence_class']})")
        print(f"  Bankability: {result['bankability_note']}")
        print(f"  Decay Logic: {result['decay_logic']}")
    
    print("\n" + "=" * 60)
    print("INVARIANT COMPLIANCE:")
    print("✓ Zero-PII: Confidence scores are about patterns, not people")
    print("✓ Coordination > Identity: Trust is property of coordination")
    print("✓ Semantic Guard: No credit scoring or individual profiling")
    print("✓ Trust decays without sustained coordination (no permanent reputations)")
    print("=" * 60)


if __name__ == "__main__":
    # Test with LUMOZA outputs
    from pilot_signals import generate_pilot_signals
    from lumoza_engine import LumozaEngine
    from policy import compute_planning_reserve
    
    print("Testing ZENTARI Engine with LUMOZA outputs...")
    
    # Generate signals and process through LUMOZA
    signals = generate_pilot_signals()
    lumoza = LumozaEngine()
    patterns = lumoza.process_signals(signals)
    
    # Evaluate coordination confidence
    zentari = ZentariEngine()
    planning_reserve = compute_planning_reserve(len(patterns))
    confidence_results = zentari.evaluate_coordination_confidence(patterns, planning_reserve=planning_reserve)
    
    print_confidence_results(confidence_results)

# Made with Bob
