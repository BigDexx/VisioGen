import random
import os
from moviepy.editor import VideoFileClip, AudioFileClip

# Define the paths
minecraft_video_path = r"D:\Coding\Python\VisioGen\Minecraft Parkour Gameplay No Copyright (4K) (1).mp4"
gta_video_path = r"D:\Coding\Python\VisioGen\GTA 5 MEGA RAMP ▸ NO COPYRIGHT GAMEPLAY _ 4K 60FPS _ 469 - Dope Gameplays (1080p60, h264, youtube) (1).mp4"
cod_video_path =r"D:\Coding\Python\VisioGen\COD Black Ops 6 Gameplay - Free To Use - No Copyright Gameplay (1080p60, h264, youtube) (1).mp4"
db_video_path=r"D:\Coding\Python\VisioGen\Dragon Ball_ Sparking ZERO Gameplay - No Commentary - No Copyright Gameplay (1080p60, h264, youtube) (1).mp4"
audio_path = r"D:\Coding\Python\VisioGen\output.mp3"

# Load audio clip   
audio_clip = AudioFileClip(audio_path)

def process_video(video_path):
    # Load video clip
    clip = VideoFileClip(video_path)

    # Get the duration of the audio clip
    audio_duration = audio_clip.duration

    # Calculate the minimum start time after 3 minutes (180 seconds)
    min_start_time = 180
    max_start_time = clip.duration - audio_duration  # Ensure start time doesn't exceed available duration

    # Choose a random start time after 3 minutes
    start_time = random.uniform(min_start_time, max_start_time)

    # Calculate end time based on audio duration
    end_time = start_time + audio_duration  
    if end_time > clip.duration:
        end_time = clip.duration

    # Get a random subclip from the video with the same duration as the audio clip
    random_clip = clip.subclip(start_time, end_time)

    # Set audio for the video clip
    final_clip = random_clip.set_audio(audio_clip)

    # Construct the output path to save in the same directory as the script
    output_path = os.path.join(os.path.dirname(video_path), "random_subclip_with_audio.mp4")

    # Write the subclip to a file with the audio
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", ffmpeg_params=["-preset", "ultrafast"])

    print(f"Video saved at: {output_path}")

if __name__ == "__main__":
    # Get the video type from the environment variable set in app.py
    video_type = os.environ.get('VIDEO_TYPE')

    # Switch case equivalent in Python (using if-else)
    if video_type == 'Minecraft':
        print("Processing Minecraft video...")
        process_video(minecraft_video_path)
    elif video_type == 'GTA':
        print("Processing GTA video...")
        process_video(gta_video_path)
    elif video_type == 'COD':
        print("Processing COD video...")
        process_video(cod_video_path)
    elif video_type == 'Dragon Ball':
        print("Processing Dragon Ball video...")
        process_video(db_video_path)        
    else:
        print(f"Unknown video type: {video_type}. Defaulting to Minecraft.")
        process_video(minecraft_video_path)
