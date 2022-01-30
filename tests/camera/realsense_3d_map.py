# from chesster.camera.realsense import RealSenseCamera
from matplotlib import pyplot as plt
import numpy as np


if __name__ == '__main__':
    # with RealSenseCamera() as camera:
    #     depth_image, aligned_depth_image = camera.capture_depth()
    #     depth_image = np.load('../obj_recognition/extracted.npy')
        # depth_image = np.load('img/01_26_2022_13_00_54.npy')
        depth_image = np.load('../obj_recognition/depth_map.npy')
        print(f'Input shape: {depth_image.shape}')
        width, height = depth_image.shape
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        ax.invert_zaxis()
        data = depth_image.flatten()
        norm = plt.Normalize(np.min(data), np.max(data))
        X = np.transpose(np.meshgrid(range(width), range(height), indexing='ij'), (1, 2, 0)) \
            .reshape(-1, 2)
        c = np.abs(data)
        cmhot = plt.get_cmap('hot')
        data = data.astype(np.float32)
        data[data <= 100] = np.nan
        ax.scatter(X.T[0], X.T[1], data, c=c, cmap=cmhot)
        plt.show()
