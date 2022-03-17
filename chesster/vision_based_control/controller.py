
from pathlib import Path
import os
from typing import Union

from chesster.master.action import Action
from chesster.master.module import Module
from chesster.Robot.UR10 import UR10Robot
from chesster.camera.realsense import RealSenseCamera
import keras
import logging
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from chesster.moduls.GenericSysFunctions import ImportCSV, ExportCSV
from chesster.moduls.ImageProcessing import ExtractImageCoordinates
import cv2 as cv
import time
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.callbacks import Callback
from sklearn.preprocessing import MinMaxScaler

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
logger = logging.getLogger(__name__)

class VisualBasedController(Module):
    def __init__(self, robot: UR10Robot, model_path: Union[str, os.PathLike], scaler_path: str):
        logger.info('Constructing VB-Controller...')
        self.__model_path = model_path
        logger.info(f'Reading Neural Network from path: {self.__model_path}')
        self.__model_name = "NeuralNetwork"
        logger.info(f'Using Neural Network Model: {self.__model_name}')
        self.__scaler_path = scaler_path
        logger.info(f'Reading scaler from path: {self.__scaler_path}')
        self.__robot = robot
        logger.info('Setting Class intern variables...')
        self.__ORIENTATION = np.array([0,-3.143, 0])
        self.__graspArray = np.zeros(3)
        self.__placeArray = np.zeros(3)
        self.__graspAction = np.zeros(0)
        self.__placeAction = np.zeros(3)
        self.__heights = np.zeros(2)
        self.__flag = "None"
        self.__scalerY = None
        self.__scalerX = None
        self.__currentMove = "None"
        self.__conversionQueenPosition = [np.array([-258.60, -640.7]), np.array([-260.6, -587.6]), np.array([-263.88, -537.11])]
        self.__conversionKnightPosition = []
        self.__wasteBinPosition = np.array([-195.15, -333.82])
        self.__currentAvailableQueens = 3 #Number of Queens placed on a fixed position for conversion
        self.__currentAvailableKnights = 0 #Number of Knights placed on a fixed position for conversion
        self.__intermediateOrientation = np.array([0, 0, -1.742])
        logger.info(f'Number of Queens for promotion available: {self.__currentAvailableQueens}')
        logger.info(f'Number of Knights for promotion available: {self.__currentAvailableKnights}')

    def start(self):
        cwd = os.getcwd()
        path = cwd+'\\'+self.__model_path+self.__model_name
        try:
            logger.info('Trying to read in Neural Network...')
            self.__neural_network = keras.models.load_model(path)
        except Exception:
            logger.info('Reading failed. No matching Directory/Model found.')
            raise Exception
        else:
            logger.info('Reading Neural Network successful.')
        try:
            logger.info('Trying to read in Neural Network...')    
            self.getScaler("ScalerDataX.csv","ScalerDataY.csv")
        except Exception:
            logger.info('Reading Scaler Data failed. No matching Directory or Files found')
            raise Exception
        else:
            logger.info('Reading Scaler Data successful.')

    def stop(self):
        pass

    def getScaler(self, xName: str, yName: str):
        """
        imports scalers for the normalized data. Is based on the Trainingdata on which the neural network is trained.
        """
        cwd = os.getcwd()
        path = cwd+'\\'+self.__scaler_path
        X = ImportCSV(path, xName, ";")
        X = np.round(X, 3)
        Y = ImportCSV(path, yName, ";")
        Y = np.round(Y, 3)
        X = np.transpose(X)
        Y = np.transpose(Y)
        self.__scalerX = MinMaxScaler(feature_range=(-1,1))
        self.__scalerX.fit(X[:, :])
        self.__scalerY = MinMaxScaler(feature_range=(-1,1))
        self.__scalerY.fit(Y[:, 0:2])

    def processMove(self, ChessPiece, d_img, ScalingFactors):
        """
        Method used for processing the Move Command. Based on a prefix (xx, PQ, no prefix) a specified action is performed:
        x: capture move -> xxe3
        PQ/PN: Promotion to Queen or Knight
        None: Regular Move from field x to field y
        """
        if 'x' in self.__currentMove: #Capture move
            logger.info('Processing Capture Move...')
            self.__graspArray = np.array([ChessPiece[0].y_cimg, ChessPiece[0].x_cimg, ChessPiece[0].zenith])
            self.__placeArray = self.__wasteBinPosition
            logger.info(f'Grasp Array (px coords): {self.__graspArray}')
            logger.info(f'Place Array (world coords): {self.__placeArray}')
            self.__heights[0] = 69
            self.__heights[1] = 130
            logger.info(f'setting heights for future z-coords to: {self.__heights}')
            self.__flag = 'capture'
        elif 'P' in self.__currentMove:
            logger.info('Processing Promotion Move...')
            if ('PQ' in self.__currentMove) or ('Pq' in self.__currentMove):                   #Case: Conversion to Queen
                self.__graspArray = self.__conversionQueenPosition.pop(-1)
                logger.info(f'Grasp Array for queen promotion move: {self.__graspArray}')
            else:                                           #Case: Conversion to Knight
                self.__graspArray = self.__conversionKnightPosition.pop(-1)
                logger.info(f'Grasp Array for knight promotion move: {self.__placeArray}')
            x = int(np.round(ChessPiece[1].roi[0]*ScalingFactors[0], 0))
            y = int(np.round(ChessPiece[1].roi[1]*ScalingFactors[1], 0))
            logger.info(f'Scaling ROI of target chess field from x: {ChessPiece[1].roi[0]}, y: {ChessPiece[1].roi[1]} to x_scaled: {x}, y_scaled: {y}')
            self.__placeArray = np.array([x, y, d_img[y,x]])
            logger.info(f'Place Array: {self.__placeArray}')
            self.__flag = 'promotion'
            self.__heights[0] = 50 #tbd aber tiefer als regular, weil neben dem Feld
            self.__heights[1] = 68
            logger.info(f'Setting heights for future z-coords to: {self.__heights}')
        else:
            logger.info('Processing Regular Move...')
            x = int(np.round(ChessPiece[1].roi[0]*ScalingFactors[0], 0))
            y = int(np.round(ChessPiece[1].roi[1]*ScalingFactors[1], 0))
            logger.info(f'Scaling ROI of target chess field from x: {ChessPiece[1].roi[0]}, y: {ChessPiece[1].roi[1]} to x_scaled: {x}, y_scaled: {y}')
            self.__graspArray = np.array([ChessPiece[0].y_cimg, ChessPiece[0].x_cimg, ChessPiece[0].zenith])
            logger.info(f'Grasp Array: {self.__graspArray}')
            self.__placeArray = np.array([x, y, d_img[y,x]]) #TBD!
            logger.info(f'Place Array: {self.__placeArray}')
            self.__heights[0] = 69 #height for grasping piece
            self.__heights[1] = 69 #height for placing piece
            logger.info(f'Setting heights for future z-coords to: {self.__heights}')
            self.__flag = 'normal'

    def processActions(self, chesspieces):
        """
        Method used for defining the pose arrays which are send to the robot. Arrays are based on the flag (move categorie x / QQ / None).
        - for capture (x) only the grasp pose is predicted by the neural network
        - for promotion (QQ/QK) only the place pose is predicted by the neural network
        - for a regular move (None) grasp as well as place poses are predicted by the neural network 
        """
        graspInput = self.__graspArray
        graspInput = graspInput[np.newaxis, :]
        placeInput = self.__placeArray
        placeInput = placeInput[np.newaxis, : ]
        if self.__flag == 'capture':                                    #case: capture
            logger.info('Processing Arrays for capture move...')
            graspInput = self.__scalerX.transform(graspInput)
            logger.info('normalizing Grasp Array to [-1, 1]')
            #Add empty axis. Necessary for Keras Prediction of shape (1,3)
            logger.info('predicting Output for Grasp Array with NN...')
            graspOutput = self.__neural_network.predict(graspInput)
            logger.info('Retransform Output...')
            self.__graspAction = self.__scalerY.inverse_transform(graspOutput)
            self.__placeAction = self.__placeArray #just copy Pose from processMove
        elif self.__flag == 'promotion':                                #case: Promotion
            logger.info('Processing Arrays for promotion move...')
            logger.info('normalizing Place Array to [-1, 1]')
            placeInput = self.__scalerX.transform(placeInput)
            #Add empty axis. Necessary for Keras Prediction of shape (1,3)
            logger.info('predicting Output for Place Array with NN...')
            placeOutput = self.__neural_network.predict(placeInput)
            logger.info('Retransform Output...')
            self.__placeAction = self.__scalerY.inverse_transform(placeOutput)
            self.__graspAction = self.__graspArray #just copy Pose from processMove
        else:                                                           #case: normal move
            logger.info('Processing Arrays for regular move...')
            logger.info('normalizing Grasp Array to [-1, 1]')
            graspInput = self.__scalerX.transform(graspInput) #normalize raw data according to training data of NN
            logger.info('normalizing Place Array to [-1, 1]')
            placeInput = self.__scalerX.transform(placeInput)
            logger.info('predicting Output for Grasp Array with NN...')
            graspOutput = self.__neural_network.predict(graspInput) #predict TCP-Coordinates in normalized format
            logger.info('predicting Output for Place Array with NN...')
            placeOutput = self.__neural_network.predict(placeInput)
            logger.info('Retransform Outputs...')
            self.__graspAction = self.__scalerY.inverse_transform(graspOutput) #convert normalized data to mm 
            self.__placeAction = self.__scalerY.inverse_transform(placeOutput)
        logger.info(f'Grasp Array in world coords for robot: {self.__graspAction}')
        logger.info(f'Place Array in world coords for robot: {self.__placeAction}')

    def makeMove(self):
        """
        Processes the obtained action arrays for grasp and place. Fixed orientations and heights are assigned and then send to the
        Robot Class method MoveChesspiece.
        """
        logger.info(f'preparing trajectory for robot')
        graspPose = np.zeros(6)
        graspPose[0:2] = self.__graspAction
        graspPose[0] = graspPose[0]
        graspPose[1] = graspPose[1]
        graspPose[2] = self.__heights[0]
        graspPose[3:] = self.__ORIENTATION
        
        placePose = np.zeros(6)
        placePose[0:2] = self.__placeAction
        placePose[0] = placePose[0]#+5 #x Kamera "+" in Richtung Kamera -> Static offsets due to misalinement at detector-level
        placePose[1] = placePose[1]+3-7 #y Spieler "+" in Richtung Roboterarm -> Static offsets due to misalinement at detector-level
        placePose[2] = self.__heights[1]
        placePose[3:] = self.__ORIENTATION

        logger.info(f'Final grasp pose: {graspPose}')
        logger.info(f'Final place pose: {placePose}')

        logger.info('Moving Chesspiece.')
        self.__robot.MoveChesspiece(graspPose, placePose, self.__intermediateOrientation, 100)

    def useVBC(self, Move: str, Pieces: list, d_img: np.ndarray, ScalingFactors: list, lastMove: bool):
        """
        Main method of the Vision Based Controller. This method is the only one that should be called by the user. 
        Executes all neccessary methods for a movement of a piece.
        """
        self.__currentMove = Move
        logger.info(f'VBC processing move: {self.__currentMove}')
        self.processMove(Pieces, d_img, ScalingFactors)
        self.processActions(Pieces)
        self.makeMove()
        if lastMove == True:
            logger.info('Last move of moveset. Proceeding to drive home... ')
            self.__robot.Home()

