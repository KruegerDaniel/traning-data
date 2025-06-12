import argparse
import base64
import json
import os

import cv2
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()

PROMPT = """You are given the following materials:

* The Python source code of an animation
* A screenshot of the initial frame
* A screenshot of the final frame

Using these three inputs, write a medium-length description of what happens in the animation from beginning to end. Imagine you're describing it to someone who is watching it.

**Guidelines:**

* Only output the description—do not include any preamble or postscript.
* Make the description feel natural, like it was written by a person describing what they saw.
* Avoid technical language, code references, or overly precise details (e.g., no hex color codes).

###
Source code: 
{source_code}
###
"""


def get_valid_frame(cap, start_frame, direction, max_attempts=5, fps=30, variance_threshold=10):
    """
    Attempts to get a valid (non-monotonous) frame by moving in a direction (forward/backward).
    """
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for i in range(max_attempts):
        frame_idx = start_frame + direction * i * int(fps)
        frame_idx = int(min(max(frame_idx, 0), total_frames - 1))

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        if not success:
            continue

        if frame.var() > variance_threshold:
            return frame

    return None


def encode_image(image_path):
    """
    Encodes an image to a base64 string.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def process_videos(video_dir, code_dir, output_dir):
    output_image_dir = os.path.join(output_dir, "screenshots")
    input_jsonl = os.path.join(output_dir, "batch_input.jsonl")
    os.makedirs(output_image_dir, exist_ok=True)
    video_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]

    with open(input_jsonl, "w", encoding="utf-8") as out_file:

        for video_file in tqdm(video_files, desc="Processing videos"):
            video_path = os.path.join(video_dir, video_file)
            base_name = os.path.splitext(video_file)[0]
            code_path = os.path.join(code_dir, base_name + ".py")

            if not os.path.exists(code_path):
                continue

            with open(code_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                continue

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            frame_first = get_valid_frame(cap, start_frame=0, direction=+1, fps=fps)
            frame_last = get_valid_frame(cap, start_frame=total_frames - 1, direction=-1, fps=fps)

            if frame_first is None or frame_last is None:
                cap.release()
                continue

            first_img_path = os.path.join(output_image_dir, f"{base_name}_first.png")
            last_img_path = os.path.join(output_image_dir, f"{base_name}_last.png")

            cv2.imwrite(first_img_path, frame_first)
            cv2.imwrite(last_img_path, frame_last)

            first_img_base64 = encode_image(first_img_path)
            last_img_base64 = encode_image(last_img_path)
            prompt_text = PROMPT.format(source_code=source_code)
            request = {
                "custom_id": base_name,
                "method": "POST",
                "url": "/v1/responses",
                "body": {
                    "model": "gpt-4.1",
                    "input": [
                        {"role": "user", "content": [
                            {"type": "input_text", "text": prompt_text},
                            {"type": "input_image", "image_url": f"data:image/png;base64,{first_img_base64}"},
                            {"type": "input_image", "image_url": f"data:image/png;base64,{last_img_base64}"}
                        ]}]
                },
            }

            cap.release()
            # Save to JSONL
            json.dump(request, out_file)
            out_file.write("\n")


#################################
# OpenAI functions
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


def upload_jsonl_file(jsonl_file_path, output_dir, source="rendered/manim_scenes"):
    """
    Uploads the JSONL file to OpenAI batch processing
    """

    batch_input_file = client.files.create(
        file=open(jsonl_file_path, "rb"),
        purpose="batch"
    )

    if not batch_input_file:
        raise ValueError("Failed to upload JSONL file.")
    print("📦File uploaded successfully:", batch_input_file.to_dict())
    batch_input_file_id = batch_input_file.id
    batch = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/responses",
        completion_window="24h",
        metadata={
            "description": "Description extraction batch",
            "source": source
        }
    )
    print("📦Batch created successfully:", batch.to_dict())
    batch_info_file = os.path.join(output_dir, "batch_info.txt")
    with open(batch_info_file, 'w') as f:
        f.write(str(batch.to_dict()))


def fetch_batch_by_id(batch_id, output_dir="../output/description_extraction"):
    """
    Fetches a batch by its ID
    """
    batch = client.batches.retrieve(batch_id)
    if not batch:
        raise ValueError(f"Batch with ID {batch_id} not found.")
    status = batch.status
    if status != "completed":
        print(f"💤 Batch {batch_id} is not completed yet. Current status: {status}")
        return
    elif batch.error_file_id:
        print(f"⚠️ Batch {batch_id} failed. Fetching error details...")
        err_response = client.files.content(batch.error_file_id)
        err_response.write_to_file(os.path.join(output_dir, "batch_errors.jsonl"))
        return

    print("✅ Batch completed. Fetching content")
    response = client.files.content(batch.output_file_id)
    response.write_to_file(os.path.join(output_dir, f'{batch_id}.jsonl'))
    print("✅Batch content saved to", f'{batch_id}.jsonl')

    token_counts = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0
    }
    descriptions = {}
    for line_num, line in enumerate(response.text.splitlines(), 1):
        try:
            entry = json.loads(line)

            # Extract custom ID and description
            custom_id = entry.get('custom_id', f"unknown_{line_num}")
            description = entry['response']['body']['output'][0]['content'][0]['text']
            descriptions[custom_id] = description

            # Count tokens
            usage = entry['response']['body']['usage']
            token_counts["input_tokens"] += usage.get("input_tokens", 0)
            token_counts["output_tokens"] += usage.get("output_tokens", 0)
            token_counts["total_tokens"] += usage.get("total_tokens", 0)
        except json.JSONDecodeError:
            print(f"⚠️ Error decoding JSON on line {line_num}: {line}")
            continue
        except Exception as e:
            print(f"⚠️ Error processing line {line_num}: {e}")
            continue
    # Save descriptions to a JSON file
    descriptions_file = os.path.join(output_dir, f'{batch_id}_descriptions.json')
    with open(descriptions_file, 'w', encoding='utf-8') as desc_file:
        json.dump(descriptions, desc_file, ensure_ascii=False, indent=4)
    print("✅Descriptions saved to", descriptions_file)

    print("Token counts for batch", token_counts)
    print(f"Assuming $8/mill output => {token_counts['output_tokens'] / 1_000_000 * 8 }")
    print(f"Assuming $2/mill input => {token_counts['input_tokens'] / 1_000_000 * 2 }")
    print(f"Estimated cost: ${token_counts['output_tokens'] / 1_000_000 * 8 + token_counts['input_tokens'] / 1_000_000 * 2:.2f}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from manim videos and save source code.")
    parser.add_argument("--video_dir", type=str, default="../rendered/manim_scenes", help="Directory of videos")
    parser.add_argument("--code_dir", type=str, default="../sampled/manim_scenes", help="Directory of source code")
    parser.add_argument("--output_dir", type=str, default="../output/description_extraction", help="Directory to save output files")
    parser.add_argument("--retrieve", action="store_true", help="Retrieve a previously created batch by ID")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    args.output_jsonl = os.path.join(args.output_dir, "batch_input.jsonl")
    if args.retrieve:
        batch_id = input("Enter the batch ID to retrieve: ")
        fetch_batch_by_id(batch_id, args.output_dir)
        exit(0)


    process_videos(
        video_dir=args.video_dir,
        code_dir=args.code_dir,
        output_dir=args.output_dir
    )
    upload_jsonl_file(args.output_jsonl, source=args.video_dir)
