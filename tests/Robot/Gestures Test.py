from chesster.Robot.UR10 import UR10Robot

Robot = UR10Robot()
while True:
    print("Gestures: \n1) Start Gesture - Beginner = True\n2) Start Gesture - Beginner = False\n3) End Gesture - Victory = True\n4) End Gesture - Victory = False")
    Num = input("Please enter the Number of the gesture you would like to see: ")
    if Num == "1":
        Robot.StartGesture(Beginner=True)
    elif Num == "2":
        Robot.StartGesture(Beginner = False)
    elif Num == "3":
        Robot.EndGesture(Victory = True)
    elif Num == "4":
        Robot.EndGesture(Victory = False)
    else:
        print('No matching Number entered... ')