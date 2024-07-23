#! /usr/bin/python3
################################################################################
#
# oscope.py - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Audio oscilloscope and recorder
#
################################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
################################################################################

import pyaudio
import time
import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import wave, struct
from audio_io import WaveRecorder

################################################################################

# User params - Keep these as is for now as they have implications later on that
# we'll address later
WIDTH = 2
CHANNELS = 1
RATE = 44100
RATE = 48000
RATE = 8000

colors=['b','g','r','c','m','y','k',
        'dodgerblue','lime','orange','aqua','indigo','gold','gray',
        'navy','limegreen','tomato','cyan','purple','yellow','dimgray']

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
        self.wf=None
        self.rec=None
        self.p=None

        # Start by putting up the root window
        print('Init GUI ...')
        self.win  = QtGui.QWidget()
        self.setCentralWidget(self.win)
        self.setWindowTitle('Audio Oscilloscope by AA2IL')

        # Use a simple grid to layout controls
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

        # The Canvas is where we will put the plot
        row=1
        col=0
        self.canvas = pg.GraphicsWindow()
        self.grid.addWidget(self.canvas,row,col)
        self.p1 = self.canvas.addPlot()
        #self.p1.setLabel('bottom', 'Time', 's')
        self.curve = self.p1.plot(pen='r')
        #self.p1.enableAutoRange('xy', False)
        #self.p1.setXRange(0, np.max(self.x))
        self.p1.showAxis('left',False)
        self.p1.showAxis('bottom',False)
        
        # Allow canvas size to change when we resize the window
        # but make is always visible
        if False:
            sizePolicy = QtGui.QSizePolicy( QtGui.QSizePolicy.MinimumExpanding, 
                                            QtGui.QSizePolicy.MinimumExpanding)
            self.canvas.setSizePolicy(sizePolicy)

        # Let's roll!
        self.resize(500,0)
        self.show()
        #self.win.resize(self.win.minimumSizeHint())
        
    # Function to quit the app
    def Quit(self):
        if self.rec:
            self.rec.stop_recording()

        if self.p:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

        if self.wf:
            #self.wf.writeframes('')
            self.wf.close()
        
        self.win.destroy()
        print("\nThat's all folks!\n")
        sys.exit(0)

    # Function to update the plot
    def update(self):
        if self.rec:
            rb=self.rec.rb
            nsamps=rb.nsamps
            if nsamps>self.chunkSize:
                data=rb.pull(self.chunkSize)
                n=len(data)
                #print(n,nsamps)
                self.y[:-n] = gui.y[n:]                 # Shift data, dropping oldest chunk
                self.y[-n:] = data                      # Add new chunk

                self.rec.write_data(data)               # Save to disk also
                
            else:
                return
                
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
        print('nchan=',CHANNELS,'\tRate=',RATE)
        print('fmt=',p.get_format_from_width(WIDTH))
        print( 'All fmts:',pyaudio.paFloat32, pyaudio.paInt32, pyaudio.paInt24,
               pyaudio.paInt16, pyaudio.paInt8, \
               pyaudio.paUInt8, pyaudio.paCustomFormat )

        self.stream = p.open(format=p.get_format_from_width(WIDTH),
                             channels=CHANNELS,
                             rate=RATE,
                             input=True,
                             output=False,
                             stream_callback=self.wire_callback)

        self.stream.start_stream()

    # Audio callback called when a chunk of data is available
    def wire_callback(self,in_data, frame_count, time_info, status):
        data = np.frombuffer(in_data, dtype=np.int16)

        n=len(data)
        gui.y[:-n] = gui.y[n:]                 # Shift data, dropping oldest chunk
        gui.y[-n:] = data                               # Add new chunk
        
        if False and gui.wf:
            #print(in_data)
            gui.wf.writeframesraw( in_data )
        
        return (in_data, pyaudio.paContinue)


################################################################################

if __name__ == "__main__":

    print('\n****************************************************************************')
    print('\n   Audio Oscilloscope beginning ...\n')
    
    app  = QtGui.QApplication(sys.argv)
    gui  = OSCOPE_GUI(RATE)

    # Open audio loopback (virtual wire from mic to speakers)
    #gui.open_audio_wire()

    # Start audio recorder
    dirname=''
    fname='junk.wav'
    #fname = dirname+'capture'+s+'.wav'
    if True:
        
        gui.rec = WaveRecorder(fname, 'wb',wav_rate=RATE)
        idx=gui.rec.list_input_devices('USB Audio CODEC')
        #idx=gui.rec.list_input_devices('default')
        if idx:
            gui.rec.start_recording(idx)
            #time.sleep(5.0)
        else:
            print('Cant find radio USB Audio CODEC :-(')
            sys.exit(0)

    elif False:
        
        s=time.strftime("_%Y%m%d_%H%M%S", time.gmtime())      # UTC
        wf = wave.open(fname,'w')
        wf.setnchannels(1)
        wf.setsampwidth(2) 
        wf.setframerate(RATE)
        gui.wf=wf
            
    # Setup a timer to update the plot at the chunk rate of the audio wire
    if True:
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(gui.update)
        tt= int( 1000.*gui.chunkSize/gui.fs )
        print('tt (ms)=',tt)
        timer.start(tt)

    print('And away we go ...')
    sys.exit(app.exec_())
    
