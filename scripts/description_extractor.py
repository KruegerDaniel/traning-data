import os
import cv2
import json
from tqdm import tqdm

def get_valid_frame(cap, start_frame, direction, max_attempts=5, fps=30, variance_threshold=10):
    """
    Attempts to get a valid (non-monotonous) frame by moving in a direction (forward/backward).
    Args:
        cap: OpenCV VideoCapture object
        start_frame: Starting frame index
        direction: +1 for forward, -1 for backward
        max_attempts: Maximum number of skips
        fps: Frames per second (used to skip 1 second)
        variance_threshold: below this variance, frame is considered too flat
    Returns:
        frame (np.array) or None if all attempts fail
    """
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for i in range(max_attempts):
        frame_idx = start_frame + direction * i * fps
        frame_idx = int(min(max(frame_idx, 0), total_frames - 1))

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        if not success:
            continue

        if frame.var() > variance_threshold:
            return frame

    return None

# Directories
video_dir = "../rendered/manim_scenes"
code_dir = "../sampled/manim_scenes"
output_image_dir = "./screenshots"
output_jsonl = "./manim_training_set.jsonl"

# Create screenshot output directory
os.makedirs(output_image_dir, exist_ok=True)

# Collect all video files
video_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]

# Open output file
with open(output_jsonl, "w") as outfile:
    for video_file in tqdm(video_files, desc="Processing videos"):
        video_path = os.path.join(video_dir, video_file)

        # Derive base name to match with .py
        base_name = os.path.splitext(video_file)[0]  # e.g., "example_2_scene"
        code_filename = base_name + ".py"
        code_path = os.path.join(code_dir, code_filename)

        if not os.path.exists(code_path):
            continue  # Skip if no matching source code

        # Load source code
        with open(code_path, "r") as f:
            source_code = f.read()

        # Load video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            continue

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Capture first valid frame (start from frame 0, move forward)
        frame_first = get_valid_frame(cap, start_frame=0, direction=+1, fps=fps)
        if frame_first is None:
            continue
        first_img_path = os.path.join(output_image_dir, f"{base_name}_first.png")
        cv2.imwrite(first_img_path, frame_first)

        # Capture last valid frame (start from end, move backward)
        frame_last = get_valid_frame(cap, start_frame=total_frames - 1, direction=-1, fps=fps)
        if frame_last is None:
            continue
        last_img_path = os.path.join(output_image_dir, f"{base_name}_last.png")
        cv2.imwrite(last_img_path, frame_last)

        # Format data as prompt
        prompt = {
            "source_code": source_code,
            "first_frame": first_img_path,
            "last_frame": last_img_path
        }

        # Save to JSONL
        json.dump(prompt, outfile)
        outfile.write("\n")

        cap.release()
