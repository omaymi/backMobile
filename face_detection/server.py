import asyncio
import websockets
import cv2
import dlib
import numpy as np
import pickle
import logging
import json
import io
from PIL import Image
import time
import os
import psutil
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Set CPU affinity to prioritize process
try:
    p = psutil.Process()
    p.cpu_affinity([0, 1])  # Use first two cores
    logging.info("Set CPU affinity to cores 0,1")
except Exception as e:
    logging.warning(f"Failed to set CPU affinity: {e}")

# Define model file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHAPE_PREDICTOR_PATH = os.path.join(BASE_DIR, "shape_predictor_5_face_landmarks.dat")  # Updated to 5 landmarks
FACE_RECOGNITION_MODEL_PATH = os.path.join(BASE_DIR, "dlib_face_recognition_resnet_model_v1.dat")
SSD_PROTO_PATH = os.path.join(BASE_DIR, "deploy.prototxt")
SSD_MODEL_PATH = os.path.join(BASE_DIR, "res10_300x300_ssd_iter_140000.caffemodel")

# Validate model files
for model_path in [SHAPE_PREDICTOR_PATH, FACE_RECOGNITION_MODEL_PATH, SSD_PROTO_PATH, SSD_MODEL_PATH]:
    if not os.path.isfile(model_path):
        logging.error(f"Model file not found: {model_path}")
        exit(1)
    if not os.access(model_path, os.R_OK):
        logging.error(f"Model file not readable: {model_path}")
        exit(1)
    logging.info(f"Model file verified: {model_path}")

# Load models
try:
    detector = cv2.dnn.readNetFromCaffe(SSD_PROTO_PATH, SSD_MODEL_PATH)  # OpenCV DNN SSD detector
    shape_predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
    face_recognizer = dlib.face_recognition_model_v1(FACE_RECOGNITION_MODEL_PATH)
    logging.info("Models loaded successfully")
except Exception as e:
    logging.error(f"Failed to load models: {e}")
    exit(1)

# Load known face encodings
logging.info("Loading EncodeFile.p...")
try:
    with open(os.path.join(BASE_DIR, 'EncodeFile.p'), 'rb') as file:
        known_face_encodings, known_face_names = pickle.load(file)
    unique_encodings = []
    unique_names = []
    seen_names = set()
    for enc, name in zip(known_face_encodings, known_face_names):
        if name not in seen_names:
            unique_encodings.append(np.array(enc))
            unique_names.append(name)
            seen_names.add(name)
    known_face_encodings = np.array(unique_encodings)
    known_face_names = unique_names
    logging.info(f"Encode File Loaded. Names loaded: {known_face_names}")
except Exception as e:
    logging.error(f"Failed to load EncodeFile.p: {e}")
    exit(1)

# Face processing function for parallel execution
def process_face(face, rgb_resized):
    try:
        shape = shape_predictor(rgb_resized, face)
        face_descriptor = face_recognizer.compute_face_descriptor(rgb_resized, shape)
        encoding = np.array(face_descriptor)
        distances = np.linalg.norm(known_face_encodings - encoding, axis=1)
        best_match = np.argmin(distances)
        if distances[best_match] < 0.65:
            student_name = known_face_names[best_match]
            left, top, right, bottom = face.left(), face.top(), face.right(), face.bottom()
            return {
                "id": student_name,
                "left": left * 5,  # Scale back (x5 due to 0.2 resize)
                "top": top * 5,
                "right": right * 5,
                "bottom": bottom * 5
            }
        return None
    except Exception as e:
        logging.warning(f"Error processing face: {e}")
        return None

async def process_image(websocket, path):
    logging.info("Client connected")
    try:
        async for message in websocket:
            start_total = time.time()
            if not isinstance(message, bytes):
                response = {"error": "Expected binary image data", "detections": [], "image_size": {"width": 640, "height": 480}}
                await websocket.send(json.dumps(response))
                logging.error("Expected binary image data")
                continue

            logging.info(f"Received image ({len(message)} bytes)")

            img = None
            try:
                start_time = time.time()
                image = Image.open(io.BytesIO(message))
                img = np.array(image)
                if img is None or img.size == 0:
                    raise ValueError("Invalid image array")
                h, w = img.shape[:2]
                img_resized = cv2.resize(img, (0, 0), fx=0.2, fy=0.2)  # Reduced to 20%
                rgb_resized = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
                logging.debug(f"Image loading and resizing took {time.time() - start_time:.3f}s")
            except Exception as e:
                response = {"error": f"Image processing error: {str(e)}", "detections": [], "image_size": {"width": 640, "height": 480}}
                await websocket.send(json.dumps(response))
                logging.error(f"Image processing error: {e}")
                continue

            try:
                # Detect faces with OpenCV DNN
                start_time = time.time()
                blob = cv2.dnn.blobFromImage(img_resized, 1.0, (300, 300), (104.0, 177.0, 123.0))
                detector.setInput(blob)
                detections = detector.forward()
                faces = []
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    if confidence > 0.5:
                        box = detections[0, 0, i, 3:7] * np.array([img_resized.shape[1], img_resized.shape[0], img_resized.shape[1], img_resized.shape[0]])
                        faces.append(dlib.rectangle(int(box[0]), int(box[1]), int(box[2]), int(box[3])))
                logging.debug(f"Detected {len(faces)} faces in {time.time() - start_time:.3f}s")

                # Process faces in parallel
                start_time = time.time()
                with ThreadPoolExecutor(max_workers=4) as executor:
                    detections = list(filter(None, executor.map(lambda face: process_face(face, rgb_resized), faces)))
                logging.debug(f"Processed {len(detections)} detections in {time.time() - start_time:.3f}s")
            except Exception as e:
                response = {"error": f"Face detection error: {str(e)}", "detections": [], "image_size": {"width": img.shape[1], "height": img.shape[0]}}
                await websocket.send(json.dumps(response))
                logging.error(f"Face detection error: {e}")
                continue

            response = {
                "detections": detections,
                "image_size": {"width": img.shape[1], "height": img.shape[0]}
            }

            try:
                await websocket.send(json.dumps(response))
                logging.info(f"Sent response: {len(detections)} detections, total time: {time.time() - start_total:.3f}s")
            except Exception as e:
                logging.error(f"Error sending response: {e}")
    except websockets.exceptions.ConnectionClosed:
        logging.info("Client disconnected")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

async def main():
    server = await websockets.serve(
        process_image,
        "0.0.0.0",
        8765,
        ping_interval=20,
        ping_timeout=20
    )
    logging.info("WebSocket server running on ws://0.0.0.0:8765")
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())