import numpy as np
from numpy.core.fromnumeric import mean
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import RMSprop, SGD, Adam, Adamax
from tensorflow.keras.layers import Dense, Input, Dropout, Flatten
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.losses import mean_absolute_percentage_error, mean_squared_logarithmic_error, mean_absolute_error, Huber
import tensorflow as tf
from sklearn.datasets import make_regression
import os as os
from tensorflow.python.eager.context import DEVICE_PLACEMENT_SILENT_FOR_INT32
from tensorflow.python.keras import activations

from tensorflow.python.ops.gen_math_ops import Exp
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import sys as sys
from RadialBasisFunctionNetworks.rbflayer import RBFLayer
from tensorflow.python.util.nest import _yield_flat_up_to
sys.path.append(os.path.dirname(sys.path[0]))
from moduls.GenericSysFunctions import ImportCSV, ExportCSV
import time as time
from sklearn.preprocessing import MinMaxScaler, StandardScaler

def get_Model_NN(n_input, n_output, n_Dense, n_nodes, dpout=False, dpval=0.05):
    model = Sequential() #Current Model: Multi-Output-Regression NN
    NAME = f'nD{n_Dense}_nN{n_nodes}'
    DPCount = 0
    model.add(Dense(n_nodes, input_dim=n_input, kernel_initializer='he_uniform', activation='relu')) #INPUT-LAYER
    for i in range(n_Dense):
        model.add(Dense(n_nodes, activation='relu', kernel_initializer='he_uniform')) #i Hidden-Layer
        if i<=n_Dense-1 and dpout==True:
            model.add(Dropout(dpval))
            DPCount = DPCount+1
    NAME = NAME+f'_DpOut{DPCount}'        
    model.add(Dense(n_output)) #OUTPUT-LAYER
    return model, NAME

def get_Model_custom(n_input, n_output, n_Dense, n_nodes, dpout=False, dpval=0.05):
    model = Sequential() #Current Model: Multi-Output-Regression NN
    Dense1 = 20
    Dense2 = 128
    Dense3 = 128
    #NAME = f"CUSTOM_NN_3x{Dense1}x{Dense2}x{Dense3}x3"
    NAME = f"CUSTOM_NN_3x{Dense1}x3"
    model.add(Dense(Dense1, input_dim=n_input, kernel_initializer='he_uniform', activation='relu')) #INPUT-LAYER
    #model.add(Dense(Dense2, activation='relu', kernel_initializer='he_uniform'))
    #model.add(Dense(Dense3, activation='relu', kernel_initializer='he_uniform'))      
    model.add(Dense(n_output)) #OUTPUT-LAYER
    return model, NAME

def get_Model_RBF(n_input, n_output, n_nodes2):
    model = Sequential()
    model.add(Flatten(input_shape=(n_input)))
    model.add(RBFLayer(n_nodes2, 0.5))
    model.add(Dense(n_output))
    NAME = f'RBF_Network_Nodes_{n_nodes2}'
    return model, NAME

def get_Data_test():
    X, Y = make_regression(n_samples=1000, n_features=3, n_informative=3, n_targets=3, random_state=2, noise=0.1)
    X_Norm = np.zeros(X.shape)
    Y_Norm = np.zeros(Y.shape)
    X_Norm[:,0] = 2.*(X[:,0] - np.min(X[:,0]))/np.ptp(X[:,0])-1
    X_Norm[:,1] = 2.*(X[:,1] - np.min(X[:,1]))/np.ptp(X[:,1])-1
    X_Norm[:,2] = 2.*(X[:,2] - np.min(X[:,2]))/np.ptp(X[:,2])-1
    Y_Norm[:,0] = 2.*(Y[:,0] - np.min(Y[:,0]))/np.ptp(Y[:,0])-1
    Y_Norm[:,1] = 2.*(Y[:,1] - np.min(Y[:,1]))/np.ptp(Y[:,1])-1
    Y_Norm[:,2] = 2.*(Y[:,2] - np.min(Y[:,2]))/np.ptp(Y[:,2])-1
    return X_Norm, Y_Norm, X, Y

