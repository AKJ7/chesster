from torch.utils.data import Dataset
import cv2 as cv
import torch
import glob
import os
import numpy as np


class ChesspieceDataset(Dataset):
    def __init__(self, image_path, label_path, width, height, classes, transforms=None):
        self.transforms = transforms
        self.dir_path = image_path
        self.label_path = label_path
        self.height = height
        self.width = width
        self.classes = classes
        self.image_paths = glob.glob(f'{self.dir_path}/*.jpg')
        self.all_images = [image_path.split('/')[-1] for image_path in self.image_paths]
        self.all_images = sorted(self.all_images)

    def __len__(self):
        return len(self.all_images)

    def __getitem__(self, item):
        image_name = self.all_images[item]
        image_path = os.path.join(self.dir_path, image_name)
        image = cv.imread(image_path)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB).astype(np.float32)
        image_resized = cv.resize(image, (self.width, self.height))
        image_resized /= 255.0
        width, height = image_resized.shape[:2]
        annotation_filename = f'{image_name[:-4]}.txt'
        annotation_file_path = os.path.join(self.label_path, annotation_filename)
        rows = np.loadtxt(annotation_file_path, delimiter=' ', ndmin=2)
        labels = []
        boxes = []
        for row in rows:
            box_class, x, y, w, h = row
            labels.append(int(box_class))
            x_min, y_min = (x - w) * width, (y - h) * height
            x_max, y_max = (x + w) * width, (y + h) * height
            boxes.append(np.clip([x_min, y_min, x_max, y_max], 0.0, [width, height, width, height]))
        boxes = torch.as_tensor(np.array(boxes), dtype=torch.float32)
        area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0])
        labels = torch.as_tensor(labels, dtype=torch.int64)
        iscrowd = torch.zeros((boxes.shape[0], ), dtype=torch.int64)
        target = {'boxes': boxes, 'area': area, 'iscrowd': iscrowd, 'labels': labels}
        if self.transforms:
            sample = self.transforms(image=image_resized, bboxes=target['boxes'], labels=labels)
            image_resized = sample['image']
            target['boxes'] = torch.tensor(sample['bboxes'])
        else:
            image_resized = torch.as_tensor(image_resized, dtype=torch.float32).permute(2, 0, 1)
        return image_resized, target
