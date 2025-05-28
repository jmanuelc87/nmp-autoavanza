import cv2
import numpy as np


class Scanner:

    def __init__(self):
        pass

    def get_document_from(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            return None

        image_copy = image.copy()

        morph = self.process_morphology(image_copy)
        cutted = self.remove_background(morph)
        edges = self.detect_edges(cutted)

        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        page = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        if len(page) == 0:
            return None

        corners = self.get_corners(page)

        if corners is None:
            return np.zeros_like(image.shape)
        else:
            corners = self.order_points(corners)
            destination = self.find_dest(corners)

            M = cv2.getPerspectiveTransform(
                np.float32(corners), np.float32(destination)
            )

            final = cv2.warpPerspective(
                image,
                M,
                (destination[2][0], destination[2][1]),
                flags=cv2.INTER_LINEAR,
            )
            
            return final

    def process_morphology(self, image: np.ndarray) -> np.ndarray:
        kernel = np.ones((5, 5), np.uint8)
        return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=3)

    def remove_background(self, image: np.ndarray) -> np.ndarray:
        mask = np.zeros(image.shape[:2], np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        rect = (20, 20, image.shape[1] - 20, image.shape[0] - 20)
        cv2.grabCut(image, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)
        return image * mask2[:, :, np.newaxis]

    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)
        canny = cv2.Canny(gray, 0, 200)
        return cv2.dilate(canny, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

    def get_corners(self, contours, factor=0.02):
        for i, c in enumerate(contours):
            epsilon = factor * cv2.arcLength(c, True)
            corners = cv2.approxPolyDP(c, epsilon, True)
            if len(corners) == 4:
                return sorted(np.concatenate(corners).tolist())
        return None

    def order_points(self, pts):
        rect = np.zeros((4, 2), dtype=np.float32)
        pts = np.array(pts)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect.astype(np.int32).tolist()

    def find_dest(self, pts):
        (tl, tr, br, bl) = pts
        
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        
        maxHeight = max(int(heightA), int(heightB))

        destination_corners = [
            [0, 0],
            [maxWidth, 0],
            [maxWidth, maxHeight],
            [0, maxHeight],
        ]

        return self.order_points(destination_corners)