def get_Data(n_out, n_in, y, Norm=1, Fixed_height=True, XName="Input389Filtered.csv", YName="Output389Filtered.csv"):
    DIRPATH = os.path.dirname(__file__)
    Dir = DIRPATH+"/Trainingsdaten/"
    X = ImportCSV(Dir, XName, ";")
    X = np.round(X, 3)
    Y = ImportCSV(Dir, YName, ";")
    Y = np.round(Y, 3)
    X = np.transpose(X)
    Y = np.transpose(Y)
    
    if Fixed_height == True:
        Y[:,2] = 120
    if Norm == 1:  
        #Normalization between -1 and 1
        scalerX = MinMaxScaler(feature_range=(-1,1))
        scalerX.fit(X[:, 0:n_in])
        X_Norm = scalerX.transform(X[:, 0:n_in])
        scalerY = MinMaxScaler(feature_range=(-1,1))
        scalerY.fit(Y[:, 0+y:n_out+y])
        Y_Norm = scalerY.transform(Y[:, 0+y:n_out+y])
    elif Norm == 2:
        #Normalization between 0 and 1
        scalerX = MinMaxScaler()
        scalerX.fit(X[:, 0:n_in])
        X_Norm = scalerX.transform(X[:, 0:n_in])
        scalerY = MinMaxScaler()
        scalerY.fit(Y[:, 0+y:n_out+y])
        Y_Norm = scalerY.transform(Y[:, 0+y:n_out+y])
    elif Norm == 3:
        scalerX = StandardScaler()
        scalerX.fit(X[:, 0:n_in])
        X_Norm = scalerX.transform(X[:, 0:n_in])
        scalerY = MinMaxScaler()
        scalerY.fit(Y[:, 0+y:n_out+y])
        Y_Norm = scalerY.transform(Y[:, 0+y:n_out+y])
    else: 
        X_Norm = X
        Y_Norm = Y
        scalerY = None
        scalerX = None

    return X_Norm, Y_Norm, X, Y, scalerX, scalerY

