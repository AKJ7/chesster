# Borrowed from https://www.kaggle.com/sagaramu/yolo3-object-detection-from-scratch-easy-way

from __future__ import division
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import numpy as np
from tqdm import tqdm_notebook
from matplotlib import pyplot as plt
from matplotlib import patches as patches
import math
import time
import tqdm
import torchvision.transforms as transforms
from PIL import Image
import cv2
import warnings
from chesster.obj_recognition.nn.yolo_utils import *


class EmptyLayer(nn.Module):
    """Placeholder for 'route' and 'shortcut' layers"""

    def __init__(self):
        super(EmptyLayer, self).__init__()


class YOLOLayer(nn.Module):
    """Detection layer"""

    def __init__(self, anchors, num_classes, img_dim=416):
        super(YOLOLayer, self).__init__()
        self.anchors = anchors
        self.num_anchors = len(anchors)
        self.num_classes = num_classes
        self.ignore_thres = 0.5
        self.mse_loss = nn.MSELoss()
        self.bce_loss = nn.BCELoss()
        self.obj_scale = 1
        self.noobj_scale = 100
        self.metrics = {}
        self.img_dim = img_dim
        self.grid_size = 0  # grid size

    def compute_grid_offsets(self, grid_size, cuda=True):
        self.grid_size = grid_size
        g = self.grid_size
        FloatTensor = torch.cuda.FloatTensor if cuda else torch.FloatTensor
        self.stride = self.img_dim / self.grid_size
        # Calculate offsets for each grid
        self.grid_x = torch.arange(g).repeat(g, 1).view([1, 1, g, g]).type(FloatTensor)
        self.grid_y = torch.arange(g).repeat(g, 1).t().view([1, 1, g, g]).type(FloatTensor)
        self.scaled_anchors = FloatTensor([(a_w / self.stride, a_h / self.stride) for a_w, a_h in self.anchors])
        self.anchor_w = self.scaled_anchors[:, 0:1].view((1, self.num_anchors, 1, 1))
        self.anchor_h = self.scaled_anchors[:, 1:2].view((1, self.num_anchors, 1, 1))

    def forward(self, x, targets=None, img_dim=None):

        # Tensors for cuda support
        FloatTensor = torch.cuda.FloatTensor if x.is_cuda else torch.FloatTensor
        LongTensor = torch.cuda.LongTensor if x.is_cuda else torch.LongTensor
        ByteTensor = torch.cuda.ByteTensor if x.is_cuda else torch.ByteTensor

        self.img_dim = img_dim
        num_samples = x.size(0)
        grid_size = x.size(2)

        prediction = (
            x.view(num_samples, self.num_anchors, self.num_classes + 5, grid_size, grid_size)
            .permute(0, 1, 3, 4, 2)
            .contiguous()
        )

        # Get outputs
        x = torch.sigmoid(prediction[..., 0])  # Center x
        y = torch.sigmoid(prediction[..., 1])  # Center y
        w = prediction[..., 2]  # Width
        h = prediction[..., 3]  # Height
        pred_conf = torch.sigmoid(prediction[..., 4])  # Conf
        pred_cls = torch.sigmoid(prediction[..., 5:])  # Cls pred.

        # If grid size does not match current we compute new offsets
        if grid_size != self.grid_size:
            self.compute_grid_offsets(grid_size, cuda=x.is_cuda)

        # Add offset and scale with anchors
        pred_boxes = FloatTensor(prediction[..., :4].shape)
        pred_boxes[..., 0] = x.data + self.grid_x
        pred_boxes[..., 1] = y.data + self.grid_y
        pred_boxes[..., 2] = torch.exp(w.data) * self.anchor_w
        pred_boxes[..., 3] = torch.exp(h.data) * self.anchor_h

        output = torch.cat(
            (
                pred_boxes.view(num_samples, -1, 4) * self.stride,
                pred_conf.view(num_samples, -1, 1),
                pred_cls.view(num_samples, -1, self.num_classes),
            ),
            -1,
        )

        if targets is None:
            return output, 0
        else:
            iou_scores, class_mask, obj_mask, noobj_mask, tx, ty, tw, th, tcls, tconf = build_targets(
                pred_boxes=pred_boxes,
                pred_cls=pred_cls,
                target=targets,
                anchors=self.scaled_anchors,
                ignore_thres=self.ignore_thres,
            )

            # Loss : Mask outputs to ignore non-existing objects (except with conf. loss)
            loss_x = self.mse_loss(x[obj_mask], tx[obj_mask])
            loss_y = self.mse_loss(y[obj_mask], ty[obj_mask])
            loss_w = self.mse_loss(w[obj_mask], tw[obj_mask])
            loss_h = self.mse_loss(h[obj_mask], th[obj_mask])
            loss_conf_obj = self.bce_loss(pred_conf[obj_mask], tconf[obj_mask])
            loss_conf_noobj = self.bce_loss(pred_conf[noobj_mask], tconf[noobj_mask])
            loss_conf = self.obj_scale * loss_conf_obj + self.noobj_scale * loss_conf_noobj
            loss_cls = self.bce_loss(pred_cls[obj_mask], tcls[obj_mask])
            total_loss = loss_x + loss_y + loss_w + loss_h + loss_conf + loss_cls

            # Metrics
            cls_acc = 100 * class_mask[obj_mask].mean()
            conf_obj = pred_conf[obj_mask].mean()
            conf_noobj = pred_conf[noobj_mask].mean()
            conf50 = (pred_conf > 0.5).float()
            iou50 = (iou_scores > 0.5).float()
            iou75 = (iou_scores > 0.75).float()
            detected_mask = conf50 * class_mask * tconf
            precision = torch.sum(iou50 * detected_mask) / (conf50.sum() + 1e-16)
            recall50 = torch.sum(iou50 * detected_mask) / (obj_mask.sum() + 1e-16)
            recall75 = torch.sum(iou75 * detected_mask) / (obj_mask.sum() + 1e-16)
            self.metrics = {
                "loss": to_device(total_loss).item(),
                "x": to_device(loss_x).item(),
                "y": to_device(loss_y).item(),
                "w": to_device(loss_w).item(),
                "h": to_device(loss_h).item(),
                "conf": to_device(loss_conf).item(),
                "cls": to_device(loss_cls).item(),
                "cls_acc": to_device(cls_acc).item(),
                "recall50": to_device(recall50).item(),
                "recall75": to_device(recall75).item(),
                "precision": to_device(precision).item(),
                "conf_obj": to_device(conf_obj).item(),
                "conf_noobj": to_device(conf_noobj).item(),
                "grid_size": grid_size,
            }
            return output, total_loss


