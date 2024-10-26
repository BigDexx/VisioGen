import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

# Define the folder where the videos are stored and the output video path
downloaded_videos_folder = r"D:\Coding\Python\VisioGen\DownloadedVideos"
output_video_path = r"D:\Coding\Python\VisioGen\customvideo.mp4"

def compile_videos():
    # Create a list to store video clips
    video_clips = []

    # Iterate over all video files in the specified folder
    for filename in os.listdir(downloaded_videos_folder):
        if filename.endswith('.mp4'):
            video_path = os.path.join(downloaded_videos_folder, filename)
            print(f"Adding video: {video_path}")
            video_clips.append(VideoFileClip(video_path))

    if video_clips:
        # Concatenate the video clips
        final_video = concatenate_videoclips(video_clips)
        # Write the final video to a file
        final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
        print(f"Compiled video saved as: {output_video_path}")
    else:
        print("No videos found to compile.")

if __name__ == "__main__":
    compile_videos()
