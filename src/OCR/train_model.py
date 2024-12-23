import os
import cv2
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn import svm
from sklearn.model_selection import GridSearchCV
from extract_features import extract_combined_features
import numpy as np


def load_data_from_folder(folder_path, image_size=(28, 42)):
    """
    Load data and labels from a folder structure.
    Args:
        folder_path: Root folder containing subfolders for each class.
        image_size: Tuple (width, height) to resize images.
    Returns:
        X: List of feature vectors.
        y: List of labels.
    """
    X = []
    y = []

    for label in os.listdir(folder_path):
        class_path = os.path.join(folder_path, label)
        if os.path.isdir(class_path):

            for img_name in os.listdir(class_path):
                img_path = os.path.join(class_path, img_name)
                if img_name.endswith(('.png', '.jpg', '.jpeg')):
                    image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    image_resized = cv2.resize(image, image_size)
                    _, binary_img = cv2.threshold(
                        image_resized, 200, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                    feature_vector = extract_combined_features(binary_img)
                    X.append(feature_vector)
                    y.append((label))
    return np.array(X), np.array(y)


def train(templates, labels):
    X_train, X_test, y_train, y_test = train_test_split(
        templates, labels, test_size=0.2, random_state=42)
    param_grid = {'C': [0.1, 1, 10, 100],
                  'gamma': [0.0001, 0.001, 0.1, 1],
                  'kernel': ['rbf', 'poly', 'linear']}

    svc = svm.SVC(probability=True)

    model = GridSearchCV(svc, param_grid)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
    return model


def save_model(model, model_path):
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")


def main():
    templates, labels = load_data_from_folder("../../data/characters")
    model = train(templates, labels)
    save_model(model, "models/character_recognition_svm.pkl")


if __name__ == "__main__":
    print("Training model")
    main()
