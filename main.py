##TODO
# WORKING QUEUE

import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QTimer
import mbus as modbus
import jsonhandler as jhandler
from threading import Thread, ThreadError
import time

# Loading gui
Ui_MainWindow, QtBaseClass = uic.loadUiType('main_gui.ui')

client = modbus.Connection().client
modbus = modbus.Connection()

bConnected = False

# Adds
bNext = 9020
bPlay = 7104     # Play/pause
bStop = 7105     # Stop
bSpeedup = 7106
bSpeeddown = 7107
bError = 7201    # Error or Not
bState = 7102

states = jhandler.get_states()
registers = jhandler.get_setregisters()
read_registers = jhandler.get_readregisters()
devices = jhandler.get_devices()
operations = jhandler.get_operations()
hotel_count = jhandler.get_count('hotels')
drawer_count = jhandler.get_count('drawers')

#states_name = ['Init_Done', 'Op_Busy', 'Op_Done', 'Op_Error', 'Holder_Present', 'Init_Start', 'Op_Start', 'Op_Reset', 'Next']
#states_adds =  [9200,#Init done
#                9210,#Op_Busy
#                9211,#Op_Done
#                9212,#Op_Error
#                9220,#Holder_Present
#                9000,#Init_Start
#                9010,#Op_Start
#                9011,#Op_Reset
#                bNext]#Next
                
#codes_name = ['Dev_code', 'Op_Code', 'Op_Data1', 'Op_Data2', 'Op_Data3', 'Op_Data4', 'Op_Data5', 'Op_Data5']
#codes_adds =   [9110,#Dev_code
#                9111,#Op_Code
#                9112,#Op_Data1
#                9113,#Op_Data2 
#                9114,#Op_Data3
#                9115,#Op_Data4
#                9116,#Op_Data5
#                9117]#Op_Data6

