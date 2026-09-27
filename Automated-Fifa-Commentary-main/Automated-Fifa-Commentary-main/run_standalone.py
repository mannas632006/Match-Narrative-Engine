import asyncio
import os
import sys
import pygame
from pathlib import Path
from dotenv import load_dotenv

# Add worker to path so we can import app.*
sys.path.append(os.path.abspath("services/worker"))

from app.pipeline import CommentaryPipeline

async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_standalone.py <path_to_video>")
        return

    video_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        return

    # Initialize Pygame Mixer for audio playback
    pygame.mixer.init()

    # Load environment variables
    load_dotenv()

    print("Initializing Standalone FIFA Commentary System...")
    
    # Initialize pipeline with root-relative config
    pipeline = CommentaryPipeline("configs/pipeline.yaml")

    # Storage for the final commentary result
    final_result = {
        'commentary': '',
        'audio_raw': None,
        'timestamp': 0.0
    }

    async def result_callback(data):
        """Callback to store the final generated commentary"""
        nonlocal final_result
        final_result['commentary'] = data.get('commentary', '')
        final_result['timestamp'] = data.get('timestamp', 0)
        final_result['audio_raw'] = data.get('audio_raw')
        
        # Print commentary immediately
        print(f"\n[Generated Commentary] {final_result['commentary']}")

    job_id = "standalone_run"
    
    print(f"\n--- Starting processing: {os.path.basename(video_path)} ---")
    print("(Press Ctrl+C to stop)\n")

    try:
        # Process the entire video. Aggregator will flush and call callback at the end.
        await pipeline.process_video(video_path, job_id, callback=result_callback)
        
        # Play the generated commentary if audio is available
        if final_result['audio_raw']:
            print("\nPlaying commentary audio...")
            try:
                temp_file = Path(f"temp_audio_{job_id}.mp3")
                temp_file.write_bytes(final_result['audio_raw'])
                
                pygame.mixer.music.load(str(temp_file))
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                
                pygame.mixer.music.unload()
                if temp_file.exists():
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error playing audio: {e}")
        
        # Save final video with commentary overlay
        if final_result['audio_raw']:
            print("\n--- Generating final video with commentary overlay ---")
            from app.utils.video_editor import VideoEditor
            
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            
            video_name = Path(video_path).stem
            output_path = output_dir / f"{video_name}_with_commentary.mp4"
            
            # Format for VideoEditor
            segments = [{
                'timestamp': final_result['timestamp'],
                'audio_raw': final_result['audio_raw']
            }]
            
            VideoEditor.add_commentary_to_video(video_path, segments, str(output_path))
            print(f"\nSuccess! Final video saved to: {output_path}")
        else:
            print("\nNo commentary generated to save.")

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nStandalone run finished.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
