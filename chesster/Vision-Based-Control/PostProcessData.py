from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import sys as sys
import os as os
sys.path.append(os.path.dirname(sys.path[0]))
from moduls.GenericSysFunctions import ImportCSV, ExportCSV
import numpy as np
import statsmodels.api as sm
from sklearn.datasets import make_regression
def reg_m(y, x):
    x = np.array(x).T
    x = sm.add_constant(x)
    results = sm.OLS(endog=y, exog=x).fit()
    return results

def lin_reg_result(X, Y, coeff):
    Z = coeff[1]*X+coeff[2]*Y+coeff[0]
    return Z

DIRPATH = os.path.dirname(__file__)
DIRPATH = "C:/Mechatroniklabor/chesster/chesster/Vision-Based-Control" #Zuhause
#DIRPATH = "C:/Users/admin/Desktop/ML/chesster/chesster/Vision-Based-Control" #Uni
Dir = DIRPATH+"/Trainingsdaten/"
X = ImportCSV(Dir, "Input4000.csv", ";")
Y = ImportCSV(Dir, "Output4000.csv", ";")
filterLin = False
fig = plt.figure()
ax = fig.add_subplot(211, projection='3d')

ax2 = fig.add_subplot(221, projection='3d')
ax.set_title(f'Raw Data n={X.shape[1]}')
ax.set_xlabel('x [px]')
ax.set_ylabel('y [px]')
ax.set_zlabel('Depth [mm]')
ax2.set_xlabel('X Robot KOS [mm]')
ax2.set_ylabel('Y Robot KOS [mm]')
ax2.set_zlabel('Z Robot KOS [mm]')
ax3 = fig.add_subplot(212, projection='3d')
ax4 = fig.add_subplot(222, projection='3d')

ax3.set_xlabel('x [px]')
ax3.set_ylabel('y [px]')
ax3.set_zlabel('Depth [mm]')
ax4.set_xlabel('X Robot KOS [mm]')
ax4.set_ylabel('Y Robot KOS [mm]')
ax4.set_zlabel('Z Robot KOS [mm]')

ax.scatter(X[0,:], X[1,:], X[2,:], c='red', marker='o')
ax2.scatter(Y[0,:], Y[1,:], Y[2,:], c='red', marker='o')

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

if filterLin == True:
    result = reg_m(X[2,:], X[0:2,:])
    print(result.summary())

    coeff = result.params
    print(coeff)
    x_reg = np.linspace(np.min(X[0,:]), np.max(X[0,:]), num=500)
    y_reg = np.linspace(np.min(X[1,:]),np.max(X[1,:]), num=500)
    meshx, meshy = np.meshgrid(x_reg, y_reg)
    Z_reg = coeff[1]*meshx+coeff[2]*meshy+coeff[0]
    z_scatter = coeff[1]*X[0,0]+coeff[2]*X[1,0]+coeff[0]
    surf = ax.plot_surface(meshx, meshy, Z_reg,
                        linewidth=0, antialiased=False)
    ax.scatter(X[0,0], X[1,0], z_scatter, c='green', marker="*")
    print(X.shape[1])

    sigma = 40

    X = X[:, X_Hat[2,:]>lin_reg_result(X_Hat[0,:], X_Hat[1,:], coeff)-sigma]
    Y = Y[:, X_Hat[2,:]>lin_reg_result(X_Hat[0,:], X_Hat[1,:], coeff)-sigma]
    X_Hat = X.copy()
    X = X[:, X_Hat[2,:]<lin_reg_result(X_Hat[0,:], X_Hat[1,:], coeff)+sigma]
    Y = Y[:, X_Hat[2,:]<lin_reg_result(X_Hat[0,:], X_Hat[1,:], coeff)+sigma]
    print(X.shape[1])

ax3.scatter(X[0,:], X[1,:], X[2,:], c='red', marker='o')
ax4.scatter(Y[0,:], Y[1,:], Y[2,:], c='red', marker='o')
DIRPATH = os.path.dirname(__file__)
DirOutput = DIRPATH+"/Trainingsdaten/"
ExportCSV(X, DirOutput, f'Input{X.shape[1]}Filtered_newData.csv', ';')
ExportCSV(Y, DirOutput, f'Output{X.shape[1]}Filtered_newData.csv', ';')
ax3.set_title(f'Filtered Data n={X.shape[1]}')
plt.show()
