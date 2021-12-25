#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Thorben Pultke
Contact: thorben.pultke@gmx.de
Project: CHESSter
Summary: Script to define the currently interesting workspace of the used robotic arm for training data generation. 
Take care when running this script as every point in the defined 3D-Cubus can be accessed by randomized movements.
"""

from logging import exception
import tkinter as tk
import numpy as np
import urx as urx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #Lib für die Einbindung von Matplotlib Diagrammen in Tkinter
from mpl_toolkits.mplot3d import Axes3D #Import von 3D-Diagrammen
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection #3D Objekte für die Darstellung von Polygonen
from matplotlib.figure import Figure #Generelle Lib für Matplotlib Diagrammen
import threading as th 
import os as os
import time as time

i=0

class GUI:
    def __init__(self,tk_object):  
        self.gui = tk_object 
        self.gui.title("Arbeitsraum Definition")
        self.Coords = []
        self.Points = [[6, 0, 2], [6, 8, 2], [0, 0, 2], [0, 8, 2], [6, 0, 6], [6, 8, 6], [0, 0, 6], [0, 8, 6]]
        self.RPoints = [[9, 4, 0],[9, 4, 4],[7, 4, 6.5],[5, 4, 6],[3, 4, 4]]
        container1 = tk.Frame(self.gui, relief=tk.RAISED, width=500, height=500) #Container 1 enthält alle in der GUI links angelegte Elemente (Einstellungen, etc.)
        container2 = tk.Frame(self.gui, relief=tk.RIDGE) #Container 2 enthält alle Diagramme
        container1.pack_propagate(False)
        container1.pack(side=tk.LEFT)
        container2.pack(side=tk.LEFT)
        self.L1 = tk.Label(container1, text="ACHTUNG")
        self.L2 = tk.Label(container1, text="""Dieses Skript wird dich durch die Arbeitsraumdefinition führen. 
Bitte folge den Schritten und Abbildungen auf dem Diagramm, 
damit alles reibungslos läuft.

Drücke Start zum Beginnen""")
        self.L1.pack(pady=5)
        self.L2.pack()
        self.L3 = tk.Label(container1, text="Nicht verbunden...", bg='#ba3c3c', fg='white')
        self.L3.pack(side=tk.RIGHT)
        self.Ctrl = tk.Button(container1, text="Start", command=self.ProceedStep)
        self.Ctrl.pack(pady=5)

        self.fig = Figure(figsize=(9, 9))
        self.ax = self.fig.add_subplot(1, 1, 1, projection='3d')
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')
        self.ax.set_zlabel('z')
        self.ax.set_xlim3d([-2, 10])
        self.ax.set_ylim3d([-2, 10])
        self.ax.set_zlim3d([0, 12])
        self.tk_plot = FigureCanvasTkAgg(self.fig, container2)
        self.tk_plot.get_tk_widget().pack()
    
    def ProceedStep(self):
        global i

        if (i==0):
            try:
                self.Rob = urx.Robot("169.254.34.80")
                #print('Test')
            except Exception:
                self.L1.config(text="FEHLER")
                self.L2.config(text="Roboter konnte nicht verbunden werden. Überprüfen und neustarten...", fg='red')

            else:
                if(self.Rob.is_running()):
                #if(True):
                    TRAINING_HOME_Init = np.array([0, -120, 120, 0, -90, -180]) #has to be called because the robot will otherwise crash into the camera
                    TRAINING_HOME = np.array([60, -120, 120, 0, 90, 180])
                    self.Rob.movej(np.deg2rad(TRAINING_HOME_Init), wait=True, relative=False, vel=0.6)
                    self.Rob.movej(np.deg2rad(TRAINING_HOME), wait=True, relative=False, vel=0.6)
                    self.L3.config(text="Verbunden.", bg='#3da872', fg='white')
                    self.L1.config(text="Kalibrierung...")
                    self.Ctrl.config(text="Weiter")
                    self.L2.config(text="""Bewege den Roboterarm zum ersten Eckpunkt (siehe Diagramm)
