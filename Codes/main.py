import whisper
import os
import shutil
import cv2
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
import numpy as np

FONT_SCALE = 2
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

        transcribe_text = os.environ.get('RECEIVED_TEXT', '')  # Get the provided text from the environment variable
        if not transcribe_text:
            raise ValueError("No text provided for captions.")

        result = self.model.transcribe(self.audio_path, word_timestamps=True)  # Get word-level timestamps

        # Prepare video capture for timing
        cap = cv2.VideoCapture(self.video_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)

        provided_words = transcribe_text.split(" ")  # Provided text words
        audio_words = [word for segment in result['segments'] for word in segment['words']]  # Transcribed words from audio

        if len(provided_words) != len(audio_words):
            print("Warning: Provided text has a different word count than the transcribed audio.")

        current_frame = 0

        # Iterate over the provided words and align them with the audio word timings
        for i, word in enumerate(provided_words):
            audio_word = audio_words[i] if i < len(audio_words) else {'start': 0, 'end': 0}  # Ensure indexing doesn't fail

            start_time = audio_word['start']
            end_time = audio_word['end']
            start_frame = int(start_time * self.fps)
            end_frame = int(end_time * self.fps)

            self.text_array.append([word, start_frame, end_frame])

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
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        N_frames = 0

        # Frame extraction with progress bar
        with tqdm(total=total_frames, desc="Extracting Frames") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_image)

                # Render text for the corresponding frames
                for text_info in self.text_array:
                    if text_info[1] <= N_frames <= text_info[2]:
                        text = text_info[0]
                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_size = (text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1])
                        text_x = int((width - text_size[0]) / 2)
                        text_y = height - 200  # Place text above the bottom

                        outline_thickness = 4
                        for x_offset in [-outline_thickness, 0, outline_thickness]:
                            for y_offset in [-outline_thickness, 0, outline_thickness]:
                                draw.text((text_x + x_offset, text_y + y_offset), text, font=font, fill=(0, 0, 0))

                        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
                        break

                frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                cv2.imwrite(os.path.join(output_folder, f"{N_frames:05d}.jpg"), frame)

                N_frames += 1
                pbar.update(1)

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
transcriber.transcribe_video(caption_speed=0.95)  # No need to pass text, it uses the environment variable
transcriber.create_video(output_video_path, font)
