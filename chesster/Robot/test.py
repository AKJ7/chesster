import numpy as np
def MoveChesspiece(graspPose, placePose, intermediateOrientation, Offset: int = 100):
        graspPoseOffset = graspPose.copy()
        placePoseOffset = placePose.copy()
        graspPoseOffset[2] = graspPoseOffset[2]+Offset
        placePoseOffset[2] = placePoseOffset[2]+Offset

        intermediatePose = graspPoseOffset.copy()
        intermediatePose[2] = intermediatePose[2]+int(Offset*1.5)
        intermediatePose[3:] = intermediateOrientation

        movesGrasp = [graspPoseOffset, 
                      graspPose,
                    ]

        movesPlace = [graspPoseOffset, 
                      intermediatePose,
                      placePoseOffset,
                      placePose,
                    ]
        
        for move in movesPlace:
            move[0:3] = move[0:3]/1000
        for move in movesGrasp:
            move[0:3] = move[0:3]/1000
        print('')

MoveChesspiece(np.array([0,0,58, 0,-3.143, 0]), np.array([100,100,58, 0,-3.143, 0]), np.array([0, 0, -1.742]))