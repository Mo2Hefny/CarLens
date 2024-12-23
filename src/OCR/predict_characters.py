import cv2
import os
import numpy as np
import logging
import joblib
from extract_features import extract_combined_features


def predict_characters(characters):
    print("Current working directory:", os.getcwd())
    model = joblib.load("../../models/character_recognition_svm.pkl")
    character_features = []
    for ch in characters:
        ch = cv2.resize(ch, (28, 42))
        character_features.append(extract_combined_features(ch))
    predictions = model.predict(character_features)
    return predictions