und drücke Weiter.""")
                    i=i+1
                    self.DrawPoints(0, 1)

                    for j in range(5):
                        color='green'
                        self.ax.scatter3D(self.RPoints[j][0],self.RPoints[j][1],self.RPoints[j][2], c=color)
                    for j in range(4):
                        color='black'
                        self.ax.plot3D((self.RPoints[j][0], self.RPoints[j+1][0]),(self.RPoints[j][1], self.RPoints[j+1][1]),(self.RPoints[j][2], self.RPoints[j+1][2]), c=color)
                    self.ax.plot3D((self.RPoints[0][0], self.RPoints[0][0]-1),(self.RPoints[0][1], self.RPoints[0][1]),(self.RPoints[0][2], self.RPoints[0][2]), c='yellow')
                    self.ax.plot3D((self.RPoints[0][0], self.RPoints[0][0]),(self.RPoints[0][1], self.RPoints[0][1]+1),(self.RPoints[0][2], self.RPoints[0][2]), c='green')
                    self.ax.plot3D((self.RPoints[0][0], self.RPoints[0][0]),(self.RPoints[0][1], self.RPoints[0][1]),(self.RPoints[0][2], self.RPoints[0][2]+1), c='red')
                    self.tk_plot.draw()
                    self.Rob.set_freedrive(True, timeout=300)

                else:
                    self.L1.config(text="FEHLER")
                    self.L2.config(text="Roboter konnte nicht verbunden werden. Überprüfen und neustarten...", fg='red')
                    self.Rob.close()


        elif (i==1):
            if(self.Rob.is_running()):
            #if(True):
                self.Rob.set_freedrive(False, timeout=1300)
                pose = self.Rob.getl()
                #pose = [1,1,1,90,90,90]
                print(pose)
                self.Coords.append([pose[0], pose[1], pose[2]])
                self.L2.config(text="""Bewege den Roboterarm zum zweiten Eckpunkt (siehe Diagramm)
und drücke Weiter. Auf die Z-Höhe brauchst du nicht zu achten, 
diese wird der Roboterarm nach dem nächsten "Weiter" automatisch annehmen.""")
                for artist in self.fig.gca().collections:
                    if (isinstance(artist.get_gid(), int)):
                        if (artist.get_gid() >= 0) and (artist.get_gid() <=8):
                            artist.remove()
                self.DrawPoints(3,2)
                self.tk_plot.draw()
                i=i+1
                self.Rob.set_freedrive(True, timeout=1300)
            else:
                self.L1.config(text="FEHLER")
                self.L2.config(text="Roboter hat die Verbindung verloren.. bite prüfen und Neustarten!", fg='red')
                self.Rob.close()
        elif (i==2):
            if(self.Rob.is_running()):
            #if(True):
                self.Rob.set_freedrive(False, timeout=1300)
                pose = self.Rob.getl()
                #pose = [2,2,1,90,90,90]
                self.Coords.append([pose[0], pose[1], self.Coords[0][2]])
                pose[2] = self.Coords[1][2] 
                self.Rob.movel(pose, vel=0.6)
                self.L2.config(text="""Bewege den Roboterarm zum dritten Eckpunkt (siehe Diagramm)