class Yolomini(nn.Module):
    def __init__(self, num_classes, img_dim=416):
        super(Yolomini, self).__init__()
        self.num_classes = num_classes
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 16, 3, 1, 1, bias=False),  # 0
            nn.BatchNorm2d(16),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.pool1 = nn.MaxPool2d(2, 2, 0)  # 1
        self.conv2 = nn.Sequential(
            nn.Conv2d(16, 32, 3, 1, 1, bias=False),  # 2
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.pool2 = nn.MaxPool2d(2, 2, 0)  # 3
        self.conv3 = nn.Sequential(
            nn.Conv2d(32, 64, 3, 1, 1, bias=False),  # 4
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.pool3 = nn.MaxPool2d(2, 2, 0)  # 5
        self.conv4 = nn.Sequential(
            nn.Conv2d(64, 128, 3, 1, 1, bias=False),  # 6
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.pool4 = nn.MaxPool2d(2, 2, 0)  # 7
        self.conv5 = nn.Sequential(
            nn.Conv2d(128, 256, 3, 1, 1, bias=False),  # 8
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.pool5 = nn.MaxPool2d(2, 2, 0)  # 9
        self.conv6 = nn.Sequential(
            nn.Conv2d(256, 512, 3, 1, 1, bias=False),  # 10
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.pool6 = nn.Sequential(
            nn.ZeroPad2d((0, 1, 0, 1)),
            nn.MaxPool2d(2, 1, 0),  # 11
        )
        self.conv7 = nn.Sequential(
            nn.Conv2d(512, 1024, 3, 1, 1, bias=False),  # 12
            nn.BatchNorm2d(1024),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.conv8 = nn.Sequential(
            nn.Conv2d(1024, 256, 1, 1, bias=False),  # 13
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.conv9 = nn.Sequential(
            nn.Conv2d(256, 512, 3, 1, 1, bias=False),  # 14
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.conv10 = nn.Conv2d(512, 6912, 1, 1)  # 15
        # TODO: Change parameters
        self.yolo1 = YOLOLayer([(81, 82), (135, 169), (344, 319)], num_classes, img_dim)
        self.route1 = EmptyLayer()  # 17
        self.conv11 = nn.Sequential(
            nn.Conv2d(256, 128, 1, 1, bias=False),  # 18
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.upsample1 = nn.Upsample(scale_factor=2, mode='nearest')  # 19
        self.route2 = EmptyLayer()  # 20
        self.conv12 = nn.Sequential(
            nn.Conv2d(384, 256, 3, 1, 1),  # 21
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.1, inplace=True),
        )
        self.conv13 = nn.Conv2d(256, 6912, 1, 1)  # 22
        # TODO: Change parameters
        self.yolo2 = YOLOLayer([(23, 27), (37, 58), (81, 82)], num_classes, img_dim)

    def forward(self, X, targets=None):
        img_dim = X.shape[2]
        loss = 0
        x1 = self.conv1(X)
        x2 = self.pool1(x1)
        x3 = self.conv2(x2)
        x4 = self.pool2(x3)
        x5 = self.conv3(x4)
        x6 = self.pool3(x5)
        x7 = self.conv4(x6)
        x8 = self.pool4(x7)
        x9 = self.conv5(x8)
        x10 = self.pool5(x9)
        x11 = self.conv6(x10)
        x12 = self.pool6(x11)
        x13 = self.conv7(x12)
        x14 = self.conv8(x13)
        x15 = self.conv9(x14)
        x16 = self.conv10(x15)
        x17, layer_loss = self.yolo1(x16, targets, img_dim)
        loss += layer_loss
        x18 = x14
        x19 = self.conv11(x18)
        x20 = self.upsample1(x19)
        x21 = torch.cat([x20, x9], 1)
        x22 = self.conv12(x21)
        x23 = self.conv13(x22)
        x24, layer_loss = self.yolo2(x23, targets, img_dim)
        loss += layer_loss
        yolo_outputs = to_device(torch.cat([x17, x24], 1))
        return yolo_outputs if targets is None else (loss, yolo_outputs)
