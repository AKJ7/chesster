from ast import Import
from chesster.moduls.GenericSysFunctions import ImportCSV, ExportCSV
import numpy as np
import matplotlib.pyplot as plt
X = ImportCSV("C:/Mechatroniklabor/chesster/chesster/resources/DataScaler/", 'ScalerDataX.csv', ';').T
Y = ImportCSV("C:/Mechatroniklabor/chesster/chesster/resources/DataScaler/", 'ScalerDataY.csv', ';').T
#self.__TRAINING_WORKSPACE = np.array([[-236.1, 267], [-1100, -520.5], [80, 162.5]]) #X; Y; Z
UniformX = np.linspace(-225, 250, 5)
#UniformY = np.linspace(-1095, -515, 5)
UniformY = np.linspace(-850, -530, 5)
UniformZ = np.linspace(40, 150, 4)

mesh = np.meshgrid(UniformX, UniformY, UniformZ)
nodes = np.array(list(zip(*(dim.flat for dim in mesh))))
fig = plt.figure()
ax1 = fig.add_subplot(211, projection='3d')

#ax1.scatter(nodes[:, 0], nodes[:, 1], nodes[:, 2], c='blue')

indeces = np.zeros((100), dtype=int)

for i, node in enumerate(nodes):
    index = (np.abs(Y[:, :]-node)).sum(axis=1).argmin()
    indeces[i] = index
Benchmarkdata_X = X[indeces, :].copy()
Benchmarkdata_Y = Y[indeces, :].copy()

ax1.scatter(Y[indeces, 0], Y[indeces, 1], Y[indeces, 2], c=Benchmarkdata_X[:,2], cmap='jet')

ax1 = fig.add_subplot(212, projection='3d')

ax1.scatter(Benchmarkdata_X[:, 0], Benchmarkdata_X[:, 1], Benchmarkdata_X[:, 2], c=Benchmarkdata_X[:,2], cmap='jet')

X = np.delete(X, indeces, axis=0).T
Y = np.delete(Y, indeces, axis=0).T

ExportCSV(Benchmarkdata_X, "C:/Mechatroniklabor/chesster/chesster/vision_based_control/evaluation_data", "benchmark_data_input.csv", ';')
ExportCSV(Benchmarkdata_Y, "C:/Mechatroniklabor/chesster/chesster/vision_based_control/evaluation_data", "benchmark_data_output.csv", ';')
ExportCSV(X, "C:/Mechatroniklabor/chesster/chesster/vision_based_control/evaluation_data", f"TestDataInput{X.shape[1]}.csv", ';')
ExportCSV(Y, "C:/Mechatroniklabor/chesster/chesster/vision_based_control/evaluation_data", f"TestDataOutput{Y.shape[1]}.csv", ';')

plt.show()