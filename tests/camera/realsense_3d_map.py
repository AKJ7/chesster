from chesster.camera.realSense import RealSenseCamera
from matplotlib import pyplot as plt
import numpy as np


if __name__ == '__main__':
    with RealSenseCamera() as camera:
        depth_image = camera.capture_depth()
        print(f'Input shape: {depth_image.shape}')
        width, height = depth_image.shape
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        ax.invert_zaxis()
        X = np.transpose(np.meshgrid(range(width), range(height), indexing='ij'), (1, 2, 0))\
            .reshape(-1, 2)
        ax.scatter(X.T[0], X.T[1], depth_image.flatten())
        plt.show()