class VBC_Calibration(Module):
    def __init__(self):
        self.__TRAINING_ORIENTATION = np.array([0.023, 2.387, -1.996])
        #self.__TRAINING_WORKSPACE = np.array([[-236.1, 267], [-1100, -520.5], [30, 162.5]]) #X; Y; Z
        self.__TRAINING_WORKSPACE = np.array([[-236.1, 267], [-1100, -520.5], [80, 162.5]]) #X; Y; Z
        self.__TRAINING_HOME = np.array([60, -120, 120, 0, 90, 180])
        self.color = np.array([350.1/2, 64, 71]) #currently hardcoded as bright neon pink
        #self.color_upper_limit = np.array([179, 255, 255]) #Check https://stackoverflow.com/questions/10948589/choosing-the-correct-upper-and-lower-hsv-boundaries-for-color-detection-withcv for reference
        #self.color_lower_limit = np.array([167, 64, 111])
        self.color_upper_limit = np.array([167, 64, 255]) #Check https://stackoverflow.com/questions/10948589/choosing-the-correct-upper-and-lower-hsv-boundaries-for-color-detection-withcv for reference
        self.color_lower_limit = np.array([124, 47, 111])
        timestamp = time.time()
        self.__TRAINING_DATA_PATH = os.environ['TRAINING_DATA_PATH']+f'data_{timestamp}'
        self.__robot = UR10Robot(os.environ['ROBOT_ADDRESS'])
        self.__camera = RealSenseCamera()

    def start(self):
        #self.__robot.start()
        #self.__GraspCali()
        #self.__robot.MoveJ(self.__TRAINING_HOME)
        pass
    def stop(self):
        pass

    def GenerateTrainingdata(self, random_sample, update_func, n_data: int, gui_elements: list, save_pictures: bool =False):
        self.__robot.MoveJ(self.__TRAINING_HOME)
        os.mkdir(Path(self.__TRAINING_DATA_PATH), 0o666)
        self.__TRAINING_DATA_PATH = self.__TRAINING_DATA_PATH+'/'
        pose = np.zeros((6))
        output = np.zeros((3, n_data)) #Shape: X
                                  #       Y
                                  #       Z
        input = np.zeros((3, n_data))  #Shape: Img_X
                                  #       Img_Y
                                  #       Depth@XY
        start_total = time.time()
        gui_elements[2].setHidden(False)
        for i in range(n_data):
            start = time.time()
            pose[0:3] = random_sample[0:3, i]
            pose[3:6] = self.__TRAINING_ORIENTATION
            self.__robot.MoveC(pose)
            c_img = self.__camera.capture_color()
            d_img, _ = self.__camera.capture_depth(apply_filter=True)
            input[0:3, i], c_img_processed = self.__ProcessInput(d_img, c_img.copy(), self.color_upper_limit, self.color_lower_limit)
            output[0:3, i] = self.__ProcessOutput()
            update_func(c_img_processed, gui_elements[4])

            if save_pictures:
                cv.imwrite(self.__TRAINING_DATA_PATH+f'c_img_{i}.bmp', c_img_processed)
                cv.imwrite(self.__TRAINING_DATA_PATH+f'd_img_{i}.bmp', d_img)

            ExportCSV(input, Path(self.__TRAINING_DATA_PATH), f"input_data.csv", ";")
            ExportCSV(output, Path(self.__TRAINING_DATA_PATH), f"output_data.csv", ";")
            end = time.time()
            gui_elements[1].setText(f'data set {i+1} of {n_data} created. ({np.round(end-start,1)}s)')
            gui_elements[3].setText(str(int((i+1)*100/n_data)))
              
        end_total = time.time()
        gui_elements[0].setText(f'Generation done. total time elapsed: {np.round((end_total-start_total)/60, 1)} minutes')
        gui_elements[1].setText(f'Post processing data...')
        input_filtered, output_filtered = self.__PostProcessData(input, output)

        ExportCSV(input_filtered, Path(os.environ['SCALER_PATH']), 'ScalerDataX.csv', ';')
        ExportCSV(output_filtered, Path(os.environ['SCALER_PATH']), 'ScalerDataY.csv', ';')
        ExportCSV(input_filtered, Path(os.environ['NEURAL_NETWORK_DATA_PATH']), 'training_data_Input.csv', ';')
        ExportCSV(output_filtered, Path(os.environ['NEURAL_NETWORK_DATA_PATH']), 'training_data_Output.csv', ';')
        #input_filtered = ImportCSV(Path(os.environ['SCALER_PATH']), 'ScalerDataX.csv', ';')
        #output_filtered = ImportCSV(Path(os.environ['SCALER_PATH']), 'ScalerDataY.csv', ';')
        self.__robot.MoveJ(self.__TRAINING_HOME)
        self.__robot.Home()
        self.__RemoveCali()
        self.__robot.Home()
        return input, output, input_filtered, output_filtered
            
    def TCPDetectionCheck(self, random_sample):
        logger.info("Initializing TCP Detection Checkup...")
        logger.info("current Color settings are:")
        logger.info("------------------------------------------")
        logger.info(f"Color HSV Values: {self.color}")
        logger.info(f"Upper Limit HSV Values: {self.color_upper_limit}")
        logger.info(f"Lower Limit HSV Values: {self.color_lower_limit}")
        print("------------------------------------------")
        logger.info("taking Pictures..")
        Pose = np.zeros((6))
        Imgs = []
        Imgs_Old = []
        for i in range(3):
            Pose[0:3] = random_sample[0:3, i]
            Pose[3:6] = self.__TRAINING_ORIENTATION 
            self.__robot.MoveC(Pose)
            d_img, _ = self.__camera.capture_depth(apply_filter=True)
            c_img = self.__camera.capture_color()
            c_img_old = c_img.copy()
            _, c_img, _ = ExtractImageCoordinates(c_img, d_img, self.color_upper_limit, self.color_lower_limit)
            c_img = cv.resize(c_img, (int(c_img.shape[0]*0.66), int(c_img.shape[1]*0.66)))
            Imgs.append(c_img)
            Imgs_Old.append(c_img_old)
        Imgs_stack = np.hstack((Imgs[0], Imgs[1], Imgs[2]))
        return Imgs_Old, Imgs_stack

    def __GraspCali(self):
        self.__robot.ActuateGripper(30)
        self.__robot.MoveC(np.array([383.52, -481.60, 900, 0, 3.140, 0])) #WICHTIG: BASIS KOORDINATENSYSTEM!!
        self.__robot.MoveC(np.array([383.52, -481.60, 828.18, 0, 3.140, 0]))
        self.__robot.CloseGripper()
        self.__robot.MoveC(np.array([383.52, -481.60, 900, 0, 3.140, 0]))
        self.__robot.Home()   

    def __RemoveCali(self):
        self.__robot.MoveC(np.array([383.52, -481.60, 900, 0, 3.140, 0])) #WICHTIG: BASIS KOORDINATENSYSTEM!!
        self.__robot.MoveC(np.array([383.52, -481.60, 828.18, 0, 3.140, 0]))
        self.__robot.ActuateGripper(30)
        self.__robot.MoveC(np.array([383.52, -481.60, 900, 0, 3.140, 0]))
        self.__robot.Home()

    def __ProcessInput(self, depth_image, color_image, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT): #Bright - Neon- Green is probably the best choice for Contour extraction of the TCP
        Img_Coords, img_proc, _ = ExtractImageCoordinates(color_image, depth_image, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT, ImageTxt="TCP")
        input = np.array([Img_Coords[0], Img_Coords[1], depth_image[Img_Coords[1]-1, Img_Coords[0]-1]]) #Flipped!
        return input, img_proc

    def __ProcessOutput(self):
        pose = self.__robot.WhereC()
        output = pose[0:3]
        return output

    def PointGeneration(self, n):
        xmin = self.__TRAINING_WORKSPACE[0,0]
        xmax = self.__TRAINING_WORKSPACE[0,1]
        ymin = self.__TRAINING_WORKSPACE[1,0]
        ymax = self.__TRAINING_WORKSPACE[1,1]
        zmin = self.__TRAINING_WORKSPACE[2,0]
        zmax = self.__TRAINING_WORKSPACE[2,1]

        RandomSample = np.zeros((3,n))
        x_rand = []
        y_rand = []
        z_rand = []
        TRESHOLD_X = -225
        TRESHOLD_Y = -773
        TRESHOLD_Z = 73
        while len(x_rand)<n:
            x = np.random.randint(xmin, xmax+1, 1)[0]
            y = np.random.randint(ymin, ymax+1, 1)[0]
            z = np.random.randint(zmin, zmax+1, 1)[0]
            if (x<TRESHOLD_X) and (y>TRESHOLD_Y) and (z<TRESHOLD_Z): #Cut out the space for the E-STOP
                pass
            else:
                x_rand.append(x)
                y_rand.append(y)
                z_rand.append(z)
        
        RandomSample[0, :] = np.array(x_rand)
        RandomSample[1, :] = np.array(y_rand)
        RandomSample[2, :] = np.array(z_rand)
        return RandomSample

    def TrainNeuralNetwork(self, input, output, LogCallback):
        __epochs = 150
        __batch = 50
        __optimizer = 'adam'
        __loss_fct = 'mae'
        __layer_neurons = [64, 128, 64]
        __nInput = 3
        __nOutput = 2
        NAME = 'NeuralNetwork'
        NAME_DOCS = f'{__nInput}x'
        for Neurons in __layer_neurons:
            NAME_DOCS+=f'{Neurons}x'
        input = input[:, :]
        output = output[:, :]
        logger.info(input.shape)
        logger.info(output.shape)
        NAME_DOCS+=f'{__nOutput}_EPOCHS{__epochs}_NDATA{input.shape[1]}'
        logger.info(NAME_DOCS)
        model = self.__get_MLP_model(__nInput, __nOutput, __layer_neurons, 'relu')
        input_norm, output_norm, scalerY, scalerX = self.__scale_data(input, output, 3, 2)
        model.compile(loss=__loss_fct, optimizer=__optimizer, metrics=['accuracy'])
        model.fit(input_norm[:, :], output_norm[:, :], epochs=__epochs, batch_size=__batch, validation_split=0.2, verbose=1, callbacks=[LogCallback])
        model.save(os.environ['NEURAL_NETWORK_PATH']+NAME, save_format='tf')
        Err_data, Err, Err_abs = self.__evaluate(scalerY, scalerX, model, NAME_DOCS)
        return Err_data, Err, Err_abs

    def __scale_data(self, input, output, n_input, n_output):
        input = np.transpose(input)
        output = np.transpose(output)

        scalerX = MinMaxScaler(feature_range=(-1,1))
        scalerX.fit(input[:, 0:n_input])
        X_Norm = scalerX.transform(input[:, 0:n_input])
        scalerY = MinMaxScaler(feature_range=(-1,1))
        scalerY.fit(output[:, 0:n_output])
        Y_Norm = scalerY.transform(output[:, 0:n_output])

        return X_Norm, Y_Norm, scalerY, scalerX

    def __get_MLP_model(self, n_input: int, n_output: int, n_layer: list, activation: str):
        model = Sequential()
        for i, n in enumerate(n_layer):
            if i==0:
                model.add(Dense(n, input_dim = n_input, kernel_initializer='he_uniform', activation=activation))
            else:
                model.add(Dense(n, activation=activation, kernel_initializer='he_uniform'))
        model.add(Dense(n_output))
        return model

    def __evaluate(self, scalerY, scalerX, model, name):
        benchmark_input = ImportCSV(Path(os.environ['BENCHMARK_DATA_PATH']), 'benchmark_data_input.csv', ';')
        benchmark_output = ImportCSV(Path(os.environ['BENCHMARK_DATA_PATH']), 'benchmark_data_output.csv', ';')
        benchmark_input_rescaled = scalerX.transform(benchmark_input)
        prediction = model.predict(benchmark_input_rescaled)
        prediction_rescaled = scalerY.inverse_transform(prediction)
        Err = (prediction_rescaled-benchmark_output[:, 0:2]).T

        Data = ImportCSV(Path(os.environ['BENCHMARK_DATA_PATH']), 'benchmark_results_data.csv', ';')
        Names = ImportCSV(Path(os.environ['BENCHMARK_DATA_PATH']), 'benchmark_results_names.csv', ';', data_type=np.string_)
        if Data.size == 0:
            ExportCSV(Err, Path(os.environ['BENCHMARK_DATA_PATH']), 'benchmark_results_data.csv', ';')
            ExportCSV(np.array([name]), Path(os.environ['BENCHMARK_DATA_PATH']), 'benchmark_results_names.csv', ';', format='%s')
        else:
            temp = np.zeros((Data.shape[0]+2, Data.shape[1]))
            temp[:Data.shape[0],:Data.shape[1]] = Data
            temp[-2:,:] = Err
            ExportCSV(temp, Path(os.environ['BENCHMARK_DATA_PATH']), 'benchmark_results_data.csv', ';')
            with open(Path(os.environ['BENCHMARK_DATA_PATH']+'benchmark_results_names.csv'), 'a') as file:
                file.write(name+'\n')
        Err = Err.T
        Err_abs = np.abs(Err)

        n_x_lowerThree = (Err_abs[:, 0]<=3).sum()
        n_x_lowerFive = (Err_abs[:, 0]<=5).sum()
        n_y_lowerThree = (Err_abs[:, 1]<=3).sum()
        n_y_lowerFive = (Err_abs[:, 1]<=5).sum()
        Err_data = [n_x_lowerThree, n_x_lowerFive, n_y_lowerThree, n_y_lowerFive]
        return Err_data, Err, Err_abs

    def __PostProcessData(self, X, Y):
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
        return X, Y

