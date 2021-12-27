import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import RMSprop, SGD
from tensorflow.keras.layers import Dense, Input, Dropout, Flatten
from tensorflow.keras.callbacks import TensorBoard
import tensorflow as tf
from sklearn.datasets import make_regression
import os as os
import sys as sys
from RadialBasisFunctionNetworks.rbflayer import RBFLayer
from tensorflow.python.util.nest import _yield_flat_up_to
sys.path.append(os.path.dirname(sys.path[0]))
from moduls.GenericSysFunctions import ImportCSV
import time as time

def get_Model_NN(n_input, n_output, n_Dense, n_nodes):
    model = Sequential() #Current Model: Multi-Output-Regression NN
    model.add(Dense(n_nodes, input_dim=n_input, kernel_initializer='he_uniform', activation='relu')) #INPUT-LAYER
    #model.add(Dropout(0.15))
    for i in range(n_Dense):
        model.add(Dense(n_nodes, activation='relu', kernel_initializer='he_uniform')) #i Hidden-Layer
    model.add(Dense(n_output)) #OUTPUT-LAYER
    NAME = f'nD{n_Dense}_nN{n_nodes}'
    NAME = f'Test{time.time()}'
    return model, NAME

def get_Model_RBF(n_input, n_output, n_nodes, n_nodes2, n):
    model = Sequential()
    model.add(Dense(n_nodes, input_shape=(n_input,)))
    model.add(RBFLayer(n_nodes2, 0.5))
    model.add(Dense(n_output))

    model.compile(optimizer='rmsprop', loss='binary_crossentropy', metrics=['accuracy'])
    NAME = f'RBF_Network'
    return model, NAME

def get_Data_test():
    X, Y = make_regression(n_samples=1000, n_features=3, n_informative=3, n_targets=3, random_state=2, noise=0.1)
    X_Norm = 2.*(X - np.min(X))/np.ptp(X)-1 #normalization
    Y_Norm = 2.*(Y - np.min(Y))/np.ptp(Y)-1 #normalization
    return X_Norm, Y_Norm, X, Y

def get_Data():
    DIRPATH = os.path.dirname(__file__)
    Dir = DIRPATH+"/Trainingsdaten/"
    X = ImportCSV(Dir, "Input850.csv", ";")
    X = np.round(X, 2)
    Y = ImportCSV(Dir, "Output850.csv", ";")
    Y = np.round(Y, 2)
    X_Hat = X.copy()
    X = X[:, X_Hat[2,:]>500]
    Y = Y[:, X_Hat[2,:]>500]
    X_Hat = X.copy()

    X = X[:, X_Hat[2,:]<1100] #1500
    Y = Y[:, X_Hat[2,:]<1100] #1500
    X_Hat = X.copy()

    #sigma = np.std(X[2,:], dtype=np.float64)
    #my = np.mean(X[2,:], dtype=np.float64)

    #X = X[:, X_Hat[2,:]>my-sigma]
    #Y = Y[:, X_Hat[2,:]>my-sigma]
    #X_Hat = X.copy()

    #X = X[:, X_Hat[2,:]<my+sigma]
    #Y = Y[:, X_Hat[2,:]<my+sigma]
    #X_Hat = X.copy()
    X = np.transpose(X)
    Y = np.transpose(Y)

    X_Norm = 2.*(X - np.min(X))/np.ptp(X)-1 #normalization
    Y_Norm = 2.*(Y - np.min(Y))/np.ptp(Y)-1 #normalization
    return X_Norm, Y_Norm, X, Y

def train():
    X, Y, X_old, Y_old = get_Data()
    n_data = X.shape[0]
    print(n_data)
    Epochs = 200
    model, NAME = get_Model_NN(3, 3, 0, 128)
    #model, NAME = get_Model_RBF(3, 3, 20, 10, n_data)
    #NAME = NAME+f"_nData{n_data}_nEpochs{Epochs}"
    #NAME = "TestREG"
    tensorboard = TensorBoard(log_dir='chesster/Vision-Based-Control/logs/'+NAME) #to start tensorboard: Navigate to Chesster Root -> CMD ->
    #tensorboard --logdir=chesster/Vision-Based-Control/logs/
    #opt = SGD(lr=0.01, momentum=0.9)
    opt = 'adam'
    model.compile(loss='mae', optimizer=opt, metrics=['accuracy'])
    model.fit(X[0:-10,0:3], Y[0:-10,0:3], epochs=Epochs, validation_split=0.2, callbacks=[tensorboard], verbose=1)
    #model.save("c:/Chesster NN Models/"+NAME, save_format='h5')
    model.save("C:/NN/"+"TEST_FLAT")

    #model.evaluate(X[-10:,0:3], Y[-10:,0:3])
    Input = X[-10:,0:3]
    #Input = Input[np.newaxis, :]
    Prediction = model.predict(Input)
    Output = Y[-10:,0:3]
    
    Output = np.round(Output, 1)
    Prediction = np.round(Prediction, 1)
    Prediction = Prediction.astype('float32')
    X = ((X+1)*np.ptp(X_old))/2+np.min(X_old)
    Output = ((Output+1)*np.ptp(Y_old))/2+np.min(Y_old)
    Prediction = ((Prediction+1)*np.ptp(Y_old))/2+np.min(Y_old)
    #print(f'Real Output: {Output}')
    #print(f'Prediction: {Prediction}')

    for i in range(Output.shape[0]):
        print('####################################################################')
        print(f'Real Output: X: {Output[i,0]}; Y: {Output[i,1]}; Z: {Output[i,2]}')
        print(f'Prediction: X: {Prediction[i,0]}; Y: {Prediction[i,1]}; Z: {Prediction[i,2]}')
        print(f'Abs. Error {i+1}. Output:  X: {abs(Prediction[i, 0]-Output[i, 0])}; Y: {abs(Prediction[i, 1]-Output[i, 1])}; Z: {abs(Prediction[i, 2]-Output[i, 2])}')
        print(f'Rel. Error {i+1}. Output:  X: {round(abs((Prediction[i, 0]-Output[i, 0])/Output[i, 0])*100)}%; Y: {round(abs((Prediction[i, 1]-Output[i, 1])/Output[i,1])*100)}%; Z: {round(abs((Prediction[i, 2]-Output[i, 2])/Output[i,2])*100)}%')
if __name__=="__main__":
    train()