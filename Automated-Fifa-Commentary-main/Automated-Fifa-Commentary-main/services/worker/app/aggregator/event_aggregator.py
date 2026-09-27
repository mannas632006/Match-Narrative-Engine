from typing import List, Dict, Optional
import time

class EventAggregator:
    """Aggregate and filter events to prevent duplicate commentary"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cooldown_period = config.get('cooldown_period', 3.0)
        self.goal_cooldown = config.get('goal_cooldown', 7.0)
        self.min_confidence = config.get('min_confidence', 0.6)
        self.batch_window = config.get('batch_window', 15.0)
        
        self.batch = []
        self.batch_start_time = 0
        self.last_event_time = {}
    
    def process(self, events: List[Dict], timestamp: float) -> Optional[List[Dict]]:
        """
        Process and aggregate events into batches
        
        Args:
            events: List of detected events
            timestamp: Current timestamp in the video (seconds)
            
        Returns:
            List of aggregated events if batch is ready, None otherwise
        """
        # Add valid events to batch
        if events:
            for event in events:
                event_type = event['event_type']
                confidence = event['confidence']
                
                # Check confidence threshold
                if confidence < self.min_confidence:
                    print(f"  [Aggregator] Ignoring {event_type} (conf: {confidence} < {self.min_confidence})")
                    continue
                
                # Check cooldown (per type) to avoid spamming same event in same batch
                # Use event-specific cooldown: goals get longer cooldown to prevent duplicates
                cooldown = self.goal_cooldown if event_type == 'goal' else self.cooldown_period
                last_time = self.last_event_time.get(event_type, -cooldown)
                if timestamp - last_time < cooldown:
                    print(f"  [Aggregator] Ignoring {event_type} (cooldown: {timestamp - last_time:.1f}s < {cooldown}s)")
                    continue
                
                # Initialize batch timer IF this is the first VALID event
                if not self.batch:
                    self.batch_start_time = timestamp

                # Add to batch
                self.last_event_time[event_type] = timestamp
                self.batch.append({
                    'event_type': event_type,
                    'confidence': confidence,
                    'timestamp': timestamp,
                    'description': event.get('description', '')
                })
        
        # Check if batch window expired
        if self.batch and (timestamp - self.batch_start_time >= self.batch_window):
            result_batch = self.batch.copy()
            self.batch = []  # Reset batch
            self.batch_start_time = 0
            return result_batch
            
        return None
    
    def reset(self):
        """Reset state for a new video"""
        self.batch = []
        self.batch_start_time = 0
        self.last_event_time = {}

    def flush(self) -> Optional[List[Dict]]:
        """Force return any remaining events in the batch"""
        if self.batch:
            result_batch = self.batch.copy()
            self.batch = []
            self.batch_start_time = 0
            return result_batch
        return None

