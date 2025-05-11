# myapp/utils.py
import cv2
import numpy as np
from django.core.files.uploadedfile import InMemoryUploadedFile

def has_qr_code(uploaded_file: InMemoryUploadedFile) -> bool:
    # 1) Read bytes & convert to OpenCV image
    uploaded_file.seek(0)
    arr = np.frombuffer(uploaded_file.read(), dtype=np.uint8)
    uploaded_file.seek(0)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return False

    # 2) Use OpenCV QRCodeDetector
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img)
    return bool(data)

