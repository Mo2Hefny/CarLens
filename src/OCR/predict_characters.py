import cv2
import os
import numpy as np
import logging
import joblib
from extract_features import extract_combined_features
from commonfunctions import show_images


def predict_characters(characters):
    print("Current working directory:", os.getcwd())
    model = joblib.load("../../models/character_recognition_svm.pkl")
    character_features = []
    for ch in characters:
        show_images([ch])
        ch = cv2.resize(ch, (28, 42))
        show_images([ch])
        character_features.append(extract_combined_features(ch))
    predictions = model.predict(character_features)
    return predictions
