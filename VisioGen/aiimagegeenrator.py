import os
from PIL import Image

# Create the folder if it doesn't exist
save_directory = r"D:\Coding\Python\VisioGen\Images"
os.makedirs(save_directory, exist_ok=True)

# Initialize the client
from gradio_client import Client
client = Client("stabilityai/stable-diffusion-3-medium")


for i in range(5):
    # Predict the image
    result = client.predict(
        prompt="egypt pyramids cleopatra mummy murder slaves",
        negative_prompt="Hello!!",
        seed=0,
        randomize_seed=True,  # This ensures different images are generated each time
        width=1024,
        height=1024,
        guidance_scale=5,
        num_inference_steps=28,
        api_name="/infer"
    )

    # Extract the image path from the result tuple
    image_path = result[0]

    # Open and save the image with a unique name
    if os.path.exists(image_path):
        with Image.open(image_path) as img:
            save_path = os.path.join(save_directory, f"generated_image_{i+1}.png")
            img.save(save_path)
            print(f"Image {i+1} saved at {save_path}")
    else:
        print(f"The image path for image {i+1} does not exist.")
