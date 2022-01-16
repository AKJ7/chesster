from chesster.obj_recognition.nn.models import create_model
from chesster.obj_recognition.nn.utils import *
from chesster.obj_recognition.nn.datasets import ChesspieceDataset
from torch.utils.data import DataLoader
import torch
from matplotlib import pyplot as plt
import time
from tqdm.auto import tqdm
import click
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def train(train_data_loader, model, criterion=None):
    logger.info('Started Training')
    train_itr = 1
    train_loss_list = []
    train_lost_hist = Averager()
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=0.001, momentum=0.9, weight_decay=0.005)
    progress_bar = tqdm(train_data_loader, total=len(train_data_loader))
    for i, data in enumerate(progress_bar):
        images, targets = data
        images = list(image.to(DEVICE) for image in images)
        targets = [{k: v.to(DEVICE) for k, v in t.items()} for t in targets]
        if criterion is None:
            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())
        else:
            pred_loc, pred_sco = model(images)
            losses = criterion(pred_loc, pred_sco, [target['boxes'] for target in targets],
                               [target['labels'] for target in targets])
        loss_value = losses.item()
        train_loss_list.append(loss_value)
        train_lost_hist.send(loss_value)
        losses.backward()
        optimizer.step()
        train_itr += 1
        progress_bar.set_description(desc=f'Loss: {loss_value: .4f}')
    logger.info('Completed Training')
    return train_loss_list, train_lost_hist


def validate(valid_data_loader, model, criterion=None):
    logger.info('Started Validation')
    progress_bar = tqdm(valid_data_loader, total=len(valid_data_loader))
    val_itr = 1
    val_loss_list = []
    val_loss_hist = Averager()
    for i, data in enumerate(progress_bar):
        images, targets = data
        images = list(image.to(DEVICE) for image in images)
        targets = [{k: v.to(DEVICE) for k, v in t.items()} for t in targets]
        with torch.no_grad():
            loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())
        loss_value = losses.item()
        val_loss_list.append(loss_value)
        val_loss_hist.send(loss_value)
        val_itr += 1
        progress_bar.set_description(desc=f'Loss: {loss_value: .4f}')
    logger.info('Completed Validation')
    return val_loss_list, val_loss_hist


@click.command()
@click.option('--model', type=click.Choice(['rcnn', 'yolo', 'ssd']), default='rcnn', help='Type of model to use')
@click.option('--action', required=True, type=click.Choice(['train', 'test']), help='What is my purpose?')
@click.option('--num_epoch', default=10, help='Maximal number of epochs')
@click.option('--batch_size', default=5, help='Dataloader batch size')
@click.option('--numb_workers', default=2, help='Number of threads to use')
@click.option('--image_path', required=True, help='Image path')
@click.option('--label_path', required=True, help='Labels path')
@click.option('--width', default=300, help='Image transform width')
@click.option('--height', default=300, help='Image transform height')
@click.option('--transform', is_flag=True, help='Transform Images for data augmentation')
@click.option('-v', '--verbose', count=True, help='Set verbosity level')
def main(model, action, image_path, label_path, width, height, transform, verbose, num_epoch, batch_size, numb_workers):
    if verbose > 0:
        logging.basicConfig(level=logging.INFO)
    num_classes = len(CLASSES)
    save_mode_epoch = 5
    model, criterion = create_model(model_name=model, num_classes=num_classes)
    # model_save_dir = os.path.dirname(__file__)
    model_save_dir = Path(__file__).parent
    if action == 'train':
        transformer = get_train_transform if transform else None
        data_shuffle = True
        action_func = train
    elif action == 'test':
        transformer = None
        data_shuffle = False
        action_func = validate
    else:
        raise ValueError(f'Unsupported action type: {action}')
    dataset = ChesspieceDataset(image_path, label_path, width, height, [], transforms=transformer())
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=data_shuffle, num_workers=numb_workers,
                             collate_fn=collate_fn)
    for epoch in range(0, num_epoch):
        logger.info(f'Epoch: {epoch + 1} / {num_epoch}')
        start = time.time()
        loss_list, lost_hist = action_func(data_loader, model, criterion)
        logger.info(f'Epoch: {epoch + 1}, Loss: {lost_hist.value: 3.2f}')
        end = time.time()
        logger.info(f'Epoch: {epoch + 1}, Duration: {((end - start) / 60): 3.2f} minutes')
        if (epoch + 1) % save_mode_epoch == 0:
            torch.save(model.state_dict(), f'{model_save_dir}/model_{epoch + 1}.pth')


if __name__ == '__main__':
    main()
