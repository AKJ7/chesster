import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from chesster.obj_recognition.nn.ssd import SSD, MultiBoxLoss
from chesster.obj_recognition.nn.yolo import Yolomini
import warnings


def create_model(model_name, num_classes, image_dim=300):
    if model_name == 'rcnn':
        model = fasterrcnn_resnet50_fpn(pretrained=False)
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predicator = FastRCNNPredictor(in_features, num_classes)
        criterion = None
    elif model_name == 'ssd':
        if image_dim != 300:
            warnings.warn(f'Expected image size: 300x300. Gotten: {image_dim}!')
        model = SSD(num_classes)
        criterion = MultiBoxLoss(priors_cxcy=model.priors_cxcy)
    elif model_name == 'yolo':
        if image_dim != 416:
            warnings.warn(f'Expected image size: 416x416. Gotten: {image_dim}!')
        model = Yolomini(num_classes, image_dim)
        criterion = None
    else:
        raise RuntimeError(f'Invalid or unsupported model name "{model_name}". Allowed: "rcnn", "yolo", "ssd"')
    return model, criterion
