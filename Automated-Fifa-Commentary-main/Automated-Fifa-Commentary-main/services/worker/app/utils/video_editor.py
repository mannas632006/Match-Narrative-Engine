import os
import tempfile
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
from pathlib import Path

class VideoEditor:
    @staticmethod
    def add_commentary_to_video(video_path, audio_segments, output_path):
        """
        Overlays multiple audio segments onto a video at specific timestamps.
        
        Args:
            video_path (str): Path to the original video file.
            audio_segments (list): List of dicts with 'timestamp' and 'audio_raw' keys.
            output_path (str): Where to save the final video.
        """
        print(f"Adding {len(audio_segments)} commentary segments to {video_path}...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Load the base video
        video = VideoFileClip(video_path)
        
        # Create a list of audio clips with offsets
        audio_clips = []
        
        # Keep track of temporary files to clean up later
        temp_files = []
        
        try:
            for i, segment in enumerate(audio_segments):
                timestamp = segment['timestamp']
                audio_raw = segment['audio_raw']
                
                # Write raw bytes to a temporary file
                # MoviePy needs a file path to load audio
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(audio_raw)
                    temp_path = f.name
                    temp_files.append(temp_path)
                
                # Load the audio clip and set its start time
                audio_clip = AudioFileClip(temp_path).with_start(timestamp)
                audio_clips.append(audio_clip)
            
            # Combine all audio clips
            # We also include the original video's audio if it exists
            final_audio_elements = audio_clips
            if video.audio:
                final_audio_elements.append(video.audio)
            
            final_audio = CompositeAudioClip(final_audio_elements)
            
            # Set the new audio to the video
            final_video = video.with_audio(final_audio)
            
            # Write the result
            print(f"Exporting final video to {output_path}...")
            # Using low audio bitrate/quality to speed up processing if needed, 
            # but default should be fine.
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            print("Video exported successfully!")
            
        finally:
            # Cleanup resources
            video.close()
            for clip in audio_clips:
                clip.close()
            for temp_path in temp_files:
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Warning: Could not remove temporary file {temp_path}: {e}")

if __name__ == "__main__":
    # Test script if run directly
    pass
