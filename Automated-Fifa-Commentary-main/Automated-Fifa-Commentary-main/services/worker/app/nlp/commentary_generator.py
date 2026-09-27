from typing import Dict
import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CommentaryGenerator:
    """Generate natural language commentary from events using OpenAI"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.use_openai = True
            print("OpenAI GPT enabled for commentary generation")
        else:
            self.client = None
            self.use_openai = False
            print("Warning: OpenAI GPT disabled for commentary (no API key found)")
    
    
    def generate(self, events: object, duration: float = 0.0) -> str:
        """
        Generate commentary for an event or list of events
        
        Args:
            events: Single event dict or List of event dicts
            duration: Total duration of the clip in seconds
            
        Returns:
            Commentary text
        """
        # Handle single event for backward compatibility
        if isinstance(events, dict):
            events = [events]
            
        if not events:
            return ""
            
        # Use OpenAI if available
        if self.use_openai and self.client:
            return self._generate_with_openai(events, duration)
        
        return ""
    
    def _generate_with_openai(self, events: list, duration: float) -> str:
        """Generate live play-by-play commentary for recent events"""
        try:
            # Sort events chronologically to help LLM follow the timeline
            sorted_events = sorted(events, key=lambda x: x.get('timestamp', 0))
            
            descriptions = []
            for e in sorted_events:
                etype = e.get('event_type', 'unknown')
                desc = e.get('description', '')
                ts = e.get('timestamp', 0)
                # Include timestamp for LLM to understand event timing and pacing
                descriptions.append(f"- [{ts:.1f}s] {etype}: {desc}")
            
            events_str = "\n".join(descriptions)
            
            # Debug: Print events being sent to LLM
            print(f"[Commentary Generator] Generating commentary for {len(sorted_events)} events:")
            print(f"{events_str}")
            
            # Match commentary length to video duration 
            # Broadcast speed is ~130-150 words per minute (2.2-2.5 words/sec)
            # We target a slightly lower density (2.2) to ensure the narration has breathing room
            target_words = max(15, int(duration * 2.2))
            
            system_prompt = f"""You are a professional football commentator broadcasting a high-stakes match.

CRITICAL TIMING RULES:
1. PACE BASED ON TIMESTAMPS: The timestamps show WHEN each event occurs. You MUST pace your commentary to match these timings.
   - If events are 3 seconds apart, spend ~3 seconds worth of narration between them
   - If events are 10 seconds apart, fill that gap with build-up, tension, and scene-setting
   - Match your word count to the time gaps between events

2. FILL TIME GAPS NATURALLY: Between events, describe:
   - Player movements and positioning
   - Ball possession and passing
   - Crowd atmosphere and tension
   - Tactical plays developing
   - Anticipation building

3. MANDATORY EVENTS: You MUST describe EVERY event in the sequence at the right point in your narration.

4. CLIMAX: If a GOAL exists, it IS the climax. Celebrate it with extreme energy (\"GOAL!!!\", \"It's in!\", \"Incredible finish!\").

5. NATURAL FLOW: Never mention specific times or timestamps - just pace your narration to match the timing.

6. FORMAT: Exactly ONE continuous paragraph. No meta-talk.

7. TARGET LENGTH: {target_words} words (approximately {duration:.1f} seconds of narration).

EXAMPLE: If events are at [5s] possession, [8s] pass, [12s] shot, [15s] goal:
- Start with possession (0-5s worth of narration)
- Build tension during the pass (5-8s worth)
- Increase excitement for the shot (8-12s worth)
- Explode with celebration for the goal (12-15s worth)
"""

            prompt = f"EVENT SEQUENCE:\n{events_str}\n\nCOMMENTARY:"
            
            # Use max_tokens from config or fallback to 250
            max_tokens = self.config.get('max_tokens', 250)
            
            response = self.client.chat.completions.create(
                model=self.config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens, 
                temperature=0.7
            )
            
            commentary = response.choices[0].message.content.strip()
            
            # Post-processing: only truncate if significantly longer than target
            # Allow some flexibility for natural sentence endings
            words = commentary.split()
            if len(words) > target_words + 15:  # Increased tolerance from +5 to +15
                truncated = " ".join(words[:target_words+10])
                last_period = truncated.rfind('.')
                if last_period > 0:
                    commentary = truncated[:last_period+1]
                else:
                    commentary = truncated + "..."
            
            return commentary
                
        except Exception as e:
            print(f"OpenAI error: {e}")
            return ""