class LogCallback(Callback):
    def __init__(self, fig, axis1, axis2, label):
        self.train_accuracy = []
        self.val_accuracy = []
        self.train_loss = []
        self.val_loss = []
        self.epoch = []
        self.data = [self.train_accuracy, self.val_accuracy, self.train_loss, self.val_loss]
        self.fig = fig
        self.axis1 = axis1
        self.axis2 = axis2
        self.axes = [self.axis1, self.axis2]
        self.line1, = self.axis1.plot(0,0, color='#151D3B', label='Train accuracy')
        self.line2, = self.axis1.plot(0,0, color='#D82148', label='Val accuracy')
        self.line3, = self.axis2.plot(0,0, color='#151D3B', label='Train loss')
        self.line4, = self.axis2.plot(0,0, color='#D82148', label='Val loss')
        self.axis1.legend(loc="upper right")
        self.axis2.legend(loc="upper right")
        self.lines = [self.line1, self.line2, self.line3, self.line4]
        self.label = label

    def on_epoch_end(self, epoch, logs=None):
        self.label.setText(f'Training neural network on epoch {epoch+1}...')
        self.train_accuracy.append(logs["accuracy"])
        self.val_accuracy.append(logs["val_accuracy"])
        self.train_loss.append(logs["loss"])
        self.val_loss.append(logs["val_loss"])
        self.epoch.append(epoch)

        for d, l in zip(self.data, self.lines):
            l.set_xdata(self.epoch)
            l.set_ydata(d)

        max_y_loss = max(self.train_loss + self.val_loss)
        max_y_acc = max(self.train_accuracy + self.val_accuracy)

        min_y_loss = min(self.train_loss + self.val_loss)
        min_y_acc = min(self.train_accuracy + self.val_accuracy)

        self.axis1.set_xlim(0, epoch)
        self.axis2.set_xlim(0, epoch)
        self.axis1.set_ylim(min_y_acc*0.8, max_y_acc*1.1)
        self.axis2.set_ylim(min_y_loss*0.8, max_y_loss*1.2)
        self.fig.canvas.draw()

        

