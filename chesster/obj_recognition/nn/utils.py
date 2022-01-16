import numpy as np
import torch
import cv2 as cv
import albumentations as A
from albumentations.pytorch import ToTensorV2
from matplotlib import pyplot as plt


DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
CLASSES = ['q', 'k', 'b', 'p', 'n', 'r', 'B', 'K', 'N', 'P', 'Q', 'R']


class Averager:
    def __init__(self):
        self.current_total = 0.0
        self.iterations = 0

    def send(self, value):
        self.current_total += value
        self.iterations += 1

    @property
    def value(self):
        return 0 if self.iterations == 0 else self.current_total / self.iterations

    def reset(self):
        self.current_total = 0.0
        self.iterations = 0


def get_train_transform():
    return A.Compose([
        A.Flip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.MotionBlur(p=0.2),
        A.MedianBlur(blur_limit=3, p=0.1),
        A.Blur(blur_limit=3, p=0.1),
        ToTensorV2(p=1.0)
    ], bbox_params=A.BboxParams('pascal_voc', ['labels']))


def get_valid_transform():
    return A.Compose([
        ToTensorV2(p=1.0)
    ], bbox_params=A.BboxParams('pascal_vox', ['labels']))


def visualize_sample(image, target, use_matplotlib=False):
    boxes = target['boxes']
    labels = target['labels']
    for box, label in zip(boxes, labels):
        xmin, ymin, xmax, ymax = map(int, box)
        cv.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv.putText(image, CLASSES[int(label) - 1], (xmin, ymin - 5 if ymin - 5 > 0 else ymax + 5),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    if use_matplotlib:
        image = np.clip(image, 0.0, 1.0)
        plt.axis('off')
        plt.imshow(image)
        plt.show()
    else:
        cv.imshow('image', cv.cvtColor(image, cv.COLOR_RGB2BGR))
        cv.waitKey(0)


def collate_fn(batch):
    return tuple(zip(*batch))



