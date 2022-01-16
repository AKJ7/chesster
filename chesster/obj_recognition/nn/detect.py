from chesster.obj_recognition.nn.utils import DEVICE, CLASSES
from chesster.obj_recognition.nn.models import create_model
from pathlib import Path
from matplotlib import pyplot as plt
import torch
import cv2 as cv
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Detect:
    def __init__(self, model_name, state_path: Path, detection_threshold=0.6):
        model, criterion = create_model(model_name, len(CLASSES))
        self.model = model.to(DEVICE)
        self.model.load_state_dict(torch.load(state_path.absolute(), map_location=DEVICE))
        self.model.eval()
        self.detection_threshold = detection_threshold

    def classify(self, image, use_matplotlib=False):
        orig_image = image.copy()
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB).astype(np.float)
        image /= 255.0
        image = np.transpose(image, (2, 0, 1)).astype(np.float)
        image = torch.tensor(image, dtype=torch.float)
        image = torch.unsqueeze(image, 0)
        with torch.no_grad():
            outputs = self.model(image)
        outputs = [{k: v.to(DEVICE) for k, v in t.items()} for t in outputs]
        if len(outputs[0]['boxes']) != 0:
            boxes = outputs[0]['boxes'].data.numpy()
            scores = outputs[0]['scores'].data.numpy()
            boxes = boxes[scores >= self.detection_threshold].astype(np.int32)
            draw_boxes = boxes.copy()
            pred_classes = [CLASSES[i - 1] for i in outputs[0]['labels'].to(DEVICE).numpy()]
            width, height = orig_image.shape[:2]
            for j, box in enumerate(draw_boxes):
                x_min, y_min, x_max, y_max = map(int, box)
                cv.rectangle(orig_image, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
                cv.putText(orig_image, pred_classes[j], (x_min, y_min-5), cv.FONT_HERSHEY_SIMPLEX, 0.7,
                           (0, 255, 0), 2, lineType=cv.LINE_AA)
            if use_matplotlib:
                plt.axis('off')
                plt.imshow(cv.cvtColor(orig_image, cv.COLOR_BGR2RGB))
            else:
                cv.imshow('Prediction', orig_image)
                cv.waitKey(1)
            logger.info(f'Classification complete. Score: {list(zip(scores, pred_classes))}')
