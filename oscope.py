#! /usr/bin/python3

# Audio oscilloscope 

################################################################################

import pyaudio
import time
import sys
#from datetime import timedelta,datetime
#from collections import OrderedDict
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

colors=['b','g','r','c','m','y','k',
        'dodgerblue','lime','orange','aqua','indigo','gold','gray',
        'navy','limegreen','tomato','cyan','purple','yellow','dimgray']

################################################################################

# User params - Keep these as is for now as they have implications later on that
# we'll address later
WIDTH = 2
CHANNELS = 1
RATE = 44100
RATE = 48000
RATE = 8000

################################################################################

# The GUI
class OSCOPE_GUI(QtGui.QMainWindow):

    def __init__(self,fs):
        super(OSCOPE_GUI, self).__init__()

        # Init
        self.fs=float(fs)
        self.chunkSize = 1024         # This is set by pyaudio and seems to always be 1024
        self.maxChunks=40             # This controls the width of the time series display
        self.curves=[]
        self.x = np.arange(self.maxChunks*self.chunkSize)/self.fs
        self.y = np.zeros(self.maxChunks*self.chunkSize)
        print('fs=',self.fs,len(self.x))
        self.data=np.zeros(self.chunkSize)

        # Start by putting up the root window
        print('Init GUI ...')
        self.win  = QtGui.QWidget()
        self.setCentralWidget(self.win)
        self.setWindowTitle('Audio oscilloscope by AA2IL')

        # We use a simple grid to layout controls
        self.grid = QtGui.QGridLayout(self.win)
        nrows=6
        ncols=5

        # Create a widget and add it to our layout
        row=0
        col=0
        btn = QtGui.QPushButton('Quit')
        btn.setToolTip('Quit Application')
        btn.clicked.connect(self.Quit)
        self.grid.addWidget(btn,row,col)

        # The Canvas is where we will put the map
        row=1
        col=0
        self.canvas = pg.GraphicsWindow()
        self.grid.addWidget(self.canvas,row,col)
        self.p1 = self.canvas.addPlot()
        self.p1.setLabel('bottom', 'Time', 's')
        self.curve = self.p1.plot(pen='r')
        #self.p1.enableAutoRange('xy', False)
        #self.p1.setXRange(0, np.max(self.x))
        
        # Allow canvas size to change when we resize the window
        # but make is always visible
        if False:
            sizePolicy = QtGui.QSizePolicy( QtGui.QSizePolicy.MinimumExpanding, 
                                            QtGui.QSizePolicy.MinimumExpanding)
            self.canvas.setSizePolicy(sizePolicy)
        
        # Let's roll!
        self.resize(200,0)
        self.show()
        #self.win.resize(self.win.minimumSizeHint())
        
    # Function to quit the app
    def Quit(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        
        self.win.destroy()
        print("\nThat's all folks!\n")
        sys.exit(0)

    # Function to update the plot
    def update(self):
        self.y[:-self.chunkSize] = self.y[self.chunkSize:]                 # Shift data, dropping oldest chunk
        self.y[-self.chunkSize:] = self.data                               # Add new chunk
        self.curve.setData(self.x,self.y)                                  # Redraw

    # Function to open a virtual wire from mic to speakers
    def open_audio_wire(self):
        p = pyaudio.PyAudio()
        self.p=p

        if True:
            info = p.get_host_api_info_by_index(0)
            numdev = info.get('deviceCount')
            print('\n',numdev,'audio devices found:')
            for i in range(0,numdev):
                dev_info = p.get_device_info_by_host_api_device_index(0,i)
                #print(dev_info)
                name = dev_info.get('name')
                srate = dev_info.get('defaultSampleRate')
                print('Device',i,'\t:',name,srate)
            print(' ')

        # This is where the WIDTH influences the data format - keep it at 2 bytes for now --> int16
        print( p.get_format_from_width(WIDTH) )
        print( pyaudio.paFloat32, pyaudio.paInt32, pyaudio.paInt24,
               pyaudio.paInt16, pyaudio.paInt8, \
               pyaudio.paUInt8, pyaudio.paCustomFormat )
        
        self.stream = p.open(format=p.get_format_from_width(WIDTH),
                             channels=CHANNELS,
                             rate=RATE,
                             input=True,
                             output=True,
                             stream_callback=self.wire_callback)

        self.stream.start_stream()

    # Audio callback called when player need more samples
    def wire_callback(self,in_data, frame_count, time_info, status):
        # Update data for gui but we can't call the gui update from here since the audio callback
        # is in a different thread
        #print(in_data)
        #gui.data = np.fromstring(in_data, dtype=np.int16)
        gui.data = np.frombuffer(in_data, dtype=np.int16)
        #print(gui.data)
        return (in_data, pyaudio.paContinue)

################################################################################

if __name__ == "__main__":

    print('\n****************************************************************************')
    print('\n   Audio Oscilloscope beginning ...\n')
    
    app  = QtGui.QApplication(sys.argv)
    gui  = OSCOPE_GUI(8000)

    # Open audio loopback (virtual wire from mic to speakers)
    gui.open_audio_wire()
    
    # Setup a timer to update the plot at the chunk rate of the audio wire
    if True:
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(gui.update)
        print( 1000.*gui.chunkSize/gui.fs )
        timer.start(int(1000.*gui.chunkSize/gui.fs))

    print('And away we go ...')
    sys.exit(app.exec_())
    
