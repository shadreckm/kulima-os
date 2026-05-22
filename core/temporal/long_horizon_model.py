"""
KULIMA OS Pilot - Long-Horizon Model
====================================

Long-Horizon Model for monthly and seasonal pattern tracking.

INVARIANT ENFORCEMENT:
- Zero-PII: Operates only on aggregated patterns (never raw signals)
- Coordination > Identity: Analyzes collective patterns, not individual behaviors
- Semantic Guard: Designed for infrastructure planning, not surveillance or profiling

The Long-Horizon Model extends the 7-cycle weekly coordination system to track
patterns over monthly and seasonal time horizons, enabling long-term infrastructure planning.
"""

from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import statistics


class LongHorizonModel:
    """
    Long-Horizon Model for temporal aggregation and trend analysis.
    
    Aggregates weekly coordination patterns into monthly and seasonal signals
    to enable long-term infrastructure planning.
    """
    
    # Aggregation windows
    WEEKS_PER_MONTH = 4  # 4-5 weeks per month
    WEEKS_PER_SEASON = 16  # 12-16 weeks per season
    
    def __init__(self):
        """Initialize Long-Horizon Model."""
        self.weekly_history = []  # Store weekly patterns for aggregation
    
    def add_weekly_patterns(self, weekly_patterns: List[Dict], week_timestamp: str) -> None:
        """
        Add weekly patterns to history for long-horizon analysis.
        
        Args:
            weekly_patterns: Weekly coordination patterns from LUMOZA
            week_timestamp: Timestamp for the week (ISO format)
        """
        self.weekly_history.append({
            'timestamp': week_timestamp,
            'patterns': weekly_patterns
        })
    
    def aggregate_weekly_to_monthly(self, weekly_patterns: List[Dict]) -> List[Dict]:
        """
        Aggregate weekly patterns into monthly coordination signals.
        
        Args:
            weekly_patterns: List of weekly pattern dictionaries with timestamps
            
        Returns:
            Monthly aggregated patterns with persistence, stability, and trend
        """
        if not weekly_patterns:
            return []
        
        # Group by month and activity-zone combination
        monthly_groups = defaultdict(list)
        
        for week_data in weekly_patterns:
            timestamp = week_data['timestamp']
            week_patterns = week_data['patterns']
            
            # Extract month from timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                month_key = dt.strftime('%Y-%m')
            except:
                month_key = 'unknown'
            
            for pattern in week_patterns:
                key = (month_key, pattern['activity_type'], pattern['zone'])
                monthly_groups[key].append(pattern)
        
        # Calculate monthly metrics for each group
        monthly_patterns = []
        for (month, activity, zone), pattern_list in monthly_groups.items():
            if len(pattern_list) < 2:  # Need at least 2 weeks for meaningful aggregation
                continue
            
            # Calculate persistence (frequency across weeks)
            persistence = len(pattern_list) / self.WEEKS_PER_MONTH
            
            # Calculate stability (variance in pattern frequency)
            frequencies = [p.get('pattern_frequency', 1) for p in pattern_list]
            stability = 1.0 - (statistics.stdev(frequencies) / max(statistics.mean(frequencies), 1)) if len(frequencies) > 1 else 1.0
            
            # Calculate average frequency
            avg_frequency = statistics.mean(frequencies)
            
            # Determine trend (requires historical data)
            trend = self._calculate_monthly_trend(month, activity, zone, pattern_list)
            
            monthly_patterns.append({
                'month': month,
                'activity_type': activity,
                'zone': zone,
                'persistence': round(persistence, 2),
                'stability': round(max(0, min(1, stability)), 2),
                'avg_frequency': round(avg_frequency, 2),
                'trend': trend,
                'week_count': len(pattern_list)
            })
        
        return monthly_patterns
    
    def aggregate_monthly_to_seasonal(self, monthly_patterns: List[Dict]) -> List[Dict]:
        """
        Aggregate monthly patterns into seasonal coordination signals.
        
        Args:
            monthly_patterns: Monthly aggregated patterns
            
        Returns:
            Seasonal aggregated patterns with long-term persistence and stability
        """
        if not monthly_patterns:
            return []
        
        # Group by season and activity-zone combination
        seasonal_groups = defaultdict(list)
        
        for pattern in monthly_patterns:
            month = pattern['month']
            activity = pattern['activity_type']
            zone = pattern['zone']
            
            # Determine season from month
            season = self._month_to_season(month)
            
            key = (season, activity, zone)
            seasonal_groups[key].append(pattern)
        
        # Calculate seasonal metrics for each group
        seasonal_patterns = []
        for (season, activity, zone), pattern_list in seasonal_groups.items():
            if len(pattern_list) < 2:  # Need at least 2 months for meaningful aggregation
                continue
            
            # Calculate long-term persistence (frequency across months)
            long_term_persistence = len(pattern_list) / 4  # Assume 4 months per season
            
            # Calculate long-term stability (variance in monthly persistence)
            monthly_persistences = [p['persistence'] for p in pattern_list]
            long_term_stability = 1.0 - (statistics.stdev(monthly_persistences) / max(statistics.mean(monthly_persistences), 1)) if len(monthly_persistences) > 1 else 1.0
            
            # Calculate average monthly persistence
            avg_monthly_persistence = statistics.mean(monthly_persistences)
            
            # Determine seasonal trend
            seasonal_trend = self._calculate_seasonal_trend(pattern_list)
            
            seasonal_patterns.append({
                'season': season,
                'activity_type': activity,
                'zone': zone,
                'persistence': round(long_term_persistence, 2),
                'stability': round(max(0, min(1, long_term_stability)), 2),
                'avg_monthly_persistence': round(avg_monthly_persistence, 2),
                'trend': seasonal_trend,
                'month_count': len(pattern_list)
            })
        
        return seasonal_patterns
    
    def calculate_trend(self, patterns_over_time: List[Dict]) -> str:
        """
        Calculate trend (increasing/stable/declining) for patterns over time.
        
        Args:
            patterns_over_time: Patterns with timestamps and frequency metrics
            
        Returns:
            Trend classification: 'increasing', 'stable', or 'declining'
        """
        if len(patterns_over_time) < 3:
            return 'stable'  # Insufficient data for trend detection
        
        # Extract frequency or persistence values over time
        values = []
        for pattern in patterns_over_time:
            if 'pattern_frequency' in pattern:
                values.append(pattern['pattern_frequency'])
            elif 'persistence' in pattern:
                values.append(pattern['persistence'])
            else:
                values.append(1)
        
        # Calculate trend using linear regression slope
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(xi * yi for xi, yi in zip(x, values))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return 'stable'
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        # Classify trend
        if slope > 0.05:  # Increasing threshold
            return 'increasing'
        elif slope < -0.05:  # Declining threshold
            return 'declining'
        else:
            return 'stable'
    
    def calculate_long_term_persistence(self, patterns_over_time: List[Dict]) -> float:
        """
        Calculate long-term persistence across multiple time windows.
        
        Args:
            patterns_over_time: Patterns from multiple time windows
            
        Returns:
            Long-term persistence score (0-1)
        """
        if not patterns_over_time:
            return 0.0
        
        # Count how many windows have the pattern
        windows_with_pattern = len(patterns_over_time)
        total_windows = max(len(patterns_over_time), 1)
        
        # Calculate persistence as frequency across windows
        persistence = windows_with_pattern / total_windows
        
        return round(persistence, 2)
    
    def calculate_long_term_stability(self, patterns_over_time: List[Dict]) -> float:
        """
        Calculate long-term stability (variance in pattern consistency).
        
        Args:
            patterns_over_time: Patterns from multiple time windows
            
        Returns:
            Long-term stability score (0-1)
        """
        if len(patterns_over_time) < 2:
            return 0.0
        
        # Extract frequency or persistence values
        values = []
        for pattern in patterns_over_time:
            if 'pattern_frequency' in pattern:
                values.append(pattern['pattern_frequency'])
            elif 'persistence' in pattern:
                values.append(pattern['persistence'])
            else:
                values.append(1)
        
        # Calculate stability as inverse of variance
        if len(values) < 2:
            return 0.0
        
        try:
            variance = statistics.variance(values)
            mean_value = statistics.mean(values)
            
            if mean_value == 0:
                return 0.0
            
            # Normalize variance to 0-1 scale
            stability = 1.0 - min(variance / mean_value, 1.0)
            return round(stability, 2)
        except:
            return 0.0
    
    def _calculate_monthly_trend(self, month: str, activity: str, zone: str, pattern_list: List[Dict]) -> str:
        """
        Calculate trend for a specific month based on weekly patterns.
        
        Args:
            month: Month identifier
            activity: Activity type
            zone: Zone identifier
            pattern_list: Weekly patterns for this month
            
        Returns:
            Trend classification
        """
        return self.calculate_trend(pattern_list)
    
    def _calculate_seasonal_trend(self, pattern_list: List[Dict]) -> str:
        """
        Calculate trend for a season based on monthly patterns.
        
        Args:
            pattern_list: Monthly patterns for this season
            
        Returns:
            Trend classification
        """
        return self.calculate_trend(pattern_list)
    
    def _month_to_season(self, month: str) -> str:
        """
        Convert month to season.
        
        Args:
            month: Month in YYYY-MM format
            
        Returns:
            Season identifier
        """
        try:
            month_num = int(month.split('-')[1])
            
            if month_num in [12, 1, 2]:
                return 'Q1'  # Summer (Southern Hemisphere)
            elif month_num in [3, 4, 5]:
                return 'Q2'  # Autumn
            elif month_num in [6, 7, 8]:
                return 'Q3'  # Winter
            else:
                return 'Q4'  # Spring
        except:
            return 'unknown'
    
    def generate_time_series(self, zone: str, activity_type: Optional[str] = None) -> List[Dict]:
        """
        Generate time-series data for visualization.
        
        Args:
            zone: Zone identifier
            activity_type: Optional activity type filter
            
        Returns:
            Time-series data with timestamps and metrics
        """
        time_series = []
        
        for week_data in self.weekly_history:
            timestamp = week_data['timestamp']
            patterns = week_data['patterns']
            
            for pattern in patterns:
                if pattern['zone'] != zone:
                    continue
                
                if activity_type and pattern['activity_type'] != activity_type:
                    continue
                
                time_series.append({
                    'timestamp': timestamp,
                    'activity_type': pattern['activity_type'],
                    'zone': pattern['zone'],
                    'frequency': pattern.get('pattern_frequency', 1),
                    'persistence': pattern.get('pattern_persistence', 0),
                    'stability': pattern.get('pattern_stability', 0)
                })
        
        return time_series


