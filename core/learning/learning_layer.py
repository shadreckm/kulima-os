"""
KULIMA OS Pilot - Learning Layer
================================

Learning Layer for hybrid controlled-learning model with 4 stages.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on aggregated patterns (never raw signals)
- Coordination > Identity: System learns vocabulary, NOT user behavior
- Semantic Guard: No behavioral tracking or individual profiling

The Learning Layer enables the system to adapt to new phrases and activity types
through a controlled approval process, ensuring reliability while maintaining
strict adherence to system invariants.
"""

from typing import List, Dict, Optional, Set
from collections import defaultdict
from datetime import datetime, timedelta


class LearningLayer:
    """
    Learning Layer for hybrid controlled-learning model.
    
    Enables the system to learn new phrases and activity types through a
    controlled 4-stage process while maintaining Zero-PII and Coordination > Identity invariants.
    """
    
    # Learning thresholds
    MIN_SIGNAL_COUNT = 5  # Phrase must appear across ≥5 signals
    MIN_TIME_WINDOWS = 2  # Phrase must appear across ≥2 distinct time windows
    
    def __init__(self):
        """Initialize Learning Layer."""
        # Stage 1: Unknown phrase tracking
        self.unknown_phrases = defaultdict(list)  # phrase -> list of signal occurrences
        
        # Stage 2: Pattern-based trigger tracking
        self.phrase_patterns = defaultdict(dict)  # phrase -> {signal_count, time_windows, consistency}
        
        # Stage 3: Curated mapping dictionary (approved mappings)
        self.approved_mappings = {
            'irrigation': {
                'canonical_activity': 'irrigation',
                'synonyms': ['watering crops', 'using pump', 'watering farm', 'pumping water']
            },
            'milling': {
                'canonical_activity': 'milling',
                'synonyms': ['grinding', 'processing grain', 'maize milling']
            },
            'cold storage': {
                'canonical_activity': 'cold_storage',
                'synonyms': ['refrigeration', 'cooling', 'cold room']
            },
            'welding': {
                'canonical_activity': 'welding',
                'synonyms': ['metal work', 'fabrication']
            },
            'trading': {
                'canonical_activity': 'trading',
                'synonyms': ['market activity', 'selling goods', 'commerce']
            }
        }
        
        # Stage 4: Semantic expansion tracking
        self.semantic_expansions = defaultdict(set)  # canonical_activity -> set of synonyms
        
        # Initialize semantic expansions from approved mappings
        for canonical, mapping in self.approved_mappings.items():
            self.semantic_expansions[canonical] = set(mapping['synonyms'])
    
    def detect_unknown_phrases(self, signals: List[Dict]) -> List[Dict]:
        """
        Stage 1: Automatic Detection - Log unknown phrases from incoming signals.
        
        Args:
            signals: List of incoming signals
            
        Returns:
            List of unknown phrase detections
        """
        unknown_detections = []
        
        for signal in signals:
            activity_type = signal.get('activity_type', '').lower()
            
            # Check if phrase matches existing mappings
            if not self._is_known_phrase(activity_type):
                # Log unknown phrase
                self.unknown_phrases[activity_type].append({
                    'timestamp': signal.get('timestamp', datetime.utcnow().isoformat()),
                    'zone': signal.get('zone'),
                    'time_window': signal.get('time_window')
                })
                
                unknown_detections.append({
                    'phrase': activity_type,
                    'timestamp': signal.get('timestamp'),
                    'zone': signal.get('zone'),
                    'classification': 'unmapped_signal'
                })
        
        return unknown_detections
    
    def evaluate_phrase_consistency(self, phrase: str, signal_history: List[Dict]) -> Dict:
        """
        Stage 2: Pattern-Based Trigger - Evaluate if phrase meets learning criteria.
        
        Args:
            phrase: Phrase to evaluate
            signal_history: Signal history for the phrase
            
        Returns:
            Evaluation result with trigger status
        """
        if phrase not in self.unknown_phrases:
            return {
                'phrase': phrase,
                'trigger_status': 'not_tracked',
                'signal_count': 0,
                'time_windows': 0,
                'consistency': 0.0
            }
        
        occurrences = self.unknown_phrases[phrase]
        signal_count = len(occurrences)
        
        # Count distinct time windows
        time_windows = set(occ.get('time_window') for occ in occurrences)
        time_window_count = len(time_windows)
        
        # Calculate consistency with known activity types
        consistency = self._calculate_consistency(phrase, occurrences)
        
        # Determine trigger status
        trigger_status = 'not_met'
        if signal_count >= self.MIN_SIGNAL_COUNT and time_window_count >= self.MIN_TIME_WINDOWS and consistency >= 0.7:
            trigger_status = 'met'
        
        # Update pattern tracking
        self.phrase_patterns[phrase] = {
            'signal_count': signal_count,
            'time_windows': time_window_count,
            'consistency': consistency,
            'trigger_status': trigger_status,
            'last_evaluated': datetime.utcnow().isoformat()
        }
        
        return {
            'phrase': phrase,
            'trigger_status': trigger_status,
            'signal_count': signal_count,
            'time_windows': time_window_count,
            'consistency': consistency,
            'criteria': {
                'min_signal_count': self.MIN_SIGNAL_COUNT,
                'min_time_windows': self.MIN_TIME_WINDOWS,
                'min_consistency': 0.7
            }
        }
    
    def propose_new_mapping(self, phrase: str, canonical_activity: str) -> Dict:
        """
        Stage 3: Controlled Approval Layer - Propose new mapping for approval.
        
        Args:
            phrase: Unknown phrase to map
            canonical_activity: Canonical activity to map to
            
        Returns:
            Mapping proposal
        """
        # Check if phrase meets trigger criteria
        if phrase not in self.phrase_patterns:
            evaluation = self.evaluate_phrase_consistency(phrase, self.unknown_phrases.get(phrase, []))
        else:
            evaluation = self.phrase_patterns[phrase]
        
        # Create proposal
        proposal = {
            'phrase': phrase,
            'canonical_activity': canonical_activity,
            'proposal_id': f"prop_{phrase}_{datetime.utcnow().timestamp()}",
            'evaluation': evaluation,
            'status': 'pending_approval',
            'proposed_at': datetime.utcnow().isoformat()
        }
        
        return proposal
    
    def approve_mapping(self, proposal: Dict) -> Dict:
        """
        Stage 3: Controlled Approval Layer - Approve mapping proposal.
        
        Args:
            proposal: Mapping proposal to approve
            
        Returns:
            Approved mapping
        """
        phrase = proposal['phrase']
        canonical_activity = proposal['canonical_activity']
        
        # Add to approved mappings
        if canonical_activity not in self.approved_mappings:
            self.approved_mappings[canonical_activity] = {
                'canonical_activity': canonical_activity,
                'synonyms': []
            }
        
        # Add phrase as synonym
        if phrase not in self.approved_mappings[canonical_activity]['synonyms']:
            self.approved_mappings[canonical_activity]['synonyms'].append(phrase)
        
        # Update semantic expansion
        self.semantic_expansions[canonical_activity].add(phrase)
        
        # Remove from unknown phrases
        if phrase in self.unknown_phrases:
            del self.unknown_phrases[phrase]
        
        # Remove from pattern tracking
        if phrase in self.phrase_patterns:
            del self.phrase_patterns[phrase]
        
        return {
            'phrase': phrase,
            'canonical_activity': canonical_activity,
            'status': 'approved',
            'approved_at': datetime.utcnow().isoformat(),
            'mapping': self.approved_mappings[canonical_activity]
        }
    
    def expand_synonyms(self, canonical_activity: str, new_synonyms: List[str]) -> Dict:
        """
        Stage 4: Semantic Expansion - Add new synonyms to canonical activity.
        
        Args:
            canonical_activity: Canonical activity
            new_synonyms: List of new synonyms to add
            
        Returns:
            Updated mapping
        """
        if canonical_activity not in self.approved_mappings:
            self.approved_mappings[canonical_activity] = {
                'canonical_activity': canonical_activity,
                'synonyms': []
            }
        
        # Add new synonyms
        for synonym in new_synonyms:
            if synonym not in self.approved_mappings[canonical_activity]['synonyms']:
                self.approved_mappings[canonical_activity]['synonyms'].append(synonym)
                self.semantic_expansions[canonical_activity].add(synonym)
        
        return {
            'canonical_activity': canonical_activity,
            'updated_mapping': self.approved_mappings[canonical_activity],
            'expanded_at': datetime.utcnow().isoformat()
        }
    
    def normalize_phrase(self, phrase: str) -> str:
        """
        Normalize phrase using approved mappings and semantic expansions.
        
        Args:
            phrase: Phrase to normalize
            
        Returns:
            Canonical activity
        """
        phrase_lower = phrase.lower()
        
        # Check if phrase is already a canonical activity
        if phrase_lower in self.approved_mappings:
            return phrase_lower
        
        # Check if phrase is a synonym
        for canonical, mapping in self.approved_mappings.items():
            if phrase_lower in [s.lower() for s in mapping['synonyms']]:
                return canonical
        
        # Return original phrase if not found
        return phrase_lower
    
    def get_learning_status(self) -> Dict:
        """
        Get current learning layer status.
        
        Returns:
            Learning status summary
        """
        # Count phrases meeting trigger criteria
        triggered_phrases = [
            phrase for phrase, pattern in self.phrase_patterns.items()
            if pattern.get('trigger_status') == 'met'
        ]
        
        return {
            'unknown_phrases_count': len(self.unknown_phrases),
            'triggered_phrases_count': len(triggered_phrases),
            'approved_mappings_count': len(self.approved_mappings),
            'total_synonyms_count': sum(len(m['synonyms']) for m in self.approved_mappings.values()),
            'triggered_phrases': triggered_phrases,
            'learning_criteria': {
                'min_signal_count': self.MIN_SIGNAL_COUNT,
                'min_time_windows': self.MIN_TIME_WINDOWS,
                'min_consistency': 0.7
            }
        }
    
    def _is_known_phrase(self, phrase: str) -> bool:
        """
        Check if phrase is known (canonical or synonym).
        
        Args:
            phrase: Phrase to check
            
        Returns:
            True if known, False otherwise
        """
        phrase_lower = phrase.lower()
        
        # Check canonical activities
        if phrase_lower in self.approved_mappings:
            return True
        
        # Check synonyms
        for mapping in self.approved_mappings.values():
            if phrase_lower in [s.lower() for s in mapping['synonyms']]:
                return True
        
        return False
    
    def _calculate_consistency(self, phrase: str, occurrences: List[Dict]) -> float:
        """
        Calculate consistency of phrase with known activity types.
        
        Args:
            phrase: Phrase to evaluate
            occurrences: Signal occurrences
            
        Returns:
            Consistency score (0-1)
        """
        # Simplified consistency calculation
        # In a full implementation, this would analyze temporal patterns,
        # zone distribution, and correlation with known activities
        
        if not occurrences:
            return 0.0
        
        # Check if phrase appears in multiple zones (indicates coordination)
        zones = set(occ.get('zone') for occ in occurrences)
        zone_diversity = min(len(zones) / 3, 1.0)  # Normalize to 0-1
        
        # Check if phrase appears in multiple time windows
        time_windows = set(occ.get('time_window') for occ in occurrences)
        time_diversity = min(len(time_windows) / 3, 1.0)  # Normalize to 0-1
        
        # Calculate overall consistency
        consistency = (zone_diversity + time_diversity) / 2
        
        return round(consistency, 2)


