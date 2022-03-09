from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import os as os
import matplotlib
from chesster.moduls.GenericSysFunctions import ImportCSV, ExportCSV
import numpy as np
import statsmodels.api as sm
import matplotlib.cm as cm
def reg_m(y, x):
    x = np.array(x).T
    x = sm.add_constant(x)
    results = sm.OLS(endog=y, exog=x).fit()
    return results

def lin_reg_result(X, Y, coeff):
    Z = coeff[1]*X+coeff[2]*Y+coeff[0]
    return Z

SMALL_SIZE = 16
MEDIUM_SIZE = 18
BIGGER_SIZE = 20

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=MEDIUM_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure titl

DIRPATH = os.path.dirname(__file__)
#DIRPATH = "C:/Mechatroniklabor/chesster/chesster/Vision-Based-Control" #Zuhause
#DIRPATH = "C:/Users/admin/Desktop/ML/chesster/chesster/Vision-Based-Control" #Uni
Dir = DIRPATH+"/Trainingsdaten separiert/"
Dir = "C:/Mechatroniklabor/chesster/chesster/resources/DataScaler/"
X = ImportCSV(Dir, "ScalerDataX.csv", ";")
Y = ImportCSV(Dir, "ScalerDataY.csv", ";")
filterLin = False
fig = plt.figure()
""" ax = fig.add_subplot(211, projection='3d')

ax2 = fig.add_subplot(221, projection='3d')
ax.set_title(f'Raw Data n={X.shape[1]}')
ax.set_xlabel('x [px]')
ax.set_ylabel('y [px]')
ax.set_zlabel('Depth [mm]')
ax2.set_xlabel('X Robot KOS [mm]')
ax2.set_ylabel('Y Robot KOS [mm]')
ax2.set_zlabel('Z Robot KOS [mm]') """

ax3 = fig.add_subplot(121, projection='3d')
ax4 = fig.add_subplot(122, projection='3d')

ax3.set_xlabel('x Image [px]', labelpad=12)
ax3.set_ylabel('y Image [px]', labelpad=12)
ax3.set_zlabel('Depth [mm]', labelpad=12)
ax4.set_xlabel('X Robot KOS [mm]', labelpad=12)
ax4.set_ylabel('Y Robot KOS [mm]', labelpad=12)
ax4.set_zlabel('Z Robot KOS [mm]', labelpad=12)

""" ax.scatter(X[0,:], X[1,:], X[2,:], c='red', marker='o')
ax2.scatter(Y[0,:], Y[1,:], Y[2,:], c='red', marker='o') """

print(X.shape[1])

X_Hat = X.copy()

X = X[:, X_Hat[2,:]>500]
Y = Y[:, X_Hat[2,:]>500]
X_Hat = X.copy()

X = X[:, X_Hat[2,:]<1000]
Y = Y[:, X_Hat[2,:]<1000]
X_Hat = X.copy()

X = X[:, X_Hat[0,:]!=0]
Y = Y[:, X_Hat[0,:]!=0]
X_Hat = X.copy()

X = X[:, X_Hat[0,:]<600]
Y = Y[:, X_Hat[0,:]<600]
fig.tight_layout()

ax3.scatter(X[0,:], X[1,:], X[2,:], c=X[2,:], edgecolors='0.2', marker='o', lw=0.4, s=30, cmap=cm.jet)
ax4.scatter(Y[0,:], Y[1,:], Y[2,:], c=X[2,:], edgecolors='0.2', marker='o', lw=0.4, s=30, cmap=cm.jet)
DIRPATH = os.path.dirname(__file__)
DirOutput = DIRPATH+"/Trainingsdaten/"
#ExportCSV(X, DirOutput, f'Input{X.shape[1]}Filtered_newData.csv', ';')
#ExportCSV(Y, DirOutput, f'Output{X.shape[1]}Filtered_newData.csv', ';')
ax3.set_title(f'Input Data n={X.shape[1]}')
ax4.set_title(f'Output Data n={X.shape[1]}')
plt.show()