def print_long_horizon_results(monthly_patterns: List[Dict], seasonal_patterns: List[Dict]) -> None:
    """Print long-horizon analysis results in a readable format."""
    print("\n" + "=" * 60)
    print("LONG-HORIZON MODEL OUTPUT - MONTHLY & SEASONAL PATTERNS")
    print("=" * 60)
    
    print("\nMonthly Patterns:")
    for pattern in monthly_patterns:
        print(f"  {pattern['month']} - {pattern['activity_type']} in {pattern['zone']}:")
        print(f"    Persistence: {pattern['persistence']}")
        print(f"    Stability: {pattern['stability']}")
        print(f"    Trend: {pattern['trend']}")
    
    print("\nSeasonal Patterns:")
    for pattern in seasonal_patterns:
        print(f"  {pattern['season']} - {pattern['activity_type']} in {pattern['zone']}:")
        print(f"    Persistence: {pattern['persistence']}")
        print(f"    Stability: {pattern['stability']}")
        print(f"    Trend: {pattern['trend']}")
    
    print("\n" + "=" * 60)
    print("INVARIANT COMPLIANCE:")
    print("✓ Zero-PII: Analysis based on aggregated patterns only")
    print("✓ Coordination > Identity: Long-term patterns, not individual tracking")
    print("✓ Semantic Guard: Designed for planning, not surveillance")
    print("=" * 60)


