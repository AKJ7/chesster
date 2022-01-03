import chess
import chess.engine
import pandas as pd
from stockfish import Stockfish
def MirroredMatrix():
    Spiegelbild=pd.DataFrame(columns=['Original','Mirrored'])
    buchstaben={'Buchstabe': ['a','b','c','d','e','f','g','h']}
    BS=pd.DataFrame(data=buchstaben)
    zahlen={'Zahl': [8,7,6,5,4,3,2,1]}
    ZahlenMirr={'ZahlMirr': [1,2,3,4,5,6,7,8]}
    ZL=pd.DataFrame(data=zahlen)
    ZLM=pd.DataFrame(data=ZahlenMirr)
    for l in range(0,8):
        for i in range(0,8):
            Buch=BS['Buchstabe'][i]
            Zahl=ZL['Zahl'][l]
            StrZahl=str(Zahl)
            BZ=Buch+StrZahl

            ZahlMirr=ZLM['ZahlMirr'][l]
            StrNewZahl = str(ZahlMirr)
            BNZ=Buch+StrNewZahl
            Spiegelbild.loc[l*8+i]=[BZ,BNZ]
    return Spiegelbild

def MirrorIfPlayerIsWhite(Gegnerzug):
    MirroredPosition=[]
    for n in range(len(Gegnerzug)):
        Spiegelbild = MirroredMatrix()
        OldPosition = Gegnerzug[n][0:2]
        OldPositionMirr=""
        NewPosition = Gegnerzug[n][2:4]
        NewPositionMirr = ""
        for i in range(0,64):
            if Spiegelbild['Original'][i]==OldPosition:
                OldPositionMirr=Spiegelbild['Mirrored'][i]
            if Spiegelbild['Original'][i]==NewPosition:
                NewPositionMirr=Spiegelbild['Mirrored'][i]
        if OldPositionMirr=="":
            OldPositionMirr=OldPosition
        if NewPositionMirr=="":
            NewPositionMirr=NewPosition
        MirroredPosition.append(OldPositionMirr + NewPositionMirr)
    return MirroredPosition

Mirroredplay=MirroredMatrix()

#print(Mirroredplay)
Spielerzug=["f8c5","f2d7"]
MirroredPos=MirrorIfPlayerIsWhite(Spielerzug)
print(MirroredPos)