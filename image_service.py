"""
Service de traitement d'images (OpenCV) pour les photos de patients :
détection/extraction du visage, redimensionnement, amélioration (contraste,
luminosité, réduction de bruit).
"""
import os
import uuid
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

TAILLE_STANDARD = (300, 300)


class ImageService:
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def traiter_photo_patient(self, file_storage) -> str:
        """
        Pipeline complet appliqué automatiquement à l'upload :
        1) sauvegarde temporaire, 2) détection de visage (recadrage si trouvé),
        3) amélioration (contraste/luminosité/bruit), 4) redimensionnement standard,
        5) sauvegarde définitive. Retourne le nom de fichier stocké.
        """
        filename = f"{uuid.uuid4().hex}.jpg"
        temp_path = os.path.join(self.upload_folder, f"_tmp_{filename}")
        final_path = os.path.join(self.upload_folder, filename)

        file_storage.save(temp_path)
        try:
            image = cv2.imread(temp_path)
            if image is None:
                raise ValueError("Fichier image illisible ou format non supporté.")

            image = self._extraire_visage(image)
            image = self._ameliorer(image)
            image = cv2.resize(image, TAILLE_STANDARD, interpolation=cv2.INTER_AREA)

            cv2.imwrite(final_path, image)
            return filename
        except Exception:
            logger.exception("Échec du traitement d'image patient")
            raise
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _extraire_visage(self, image: np.ndarray) -> np.ndarray:
        """Détecte le visage principal et recadre autour, avec une marge. Si
        aucun visage n'est détecté, l'image d'origine est conservée."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                                     minSize=(60, 60))
        if len(faces) == 0:
            return image

        # On prend le plus grand visage détecté
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        marge = int(0.4 * max(w, h))
        x0, y0 = max(0, x - marge), max(0, y - marge)
        x1 = min(image.shape[1], x + w + marge)
        y1 = min(image.shape[0], y + h + marge)
        return image[y0:y1, x0:x1]

    def _ameliorer(self, image: np.ndarray) -> np.ndarray:
        """Réduction de bruit + égalisation d'histogramme (contraste/luminosité) via CLAHE."""
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 6, 6, 7, 21)
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # ---------- Bonus : documents médicaux ----------

    def ameliorer_radiographie(self, chemin_entree: str, chemin_sortie: str) -> str:
        """Amélioration de contraste pour une image de radiographie en niveaux de gris."""
        image = cv2.imread(chemin_entree, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError("Radiographie illisible.")
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        ameliore = clahe.apply(image)
        cv2.imwrite(chemin_sortie, ameliore)
        return chemin_sortie