#read_codes_name = ['Op_ErrorID', 'Op_Data_Read_1', 'Op_Data_Read_2', 'Op_Data_Read_3', 'Op_Data_Read_4', 'Op_Data_Read_5', 'Holder_ID']
#read_codes_adds =  [9310,#Op_ErrorID
#                    9311,#Op_Data_Read_1
#                    9312,#Op_Data_Read_2 
#                    9313,#Op_Data_Read_3
#                    9314,#Op_Data_Read_4
#                    9315]#Op_Data_Read_5


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):



    def __init__(self):
        # Main window initialization
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)


        self.queue = False

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
        self.GetButton.clicked.connect(self.Get_Data)
        self.ExecuteButton.clicked.connect(self.Execute)
        self.NextButton.clicked.connect(self.Next)
        self.PlayButton.clicked.connect(lambda: modbus.write_coil(bPlay, 1))
        self.StopButton.clicked.connect(lambda: modbus.write_coil(bStop, 1))
        self.PlusButton.clicked.connect(lambda: modbus.write_coil(bSpeedup, 1))
        self.MinusButton.clicked.connect(lambda: modbus.write_coil(bSpeeddown, 1))
        self.QueueButton.clicked.connect(self.Queue_Add)
        self.LoadQueueButton.clicked.connect(self.open_file)
        self.SaveQueueButton.clicked.connect(self.save_file)
        self.StartQueueButton.clicked.connect(lambda: self.Set_Queue_Flag(True))
        self.StopQueueButton.clicked.connect(lambda: self.Set_Queue_Flag(False))
        self.StateList.itemClicked.connect(self.change_state)

        # Initialize Robot States
        for item in range(len(states)):
            # Create new item for widgetlist
            self.state_item = QtWidgets.QListWidgetItem(states[item]['Name'])
            # Set font size
            font = QtGui.QFont()
            font.setPointSize(12)
            self.state_item.setFont(font)

            self.StateList.addItem(self.state_item)
            self.StateList.item(item).setCheckState(QtCore.Qt.Unchecked)

        # Initialize robot Registers
        for item in range(len(registers)):
            # Create new item for widgetlist
            self.codes_item = QtWidgets.QListWidgetItem('0')
            self.names_item = QtWidgets.QListWidgetItem(registers[item]['Name'])
            self.code_name_item = QtWidgets.QListWidgetItem('')
            # Set font size
            font = QtGui.QFont()
            font.setPointSize(12)
            self.codes_item.setFont(font)
            self.code_name_item.setFont(font)
            self.names_item.setFont(font)
            # Add item to widget list 
            self.RegistersData.addItem(self.codes_item)
            self.RegistersDataNames.addItem(self.code_name_item)
            self.RegistersName.addItem(self.names_item)

        # Initialize robot read registers
        for item in range(len(read_registers)):
            # Create new item for widgetlist
            self.codes_item = QtWidgets.QListWidgetItem('0')
            self.names_item = QtWidgets.QListWidgetItem(read_registers[item]['Name'])
            # Set font size
            font = QtGui.QFont()
            font.setPointSize(12)
            self.codes_item.setFont(font)  
            self.names_item.setFont(font)
            # Add item to widget list 
            self.RegistersReadData.addItem(self.codes_item)
            self.RegistersReadName.addItem(self.names_item)

        # Load devices from config
        for item in devices:
            self.device_item = QtWidgets.QListWidgetItem(item['Name'])
            self.DeviceCode.addItem(self.device_item)

        # Load operations from config
        for item in operations:
            self.operation_item = QtWidgets.QListWidgetItem(item['Name'])
            self.OpCode.addItem(self.operation_item)
        
        # Get hotel count
        for x in range(hotel_count+1):
            self.count = QtWidgets.QListWidgetItem(str(x))
            self.OpData1.addItem(self.count)

        # Get drawer count
        for x in range(drawer_count+1):
            self.count = QtWidgets.QListWidgetItem(str(x))
            self.OpData2.addItem(self.count)

    def change_state(self, item):
        try:
            index = self.StateList.indexFromItem(item).row()
            if item.checkState() > 0:
                modbus.write_coil(states[index]['Register'], True)
            else:
                modbus.write_coil(states[index]['Register'], False)
        
        except Exception as ex:
            print(ex)

    def open_file(self):
        # Open file dialogline.rstrip('\n')
        dialog = QtWidgets.QFileDialog()
        file_path = dialog.getOpenFileName(self, 'Open queue','' , "Queue list (*.que)")
        if( len(file_path[0]) != 0 ):
            print(f'Loading file: {file_path[0]}')
            self.QueueList.clear()
            # Read file and load
            file = open(file_path[0], "r")
            for line in file:
                self.QueueList.addItem(line.rstrip('\n'))
            file.close()

    def save_file(self):
        dialog = QtWidgets.QFileDialog()
        file_path = dialog.getSaveFileName(self, 'Save queue','' , "Queue list (*.que)")
        if( len(file_path[0]) != 0 ):
            print(f'Saving to file: {file_path[0]}')
            # Create or overwrite file
            file = open(file_path[0], "w")
            for i in range(self.QueueList.count()):
                file.write(f'{self.QueueList.item(i).text()}\n')
            file.close()


    # Connect button
    def connection(self):
        modbus.disconnect()
        self.ip = self.ipText.property('text')
        self.port = self.PortText.property('value')

        # sets status & connects again
        if modbus.connect(self.ip, self.port):
            self.updater.start()
            self.ConnectionStatus.setProperty('text', 'CONNECTED')
            self.ConnectButton.setProperty('text', 'Disconnect')
            return True

        else:
            self.updater.stop()
            self.reset_values()
            self.ConnectionStatus.setProperty('text', 'DISCONNECTED')
            self.ConnectButton.setProperty('text', 'Connect')
            return False


    def Set_Queue_Flag(self, state):
        self.queue = state

    def Queue_Add(self):
        # add items to queue list
        self.QueueList.addItem(f'{self.DeviceCode.currentRow()+1} {self.OpCode.currentRow()} {self.OpData1.currentRow()} {self.OpData2.currentRow()} {self.OpData3.value()}')

    def Set_Data(self):
        # save data to array
        codes = [self.DeviceCode.currentRow(), self.OpCode.currentRow(), self.OpData1.currentRow(), self.OpData2.currentRow(),
        str(self.OpData3.property('value')), str(self.OpData4.property('value')), str(self.OpData5.property('value')), str(self.OpData6.property('value'))]
        # array data to registers
        for x in range(len(registers)):
            modbus.int_to_register(registers[x]['ID'], int(codes[x]))

    def Get_Data(self):
        
        for x in range (len(registers)):
            print(modbus.register_to_int(registers[x]['ID']))

    def Execute(self):
        self.Set_Data()
        modbus.write_coil(states[6]['Register'], True)
        

    def Next(self):
        modbus.write_coil(states[8]['Register'], True)
        time.sleep(.5)
        modbus.write_coil(states[8]['Register'], False)
    

    def reset_values(self):
        for i in range(len(states)):
            self.StateList.item(i).setCheckState(QtCore.Qt.Unchecked)
        
        for i in range(len(registers)):
            self.RegistersData.item(i).setText(str('0'))
            self.RegistersDataNames.item(i).setText('')
        
        for i in range(len(read_registers)):
            self.RegistersReadData.item(i).setText(str('0'))
        
        self.RunLabel.setProperty('text', 'Not Running')
        self.ErrLabel.setProperty('text', 'Error: 0')
        self.SpeedDisplay.setProperty('value', 0)


    # robot states 
    def robot_states(self):
        # Read states from robot
        for i in range(len(states)):
            state = client.read_coils(states[i]['Register']).bits[0]
            if(state):
                state = QtCore.Qt.Checked
            self.StateList.item(i).setCheckState(state)

    # robot data
    def robot_data(self):

        # Read data from robot
        for x in range(len(registers)):
            self.RegistersData.item(x).setText(str(modbus.register_to_int(registers[x]['ID'])))

        self.RegistersDataNames.item(0).setText( self.DeviceCode.item(int(self.RegistersData.item(0).text())).text() )
        self.RegistersDataNames.item(1).setText( self.OpCode.item(int(self.RegistersData.item(1).text())).text() )
        self.RegistersDataNames.item(2).setText('Hotel')
        self.RegistersDataNames.item(3).setText('Drawer')
        self.RegistersDataNames.item(4).setText('Position')
        self.RegistersDataNames.item(5).setText('Grab Height')
        self.RegistersDataNames.item(6).setText('Additional')
        

    def robot_read_data(self):
        length = len(read_registers)-1
        # Read data robot just Read
        for x in range(length):
            self.RegistersReadData.item(x).setText(str(modbus.register_to_int(read_registers[x]['ID'])))
        # Reading holder ID
        self.RegistersReadData.item(length).setText(str(modbus.read_string(read_registers[length]['ID'],20)))

    def controls_state(self):
        # ROBOT SPEED
        read_speed = modbus.read_input_registers(7101) 
        if(read_speed != self.SpeedDisplay.property('value')):
            self.SpeedDisplay.setProperty('value', read_speed)

        # ROBOT STATUS
        if(modbus.read_coil(7202)):
            self.RunLabel.setProperty('text', 'Running')
        else:
            self.RunLabel.setProperty('text', 'Not Running')
        if(modbus.read_coil(bError)):
            self.ErrLabel.setProperty('text', 'Error: 1')
        else:
            self.ErrLabel.setProperty('text', 'Error: 0')

        # ROBOT MODE
        if(modbus.read_input_registers(bState) == 1):
            self.bState.setProperty('text', 'State: A')
        elif(modbus.read_input_registers(bState) == 2):
            self.bState.setProperty('text', 'State: M')
        else:
            self.bState.setProperty('text', 'State:')
            
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

    def contextMenuEvent(self, event):
        contextMenu = QtWidgets.QMenu(self)
        removeAction = QtWidgets.QAction ("Remove", triggered = self.remove_item)
        clearAction = QtWidgets.QAction ("Clear", triggered = lambda: self.QueueList.clear())

        contextMenu.addAction(removeAction)
        contextMenu.addAction(clearAction)

        contextMenu.exec_(self.mapToGlobal(event.pos()))

    def remove_item(self):
        print('remove item')


    def queue_action(self):
        # queue enabled
        if self.queue:
            self.StartQueueButton.setProperty("enabled", False)
            self.LoadQueueButton.setProperty("enabled", False)
            # is connected
            if self.connection():
                # is running
                if modbus.client.read_discrete_inputs(7202, 1)[0]:    
                    pass
        else:
            self.StartQueueButton.setProperty("enabled", True)
            self.LoadQueueButton.setProperty("enabled", True)

# showing window
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