def print_learning_status(learning_layer: LearningLayer) -> None:
    """Log learning layer status in a readable format."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("\n" + "=" * 60)
    logger.info("LEARNING LAYER STATUS")
    logger.info("=" * 60)

    status = learning_layer.get_learning_status()

    logger.info(f"\nUnknown Phrases: {status['unknown_phrases_count']}")
    logger.info(f"Triggered Phrases: {status['triggered_phrases_count']}")
    logger.info(f"Approved Mappings: {status['approved_mappings_count']}")
    logger.info(f"Total Synonyms: {status['total_synonyms_count']}")

    if status['triggered_phrases']:
        logger.info("\nTriggered Phrases (ready for approval):")
        for phrase in status['triggered_phrases']:
            logger.info(f"  - {phrase}")

    logger.info("\nLearning Criteria:")
    logger.info(f"  Min Signal Count: {status['learning_criteria']['min_signal_count']}")
    logger.info(f"  Min Time Windows: {status['learning_criteria']['min_time_windows']}")
    logger.info(f"  Min Consistency: {status['learning_criteria']['min_consistency']}")

    logger.info("\n" + "=" * 60)
    logger.info("INVARIANT COMPLIANCE:")
    logger.info("✓ Zero-PII: System learns vocabulary, NOT user behavior")
    logger.info("✓ Coordination > Identity: Phrase patterns, not individual tracking")
    logger.info("✓ Semantic Guard: Controlled approval layer prevents uncontrolled expansion")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Test with sample data
    import logging
    logging.getLogger(__name__).info("Testing Learning Layer...")

    learning_layer = LearningLayer()
    
    # Sample signals with unknown phrases
    signals = [
        {'activity_type': 'watering crops', 'zone': 'MZUZU', 'time_window': 'morning', 'timestamp': '2026-01-01T08:00:00Z'},
        {'activity_type': 'watering crops', 'zone': 'MZUZU', 'time_window': 'morning', 'timestamp': '2026-01-02T08:00:00Z'},
        {'activity_type': 'watering crops', 'zone': 'MZUZU', 'time_window': 'afternoon', 'timestamp': '2026-01-03T14:00:00Z'},
        {'activity_type': 'watering crops', 'zone': 'LILONGWE', 'time_window': 'morning', 'timestamp': '2026-01-04T08:00:00Z'},
        {'activity_type': 'watering crops', 'zone': 'BLANTYRE', 'time_window': 'morning', 'timestamp': '2026-01-05T08:00:00Z'},
        {'activity_type': 'grinding', 'zone': 'MZUZU', 'time_window': 'afternoon', 'timestamp': '2026-01-01T14:00:00Z'},
        {'activity_type': 'grinding', 'zone': 'MZUZU', 'time_window': 'afternoon', 'timestamp': '2026-01-02T14:00:00Z'},
        {'activity_type': 'grinding', 'zone': 'MZUZU', 'time_window': 'morning', 'timestamp': '2026-01-03T08:00:00Z'},
        {'activity_type': 'grinding', 'zone': 'LILONGWE', 'time_window': 'afternoon', 'timestamp': '2026-01-04T14:00:00Z'},
        {'activity_type': 'grinding', 'zone': 'BLANTYRE', 'time_window': 'afternoon', 'timestamp': '2026-01-05T14:00:00Z'}
    ]
    
    # Stage 1: Detect unknown phrases
    unknown_detections = learning_layer.detect_unknown_phrases(signals)
    logging.getLogger(__name__).info(f"\nStage 1: Detected {len(unknown_detections)} unknown phrases")
    
    # Stage 2: Evaluate phrase consistency
    for phrase in ['watering crops', 'grinding']:
        evaluation = learning_layer.evaluate_phrase_consistency(phrase, learning_layer.unknown_phrases.get(phrase, []))
        logging.getLogger(__name__).info(f"\nStage 2: Evaluation for '{phrase}':")
        logging.getLogger(__name__).info(f"  Trigger Status: {evaluation['trigger_status']}")
        logging.getLogger(__name__).info(f"  Signal Count: {evaluation['signal_count']}")
        logging.getLogger(__name__).info(f"  Time Windows: {evaluation['time_windows']}")
        logging.getLogger(__name__).info(f"  Consistency: {evaluation['consistency']}")
    
    # Stage 3: Propose and approve mappings
    proposal1 = learning_layer.propose_new_mapping('watering crops', 'irrigation')
    proposal2 = learning_layer.propose_new_mapping('grinding', 'milling')
    
    logging.getLogger(__name__).info(f"\nStage 3: Proposed mappings")
    approved1 = learning_layer.approve_mapping(proposal1)
    approved2 = learning_layer.approve_mapping(proposal2)
    
    # Stage 4: Test normalization
    logging.getLogger(__name__).info(f"\nStage 4: Normalization test")
    logging.getLogger(__name__).info(f"  'watering crops' -> {learning_layer.normalize_phrase('watering crops')}")
    logging.getLogger(__name__).info(f"  'grinding' -> {learning_layer.normalize_phrase('grinding')}")

    # Log final status
    print_learning_status(learning_layer)
