import asyncio
import websockets
import cv2
import face_recognition
import pickle
import numpy as np
import logging
import json
import time
from PIL import Image
import io
from app import mysql
from app import create_app

app = create_app()

logging.basicConfig(level=logging.DEBUG)

# Chargement des encodages
try:
    with open('EncodeFile.p', 'rb') as file:
        encodeListKnown, studentIds = pickle.load(file)
    logging.info(f"Encode File Loaded. IDs chargés : {studentIds}")
except Exception as e:
    logging.error(f"Erreur lors du chargement de EncodeFile.p : {e}")
    exit(1)


def insert_presence(seance_id, etudiant_nom):
    with app.app_context():
        try:
            cursor = mysql.connection.cursor()
            query = "INSERT IGNORE INTO presence (seance_id, etudiant_nom) VALUES (%s, %s)"
            cursor.execute(query, (seance_id, etudiant_nom))
            mysql.connection.commit()
            logging.info(f"Présence enregistrée pour {etudiant_nom} dans la séance {seance_id}")
        except Exception as e:
            logging.error(f"Erreur MySQL : {e}")
            mysql.connection.rollback()
        finally:
            cursor.close()


async def process_image(websocket, path):
    logging.info("Client connecté")

    try:
        while True:
            # Étape 1: Recevoir le JSON avec seance_id
            try:
                json_data = await websocket.recv()
                if not isinstance(json_data, str):
                    raise ValueError("Message JSON attendu")

                data = json.loads(json_data)
                seance_id = data['seance_id']
                logging.info(f"Reçu seance_id: {seance_id}")
            except Exception as e:
                logging.error(f"Erreur JSON: {e}")
                continue

            # Étape 2: Recevoir l'image binaire
            try:
                image_data = await websocket.recv()
                if not isinstance(image_data, bytes):
                    raise ValueError("Données image attendues")

                logging.info(f"Image reçue ({len(image_data)} bytes)")
            except Exception as e:
                logging.error(f"Erreur image: {e}")
                continue

            # Traitement de l'image
            try:
                image = Image.open(io.BytesIO(image_data))
                img = np.array(image)
                img_resized = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
                rgb_resized = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            except Exception as e:
                logging.error(f"Erreur traitement image: {e}")
                continue

            # Détection des visages
            face_locations = face_recognition.face_locations(rgb_resized, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_resized, face_locations)

            # Reconnaissance
            detections = []
            detected_ids = set()
            for encoding, location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(encodeListKnown, encoding)
                face_distances = face_recognition.face_distance(encodeListKnown, encoding)
                best_match = np.argmin(face_distances)

                if matches[best_match]:
                    student_id = studentIds[best_match]
                    detected_ids.add(student_id)
                    top, right, bottom, left = location
                    detections.append({
                        "id": student_id,
                        "left": left * 4,  # Adaptation à l'échelle originale
                        "top": top * 4,
                        "right": right * 4,
                        "bottom": bottom * 4
                    })

            # Enregistrement en base
            for student_id in detected_ids:
                insert_presence(seance_id, student_id)

            # Préparation de la réponse
            response = {
                "seance_id": seance_id,
                "detections": detections,
                "image_size": {
                    "width": img.shape[1],
                    "height": img.shape[0]
                }
            }

            await websocket.send(json.dumps(response))
            logging.info("Réponse envoyée")

    except websockets.exceptions.ConnectionClosed:
        logging.info("Connexion fermée")
    except Exception as e:
        logging.error(f"Erreur générale : {e}")


# Démarrage du serveur
start_server = websockets.serve(process_image, "0.0.0.0", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()