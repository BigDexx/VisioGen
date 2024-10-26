import whisper
import os
import shutil
import cv2
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
import numpy as np

FONT_SCALE = 2  # Set to a large value for testing (e.g., 100px font size)
FONT_THICKNESS = 2

class VideoTranscriber:
    def __init__(self, model_path, video_path):
        self.model = whisper.load_model(model_path)
        self.video_path = video_path
        self.audio_path = ''
        self.text_array = []
        self.fps = 0

    def transcribe_video(self, caption_speed=1.0):
        print('Transcribing video...')

        transcribe_text = os.environ.get('TEXT', '')
        if transcribe_text:
            print("Using provided text for captions.")
            result = {'segments': [{'text': transcribe_text, 'start': 0, 'end': VideoFileClip(self.video_path).duration}]}
        else:
            print("Transcribing from audio.")
            result = self.model.transcribe(self.audio_path)

        cap = cv2.VideoCapture(self.video_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)

        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Get total frames in the video
        comma_pause_frames = int(0.2 * self.fps)  # 200 ms pause after a comma
        full_stop_pause_frames = int(0.5 * self.fps)  # 500 ms pause after a full stop
        long_word_pause_frames = int(0.25 * self.fps)  # 700 ms pause after a long word

        # Adding loading bar for transcription
        for segment in tqdm(result["segments"], desc="Transcribing"):
            text = segment["text"]
            end = segment["end"]
            start = segment["start"]

            total_frames = int((end - start) * self.fps)

            start_frame = int(start * self.fps)
            start_frame = max(0, start_frame)  # Ensure start frame doesn't go below 0

            words = text.split(" ")
            combined_words = []
            skip_next = False

            for i, word in enumerate(words):
                if skip_next:
                    skip_next = False
                    continue

                if len(word) < 3 and i + 1 < len(words):  # Check for words with less than three letters
                    combined_words.append(word + " " + words[i + 1])  # Combine with the next word
                    skip_next = True  # Skip the next word since it's already combined
                else:
                    combined_words.append(word)

            # Calculate frames for each word
            frames_per_word = max(1, int((total_frames // len(combined_words)) * caption_speed))
            current_frame = start_frame

            for i, word in enumerate(combined_words):
                if i > 0:
                    # Apply delay based on the previous word's punctuation
                    if combined_words[i - 1].endswith(','):
                        current_frame += comma_pause_frames
                    elif combined_words[i - 1].endswith('.'):
                        current_frame += full_stop_pause_frames

                    # Apply additional delay for long words
                    if len(combined_words[i - 1]) > 9:
                        current_frame += long_word_pause_frames

                end_frame_for_word = current_frame + frames_per_word
                end_frame_for_word = min(end_frame_for_word, int(end * self.fps))

                self.text_array.append([word, current_frame, end_frame_for_word])

                # Update the current frame to the next word's start frame
                current_frame = end_frame_for_word

        if self.text_array:
            self.text_array[-1][2] = total_video_frames

        cap.release()
        print('Transcription complete.')

    def extract_audio(self):
        print('Extracting audio...')
        audio_path = os.path.join(os.path.dirname(self.video_path), "audio.mp3")
        video = VideoFileClip(self.video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        self.audio_path = audio_path
        print('Audio extracted.')

    def extract_frames(self, output_folder, font):
        print('Extracting frames...')
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Get the total number of frames for progress bar

        N_frames = 0

        # Add loading bar for frame extraction
        with tqdm(total=total_frames, desc="Extracting Frames") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert the frame to a PIL image for text rendering
                pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_image)

                # Iterate over the text segments for this frame
                for text_info in self.text_array:
                    if text_info[1] <= N_frames <= text_info[2]:
                        text = text_info[0]

                        # Get text size using Pillow font
                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_size = (text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1])
                        text_x = int((width - text_size[0]) / 2)

                        # Shift text 100 pixels above the original position
                        text_y = height - 100 - 100  # Original height - 100 (for placement) - 100 (for the shift)

                        # Draw black outline (for better visibility of the text)
                        outline_thickness = 4
                        for x_offset in [-outline_thickness, 0, outline_thickness]:
                            for y_offset in [-outline_thickness, 0, outline_thickness]:
                                draw.text((text_x + x_offset, text_y + y_offset), text, font=font, fill=(0, 0, 0))

                        # Draw the white text
                        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
                        break

                # Convert back to OpenCV image
                frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                cv2.imwrite(os.path.join(output_folder, f"{N_frames:05d}.jpg"), frame)

                N_frames += 1
                pbar.update(1)  # Update the loading bar

        cap.release()
        print(f'{N_frames} frames extracted.')

    def create_video(self, output_video_path, font):
        print('Creating video...')
        image_folder = os.path.join(os.path.dirname(self.video_path), "frames")
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        self.extract_frames(image_folder, font)

        images = sorted([img for img in os.listdir(image_folder) if img.endswith(".jpg")],
                        key=lambda x: int(x.split(".")[0]))

        clip = ImageSequenceClip([os.path.join(image_folder, image) for image in images], fps=self.fps)
        audio = AudioFileClip(self.audio_path)
        clip = clip.set_audio(audio)
        clip.write_videofile(output_video_path)

        shutil.rmtree(image_folder)
        os.remove(self.audio_path)
        print(f'Video saved at {output_video_path}')


# Function to choose the font from the environment variable passed by app.py
def choose_font():
    font = os.environ.get('SELECTED_FONT', 'Arvo-Bold')  # Default to 'Arvo-Bold' if not provided
    font_path = ""

    if font == 'naname-goma':
        font_path = r"C:\Users\Asus\Downloads\naname-goma\gomarice_naname_goma.ttf"
    elif font == 'Handscript':
        font_path = r"C:\Users\Asus\Downloads\handscript\Handscript.ttf"
    elif font == 'Shikaku-serif':
        font_path = r"C:\Users\Asus\Downloads\shikaku-serif\gomarice_shikaku_serif.ttf"
    elif font == 'Arvo-Bold':
        font_path = r"C:\Users\Asus\Downloads\arvo\Arvo-Bold.ttf"
    else:
        print("Invalid font provided. Defaulting to Arvo-Bold.")
        font_path = r"C:\Users\Asus\Downloads\arvo\Arvo-Bold.ttf"

    font_size = 60  # Adjust font size as needed
    return ImageFont.truetype(font_path, font_size)


# Example usage
model_path = "base"
video_path = r"D:\Coding\Python\VisioGen\random_subclip_with_audio.mp4"
output_video_path = r"D:\Coding\Python\VisioGen\random_subclip_with_audio(captioned).mp4"

# Initialize and use the VideoTranscriber class
transcriber = VideoTranscriber(model_path, video_path)
font = choose_font()  # Get the font from the environment variable set by app.py
transcriber.extract_audio()  # Make sure to extract audio first
transcriber.transcribe_video(caption_speed=0.95)
transcriber.create_video(output_video_path, font)
