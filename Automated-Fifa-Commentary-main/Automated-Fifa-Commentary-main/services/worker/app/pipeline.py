import asyncio
import yaml
from pathlib import Path
from dotenv import load_dotenv
from app.detectors.yolo_detector import YOLODetector
from app.trackers.bytetrack_wrapper import ByteTrackWrapper
from app.classifiers.video_classifier import VideoClassifier
from app.aggregator.event_aggregator import EventAggregator
from app.nlp.commentary_generator import CommentaryGenerator
from app.tts.piper_tts import PiperTTS
from app.utils.video_reader import VideoReader
from app.config import Config

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

class CommentaryPipeline:
    def __init__(self, config_path: str):
        self.config = Config(config_path)
        
        # Initialize components
        print("Initializing pipeline components...")
        self.detector = YOLODetector(self.config.detection)
        self.tracker = ByteTrackWrapper(self.config.tracking)
        self.classifier = VideoClassifier(self.config.classification)
        self.aggregator = EventAggregator(self.config.aggregation)
        self.commentary_gen = CommentaryGenerator(self.config.commentary)
        self.tts = PiperTTS(self.config.tts)
        print("Pipeline ready!")
    
    async def handle_results(self, batch, frame_id, reader, job_id, callback=None):
        """Handle generated commentary results (publish to Redis or call callback)"""
        if not batch: return
        
        # Calculate duration of the batch/clip
        total_duration = reader.frame_count / reader.fps if reader.fps > 0 else 0
        
        # Generate commentary
        commentary = self.commentary_gen.generate(batch, duration=total_duration)
        print(f"[Frame {frame_id}] Commentary: {commentary}")
        
        # Generate audio if TTS is enabled
        audio_data = None
        if self.tts:
            audio_data = self.tts.synthesize(commentary)

        # Determine event type and timestamp
        if isinstance(batch, list) and batch:
            primary_event = max(batch, key=lambda x: x.get('confidence', 0))
            event_type = primary_event.get('event_type', 'unknown')
            
            # Commentary covers the entire video duration chronologically,
            # so it should always start at the beginning (timestamp 0.0)
            actual_timestamp = 0.0
        else:
            event_type = batch.get('event_type', 'unknown') if batch else 'unknown'
            actual_timestamp = 0.0

        commentary_data = {
            'frame_id': frame_id,
            'commentary': commentary,
            'timestamp': actual_timestamp,
            'event_type': event_type
        }
        
        # If we have audio, encode it for transmission (base64)
        if audio_data:
            import base64
            commentary_data['audio_b64'] = base64.b64encode(audio_data).decode('utf-8')
            commentary_data['audio_raw'] = audio_data # Keep raw bytes for local use
        
        # Send to callback if provided
        if callback:
            if asyncio.iscoroutinefunction(callback):
                await callback(commentary_data)
            else:
                callback(commentary_data)


    async def process_video(self, video_path: str, job_id: str, callback=None):
        """Process a video and generate commentary"""
        try:
            print(f"Processing video: {video_path}")
            
            # Reset aggregator state for new video
            self.aggregator.reset()
            
            reader = VideoReader(video_path)
            print(f"Video info: {reader.frame_count} frames, {reader.fps} fps")
            

            frame_count = 0
            last_frame_id = 0
            
            for frame_id, frame in enumerate(reader):
                frame_count += 1
                last_frame_id = frame_id
                
                # Process every 90th frame for efficiency
                if frame_id % 90 != 0:
                    continue
                
                # Detect objects
                detections = self.detector.detect(frame)
                print(f"[Frame {frame_id}] Detected {len(detections)} objects")
                
                # Track objects
                tracks = self.tracker.update(detections, frame)
                
                # Classify events
                current_ts = frame_id / reader.fps if reader.fps > 0 else 0
                events = self.classifier.classify(frame, tracks, current_ts)
                
                # Debug: print events detected
                if events:
                    print(f"[Frame {frame_id}] Events: {events}")
                
                # Aggregate events
                current_ts = frame_id / reader.fps if reader.fps > 0 else 0
                aggregated = self.aggregator.process(events, current_ts)
                
                if aggregated:
                    await self.handle_results(aggregated, frame_id, reader, job_id, callback)
                
                # Small delay
                await asyncio.sleep(0.01)
            
            # Flush remaining events at the end
            print("Flushing remaining events...")
            flushed_batch = self.aggregator.flush()
            if flushed_batch:
                await self.handle_results(flushed_batch, last_frame_id, reader, job_id, callback)
            
            print(f"Processed {frame_count} total frames")
            print(f"Job {job_id} completed!")
            
        except Exception as e:
            print(f"Error processing video: {e}")
            import traceback
            traceback.print_exc()