def train():
    DIRPATH = os.path.dirname(__file__)
    Norm = 1
    Fixed_height = False
    Shuffle = False
    n_Input = 3
    n_Output = 3
    y_variable = False
    if n_Output == 1 and y_variable == True:
        y = 1
    else:
        y = 0
    #X, Y, X_Backup, Y_Backup = get_Data_test()
    X, Y, X_Backup, Y_Backup, scalerX, scalerY = get_Data(n_Output, n_Input, y, Norm, Fixed_height, XName='Input2969Filtered.csv', YName='Output2969Filtered.csv')
    #X = X[0:600, :]
    #Y = Y[0:600, :]
    n_data = X.shape[0]
    print(n_data)

    Epochs = 1000
    batch = 50
    opt = 'adam'
    loss_fct = 'mae'
    model, NAME = get_Model_custom(n_Input, n_Output, 0, 20 , False, 0.1)
    #model, NAME = get_Model_RBF([n_Input,1], n_Output, 5)
    model.compile(loss=loss_fct, optimizer=opt, metrics=['accuracy'])
    NAME = NAME+f"_nData{n_data}_nEpochs{Epochs}_{loss_fct}_Norm_{Norm}_FH_{Fixed_height}_Input{n_Input}_Output{n_Output}_loss_{loss_fct}_batch_{batch}_Optimizer_{opt}_Test"
    tensorboard = TensorBoard(log_dir='C:/Mechatroniklabor/ChessterLogs/'+NAME) #to start tensorboard: Navigate to Chesster Root -> CMD ->
    #tensorboard --logdir=ChessterLogs/
    
    model.fit(X[0:-100,0:n_Input], Y[0:-100,:], epochs=Epochs, validation_split=0.3, callbacks=[tensorboard], verbose=1, batch_size=batch)
    
    #print('Training 1/2 done..')
    #time.sleep(2)
    #model.fit(X[-1900:-1500,0:n_Input], Y[-1900:-1500,0:n_Output], epochs=Epochs, validation_split=0.2, callbacks=[tensorboard], verbose=1, batch_size=batch)
    model.save("C:/Mechatroniklabor/ChessterModels/"+NAME ,save_format='tf')
    #model.save("C:/NN/"+"TEST_FLAT")
    
    #X, Y, X_Backup, Y_Backup = get_Data(Norm, Fixed_height, XName='Input200.csv', YName='Output200.csv')

    Input = X[-100:,0:n_Input]
    print(Input[0,:])
    Prediction = model.predict(Input)
    Output = Y[-100:,:]
    if Norm != 0:
        Output = scalerY.inverse_transform(Output)
        Prediction = scalerY.inverse_transform(Prediction)
    
    Output = np.round(Output, 2)
    Prediction = np.round(Prediction, 2)
    print(Prediction[0,:])
    Err = np.zeros((3, Prediction.shape[0]))
    if n_Output== 1 and y_variable==False:
        for i in range(Output.shape[0]):
            Err[0,i] = Prediction[i, :]-Output[i, :]
            print('####################################################################')
            print(f'Real Output: X: {Output[i,0]}; Y: {Y_Backup[i,1]}; Z: {Y_Backup[i,2]}')
            print(f'Prediction: X: {Prediction[i,0]}; Y: {Y_Backup[i,1]}; Z: {Y_Backup[i,2]}')
            print(f'Abs. Error {i+1}. Output:  X: {Err[0,i]}; Y: {Err[1, i]}; Z: {Err[2, i]}')
            print(f'Rel. Error {i+1}. Output:  X: {round(abs((Prediction[i, 0]-Output[i, 0])/Output[i, 0])*100)}%; Y: {round(abs((Y_Backup[i, 1]-Y_Backup[i, 1])/Y_Backup[i,1])*100)}%; Z: {round(abs((Y_Backup[i, 2]-Y_Backup[i, 2])/Y_Backup[i,2])*100)}%')
    
    elif n_Output==1 and y_variable==True:
        for i in range(Output.shape[0]):
            Err[1,i] = Prediction[i, :]-Output[i, :]
            print('####################################################################')
            print(f'Real Output: X: {Y_Backup[i,0]}; Y: {Output[i,0]}; Z: {Y_Backup[i,2]}')
            print(f'Prediction: X: {Y_Backup[i,0]}; Y: {Prediction[i,0]}; Z: {Y_Backup[i,2]}')
            print(f'Abs. Error {i+1}. Output:  X: {Err[0,i]}; Y: {Err[1, i]}; Z: {Err[2, i]}')
            print(f'Rel. Error {i+1}. Output:  X: {round(abs((Prediction[i, 0]-Output[i, 0])/Output[i, 0])*100)}%; Y: {round(abs((Y_Backup[i, 1]-Y_Backup[i, 1])/Y_Backup[i,1])*100)}%; Z: {round(abs((Y_Backup[i, 2]-Y_Backup[i, 2])/Y_Backup[i,2])*100)}%')
    
    elif n_Output== 2:
        for i in range(Output.shape[0]):
            Err[0:2,i] = Prediction[i, :]-Output[i, :]
            print('####################################################################')
            print(f'Real Output: X: {Output[i,0]}; Y: {Output[i,1]}; Z: {Y_Backup[i,2]}')
            print(f'Prediction: X: {Prediction[i,0]}; Y: {Prediction[i,1]}; Z: {Y_Backup[i,2]}')
            print(f'Abs. Error {i+1}. Output:  X: {Err[0,i]}; Y: {Err[1, i]}; Z: {Err[2, i]}')
            print(f'Rel. Error {i+1}. Output:  X: {round(abs((Prediction[i, 0]-Output[i, 0])/Output[i, 0])*100)}%; Y: {round(abs((Prediction[i, 1]-Output[i, 1])/Output[i,1])*100)}%; Z: {round(abs((Y_Backup[i, 2]-Y_Backup[i, 2])/Y_Backup[i,2])*100)}%')
    
    elif n_Output == 3:
        for i in range(Output.shape[0]):
            Err[:,i] = Prediction[i, :]-Output[i, :]
            print('####################################################################')
            print(f'Real Output: X: {Output[i,0]}; Y: {Output[i,1]}; Z: {Output[i,2]}')
            print(f'Prediction: X: {Prediction[i,0]}; Y: {Prediction[i,1]}; Z: {Prediction[i,2]}')
            print(f'Abs. Error {i+1}. Output:  X: {Err[0,i]}; Y: {Err[1, i]}; Z: {Err[2, i]}')
            print(f'Rel. Error {i+1}. Output:  X: {round(abs((Prediction[i, 0]-Output[i, 0])/Output[i, 0])*100)}%; Y: {round(abs((Prediction[i, 1]-Output[i, 1])/Output[i,1])*100)}%; Z: {round(abs((Prediction[i, 2]-Output[i, 2])/Output[i,2])*100)}%')

    Data = ImportCSV(DIRPATH+'/NeuralNetworkComparison/', 'Measurements.csv', ';')
    if Data.size == 0:
        ExportCSV(Err, DIRPATH+'/NeuralNetworkComparison/', 'Measurements.csv', ';')
    else:
        temp = np.zeros((Data.shape[0]+3, Data.shape[1]))
        temp[:Data.shape[0],:Data.shape[1]] = Data
        temp[-3:,:] = Err
        ExportCSV(temp, DIRPATH+'/NeuralNetworkComparison/', 'Measurements.csv', ';')

    Names = ImportCSV(DIRPATH+'/NeuralNetworkComparison/', 'Names.csv', ';', data_type=np.string_)
    if Names.size == 0:
        ExportCSV(np.array([NAME]), DIRPATH+'/NeuralNetworkComparison/', 'Names.csv', ';', format='%s')
    else:
        with open(DIRPATH+'/NeuralNetworkComparison/Names.csv', 'a') as file:
            file.write(NAME+'\n')

if __name__=="__main__":
    train()