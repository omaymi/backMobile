import pickle

import face_recognition
import os
import cv2

# Chemin du dossier contenant les sous-dossiers des étudiants
folderPath = 'Images'

# Initialiser les listes
studentImages = []
studentIds = []

# Parcourir chaque sous-dossier dans 'Images'
for studentFolder in os.listdir(folderPath):
    studentPath = os.path.join(folderPath, studentFolder)

    # Vérifier que c'est bien un dossier
    if not os.path.isdir(studentPath):
        continue

    # Parcourir les images dans le sous-dossier
    for imgName in os.listdir(studentPath):
        imgPath = os.path.join(studentPath, imgName)
        print(f"Chargement de l'image : {imgPath}")
        img = cv2.imread(imgPath)
        if img is not None:
            studentImages.append(img)
            studentIds.append(studentFolder.replace("_", " "))
            print(f"Image chargée avec succès : {imgPath}")
        else:
            print(f"Échec du chargement de l'image : {imgPath}")

# Afficher les IDs extraits
print("Étudiants détectés :", set(studentIds))

# Créer les encodages
def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        # Convertir l'image en RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Trouver les encodages faciaux
        encodings = face_recognition.face_encodings(img)
        if len(encodings) > 0:
            encodeList.append(encodings[0])
        else:
            print("Aucun visage détecté dans l'image.")
    return encodeList

print("Encoding started")
encodeListKnown = findEncodings(studentImages)
encodeListKnownWithIds = [encodeListKnown, studentIds]
# print(encodeListKnown)
print("Encoding finished")

file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("File Saved")