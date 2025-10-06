import numpy as np
import cv2

class PurpleDetector:
    @staticmethod
    def detect_purple_regions(image_path, hsv_threshold=0.1, min_purple_area=100):
        """
        Детектирует регионы с фиолетовым цветом
        """
        img = cv2.imread(image_path)
        if img is None:
            return False, 0, []
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Расширенные диапазоны для фиолетового
        lower_purple = np.array([125, 40, 40])
        upper_purple = np.array([165, 255, 255])
        
        mask = cv2.inRange(hsv, lower_purple, upper_purple)
        
        # Морфологические операции для улучшения маски
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Находим контуры фиолетовых областей
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Фильтруем маленькие области
        large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_purple_area]
        
        purple_ratio = np.sum(mask > 0) / (img.shape[0] * img.shape[1])
        has_purple = purple_ratio >= hsv_threshold and len(large_contours) > 0
        
        return has_purple, purple_ratio, large_contours