if __name__ == "__main__":
    # Test with sample data
    print("Testing Long-Horizon Model...")
    
    model = LongHorizonModel()
    
    # Sample weekly patterns
    weekly_patterns = [
        {
            'timestamp': '2026-01-01',
            'patterns': [
                {'activity_type': 'irrigation', 'zone': 'MZUZU', 'pattern_frequency': 5},
                {'activity_type': 'milling', 'zone': 'MZUZU', 'pattern_frequency': 4}
            ]
        },
        {
            'timestamp': '2026-01-08',
            'patterns': [
                {'activity_type': 'irrigation', 'zone': 'MZUZU', 'pattern_frequency': 6},
                {'activity_type': 'milling', 'zone': 'MZUZU', 'pattern_frequency': 5}
            ]
        },
        {
            'timestamp': '2026-01-15',
            'patterns': [
                {'activity_type': 'irrigation', 'zone': 'MZUZU', 'pattern_frequency': 7},
                {'activity_type': 'milling', 'zone': 'MZUZU', 'pattern_frequency': 4}
            ]
        },
        {
            'timestamp': '2026-01-22',
            'patterns': [
                {'activity_type': 'irrigation', 'zone': 'MZUZU', 'pattern_frequency': 8},
                {'activity_type': 'milling', 'zone': 'MZUZU', 'pattern_frequency': 6}
            ]
        }
    ]
    
    # Add to history
    for week_data in weekly_patterns:
        model.add_weekly_patterns(week_data['patterns'], week_data['timestamp'])
    
    # Aggregate to monthly
    monthly_patterns = model.aggregate_weekly_to_monthly(weekly_patterns)
    
    # Aggregate to seasonal (using monthly patterns as proxy)
    seasonal_patterns = model.aggregate_monthly_to_seasonal(monthly_patterns)
    
    print_long_horizon_results(monthly_patterns, seasonal_patterns)