und drücke Weiter. Hier ist nur die Z-Höhe entscheidend, auf X- und Y- brauchst du nicht zu achten. 
Nachdem du auf Fertig drückst, fährt der Roboterarm alle 8 Eckpunkte ab und der Arbeitsraum wird unter
Arbeitsraum.csv gespeichert.""")
                for artist in self.fig.gca().collections:
                    if (isinstance(artist.get_gid(), int)):
                        if (artist.get_gid() >= 0) and (artist.get_gid() <=8):
                            artist.remove()
                self.DrawPoints(7,3)
                self.tk_plot.draw()
                i=i+1
                self.Rob.set_freedrive(True, timeout=1300)
            else:
                self.L1.config(text="FEHLER")
                self.L2.config(text="Roboter hat die Verbindung verloren.. bite prüfen und Neustarten!", fg='red')
                self.Rob.close()
        elif (i==3):
            if(self.Rob.is_running()):
            #if(True):
                self.Rob.set_freedrive(False, timeout=1300)
                self.L1.config(text="Erfolgreich!")
                self.L2.config(text="""Kalibrierung erfolgreich. Alle 8 Eckpunkte werden nun abgefahren...""")
                
                pose = self.Rob.getl()
                #pose = [1,1,2,90,90,90]
                self.Coords.append([self.Coords[1][0], self.Coords[1][1], pose[2]])
                pose[0] = self.Coords[2][0]
                pose[1] = self.Coords[2][1]
                self.Rob.movel(pose, vel=0.3)

                Arbeitsraum = np.zeros((8,3)) #Shape: all eight corners of the cuboid working space
                Arbeitsraum_min_max = np.zeros((3,2)) #Shape: X  Min  Max
                                                    #       Y  Min  Max
                                                    #       Z  Min  Max

                Arbeitsraum[0, 0:3] = self.Coords[0][0:3]
                Arbeitsraum[1][0] = self.Coords[0][0]
                Arbeitsraum[1,1:3] = self.Coords[1][1:3]
                Arbeitsraum[2,0:3] = self.Coords[1][0:3]
                Arbeitsraum[3][0] = self.Coords[1][0]
                Arbeitsraum[3,1:3] = self.Coords[0][1:3]
                Arbeitsraum[4:8,0:3] = Arbeitsraum[0:4, 0:3]
                Arbeitsraum[4:8,2] = Arbeitsraum[4:8,2]+(self.Coords[2][2]-self.Coords[1][2])

                Arbeitsraum_min_max[0, 0:2] = np.array([np.min(Arbeitsraum[0:8, 0]), np.max(Arbeitsraum[0:8, 0])])
                Arbeitsraum_min_max[1, 0:2] = np.array([np.min(Arbeitsraum[0:8, 1]), np.max(Arbeitsraum[0:8, 1])])
                Arbeitsraum_min_max[2, 0:2] = np.array([np.min(Arbeitsraum[0:8, 2]), np.max(Arbeitsraum[0:8, 2])])

                Arbeitsraum = np.round(Arbeitsraum*1000,1) #Konvertierung Meter -> Millimeter
                Arbeitsraum_min_max = np.round(Arbeitsraum_min_max*1000,1) #Konvertierung Meter -> Millimeter

                for artist in self.fig.gca().collections + self.fig.gca().lines + self.fig.gca().texts:
                    if (isinstance(artist.get_gid(), int)):
                        if (artist.get_gid() >= 0) and (artist.get_gid() <=8):
                            artist.remove()

                for j in range(8):
                    self.ax.text(self.Points[j][0]+0.5,self.Points[j][1]-0.5,self.Points[j][2], f'P{j+1}:\nX: {Arbeitsraum[j, 0]}\nY: {Arbeitsraum[j, 1]}\nZ: {Arbeitsraum[j, 2]}', 'x')
                    self.ax.scatter3D(self.Points[j][0],self.Points[j][1],self.Points[j][2], c='cyan')
                DIRPATH = os.path.dirname(__file__)

                np.savetxt(DIRPATH+'/Arbeitsraum.csv', Arbeitsraum, delimiter=";")
                np.savetxt(DIRPATH+'/Arbeitsraum_min_max.csv', Arbeitsraum_min_max, delimiter=";")

                self.tk_plot.draw()
                time.sleep(1)
                homepos = np.array([0, -120, 120, 0, 90, 180])
                for j in range(8):
                    #self.Rob.movej(np.deg2rad(homepos), wait=True, relative=False, vel=0.6, acc=0.15)
                    pose[0:3] = Arbeitsraum[j, 0:3]/1000
                    pose[3:6] = [0, 2.220, -2.220]
                    self.Rob.movel(pose, vel=0.6)
                self.Rob.movej(np.deg2rad(homepos), wait=True, relative=False, vel=0.6, acc=0.15)
                self.Ctrl.config(text="Fertig")
                i=i+1
            else:
                self.L1.config(text="FEHLER")
                self.L2.config(text="Roboter hat die Verbindung verloren.. bite prüfen und Neustarten!", fg='red')
                self.Rob.close()
        elif (i==4):
            self.L2.config(text="Arbeitsraum gespeichert. Du kannst das Skript nun schließen.")
            self.L3.config(text="Verbindung getrennt", bg='#ba3c3c', fg='white')
            self.Rob.close()
            self.Ctrl.config(state="disabled")

    def DrawPoints(self,n,k):
        for j in range(8):
            if j==n:
                color='red'
                self.ax.text(self.Points[j][0]+0.5,self.Points[j][1]-0.5,self.Points[j][2], f'Punkt {k}', 'x', gid=8)
            else:
                color='gray'
            self.ax.scatter3D(self.Points[j][0],self.Points[j][1],self.Points[j][2], c=color, gid=j)

def main():
    fenster = tk.Tk() #Erzeugen eines Tkinter Objektes
    instanz = GUI(fenster) #Erzeugen der GUI-Instanz dieses Objektes durch Übergabe an Klasse
    fenster.mainloop() #Mainloop startet einen Thread mit der GUI => GUI ist somit Main-Thread
if __name__ == "__main__":
    main()
    