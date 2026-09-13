import cv2
import mediapipe as mp
import numpy as np


class HandLandmarkExtractor:
    """
    Extract 21 MediaPipe hand landmarks.

    Each landmark contains x, y and z coordinates:
        21 x 3 = 63 features
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
    ):
        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=min_detection_confidence,
        )

    def extract(
        self,
        image_path: str,
    ) -> np.ndarray | None:

        image = cv2.imread(image_path)

        if image is None:
            return None

        image_rgb = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

        results = self.hands.process(
            image_rgb
        )

        if not results.multi_hand_landmarks:
            return None

        hand = results.multi_hand_landmarks[0]

        features = []

        for landmark in hand.landmark:
            features.extend(
                [
                    landmark.x,
                    landmark.y,
                    landmark.z,
                ]
            )

        return np.asarray(
            features,
            dtype=np.float32,
        )

    def close(self) -> None:
        self.hands.close()