import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QTimer
import mbus as modbus
from threading import Thread, ThreadError
import time

# Loading gui
Ui_MainWindow, QtBaseClass = uic.loadUiType('main_gui.ui')

client = modbus.Connection().client
modbus = modbus.Connection()

# Adds

next = 9020

play = 7104     # Play/pause
stop = 7105     # Stop
error = 7201    # Error or Not

states_name = ['Init_Done', 'Op_Busy', 'Op_Done', 'Op_Error', 'Holder_Present', 'Init_Start', 'Op_Start', 'Op_Reset']
states_adds =  [9200,#Init done
                9210,#Op_Busy
                9211,#Op_Done
                9212,#Op_Error 
                9220,#Holder_Present
                9000,#Init_Start
                9010,#Op_Start
                9011]#Op_Reset
                
codes_name = ['Dev_code', 'Op_Code', 'Op_Data1', 'Op_Data2', 'Op_Data3', 'Op_Data4', 'Op_Data5']
codes_adds =   [9110,#Dev_code
                9111,#Op_Code
                9112,#Op_Data1
                9113,#Op_Data2 
                9114,#Op_Data3
                9115,#Op_Data4
                9116]#Op_Data5

read_codes_name = ['Op_ErrorID', 'Op_Data_Read_1', 'Op_Data_Read_2', 'Op_Data_Read_3', 'Op_Data_Read_4', 'Op_Data_Read_5', 'Holder_ID']
read_codes_adds =  [9310,#Op_ErrorID
                    9311,#Op_Data_Read_1
                    9312,#Op_Data_Read_2 
                    9313,#Op_Data_Read_3
                    9314,#Op_Data_Read_4
                    9315]#Op_Data_Read_5

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        # Main window initialization
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        

        # Select first item in lists
        self.DeviceCode.setCurrentRow(0)
        self.OpCode.setCurrentRow(0)
        self.OpData1.setCurrentRow(0)
        self.OpData2.setCurrentRow(0)

        # updating timer
        self.updater = QTimer()
        self.updater.setInterval(500)

        # all connections
        self.ConnectButton.clicked.connect(self.connection)
        self.updater.timeout.connect(self. update_functions)
        self.SetButton.clicked.connect(self.Set_Data)
        self.ExecuteButton.clicked.connect(self.Execute)
        self.NextButton.clicked.connect(self.Next)
        self.PlayButton.clicked.connect(lambda: modbus.write_coil(7104, 1))
        self.StopButton.clicked.connect(lambda: modbus.write_coil(7105, 1))
        self.PlusButton.clicked.connect(lambda: modbus.write_coil(7106, 1))
        self.MinusButton.clicked.connect(lambda: modbus.write_coil(7107, 1))
        self.LoadQueueButton.clicked.connect(self.dg)

        # Initialize Robot States
        for x in range(len(states_name)):
            # Create new item for widgetlist
            self.state_item = QtWidgets.QListWidgetItem(states_name[x])
            # Set font size
            font = QtGui.QFont()
            font.setPointSize(20)
            self.state_item.setFont(font)  
            # Add item to widget list & add Checkbox  
            self.StateList.addItem(self.state_item)
            self.StateList.item(x).setCheckState(QtCore.Qt.Unchecked)

        # Initialize robot Registers
        for x in range(len(codes_name)):
            # Create new item for widgetlist
            self.codes_item = QtWidgets.QListWidgetItem('0')
            self.names_item = QtWidgets.QListWidgetItem(codes_name[x])
            self.code_name_item = QtWidgets.QListWidgetItem('')
            # Set font size
            font = QtGui.QFont()
            font.setPointSize(15)
            self.codes_item.setFont(font)
            self.code_name_item.setFont(font)
            self.names_item.setFont(font)
            # Add item to widget list 
            self.RegistersData.addItem(self.codes_item)
            self.RegistersDataNames.addItem(self.code_name_item)
            self.RegistersName.addItem(self.names_item)

        # Initialize robot read registers
        for x in range(len(read_codes_name)):
            # Create new item for widgetlist
            self.codes_item = QtWidgets.QListWidgetItem('0')
            self.names_item = QtWidgets.QListWidgetItem(read_codes_name[x])
            # Set font size
            font = QtGui.QFont()
            font.setPointSize(15)
            self.codes_item.setFont(font)  
            self.names_item.setFont(font)
            # Add item to widget list 
            self.RegistersReadData.addItem(self.codes_item)
            self.RegistersReadName.addItem(self.names_item)

    def dg(self):
        new = QtWidgets.QFileDialog()
        test = new.getOpenFileName()
        print(test)

    # Connect button
    def connection(self):
        # closes connection, sets new address
        modbus.disconnect()
        self.ip = self.ipText.property('text')
        self.port = self.PortText.property('value')

        # sets status & connects again
        if modbus.connect(self.ip, self.port):
            self.updater.start()
            self.ConnectionStatus.setProperty('text', 'CONNECTED')
            self.ConnectButton.setProperty('text', 'Disconnect')

        else:
            self.updater.stop()
            self.ConnectionStatus.setProperty('text', 'DISCONNECTED')
            self.ConnectButton.setProperty('text', 'Connect')
            self.reset_values()


    def Set_Data(self):
        # save data to array
        codes = [self.DeviceCode.currentRow(), self.OpCode.currentRow(), self.OpData1.currentRow(), self.OpData2.currentRow(),
        str(self.OpData3.property('value')), str(self.OpData4.property('value')), str(self.OpData5.property('value'))]
        # array data to registers
        for x in range(len(codes)):
            modbus.int_to_register(codes_adds[x], int(codes[x]))

    def Execute(self):
        self.Set_Data()
        modbus.write_coil(states_adds[6], True)
        

    def Next(self):
        modbus.write_coil(next, True)
        time.sleep(.5)
        modbus.write_coil(next, False)
    

    def reset_values(self):
        for i in range(len(states_name)):
            self.StateList.item(i).setCheckState(QtCore.Qt.Unchecked)
        
        for i in range(len(codes_name)):
            self.RegistersData.item(i).setText(str('0'))
            self.RegistersDataNames.item(i).setText('')
        
        for i in range(len(read_codes_name)):
            self.RegistersReadData.item(i).setText(str('0'))
        
        self.RunLabel.setProperty('text', 'Not Running')
        self.ErrLabel.setProperty('text', 'Error: 0')
        self.SpeedDisplay.setProperty('value', 0)


    # robot states 
    def robot_states(self):
        # Read states from robot
        for i in range(len(states_adds)):
            state = client.read_coils(states_adds[i]).bits[0]
            if(state):
                state = QtCore.Qt.Checked
            self.StateList.item(i).setCheckState(state)

    # robot data
    def robot_data(self):

        # Read data from robot
        for x in range(len(codes_adds)):
            self.RegistersData.item(x).setText(str(modbus.register_to_int(codes_adds[x])))

        self.RegistersDataNames.item(0).setText( self.DeviceCode.item(int(self.RegistersData.item(0).text())).text() )
        self.RegistersDataNames.item(1).setText( self.OpCode.item(int(self.RegistersData.item(1).text())).text() )
        self.RegistersDataNames.item(2).setText('Hotel')
        self.RegistersDataNames.item(3).setText('Drawer')
        self.RegistersDataNames.item(4).setText('Position')
        self.RegistersDataNames.item(5).setText('Grab Height')
        self.RegistersDataNames.item(6).setText('Additional')
        

    def robot_read_data(self):
        # Read data robot just Read
        for x in range(len(read_codes_adds)):
            self.RegistersReadData.item(x).setText(str(modbus.register_to_int(read_codes_adds[x])))
        # Reading holder ID
        self.RegistersReadData.item(len(read_codes_adds)).setText(str(modbus.read_string(9400,20)))

    def controls_state(self):
        read_speed = modbus.read_input_registers(7101) 

        if(read_speed != self.SpeedDisplay.property('value')):
            self.SpeedDisplay.setProperty('value', read_speed)

        if(modbus.read_coil(7202)):
            self.RunLabel.setProperty('text', 'Running')
        else:
            self.RunLabel.setProperty('text', 'Not Running')
        if(modbus.read_coil(7201)):
            self.ErrLabel.setProperty('text', 'Error: 1')
        else:
            self.ErrLabel.setProperty('text', 'Error: 0')

    # updating all functions using timer
    def update_functions(self):
        try:
            self.robot_states()
            self.robot_data()   
            self.robot_read_data()
            self.controls_state()
        except Exception as ex:
            print(f'Disconnected: {ex}')
            self.connection()
            


# showing window
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())