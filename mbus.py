from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

class Connection():
    client = ModbusTcpClient()

    def connect(self, ip, port):
        self.client.host = ip
        self.client.port = port
        return self.client.connect()

    def disconnect(self):
        return self.client.close()
        
    def register_to_int(self, address):
        try:
            result = self.client.read_holding_registers(address, 1, unit=1).registers
            decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big, wordorder=Endian.Big)
            decoded = decoder.decode_16bit_int()
            return decoded
        except Exception as ex:
            print(ex)

    def int_to_register(self, address, value):
        try:
            # Create a builder
            builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
            # Add num to builder
            builder.add_16bit_int(value)
            payload = builder.to_registers()
            payload = builder.build()
            registers = builder.to_registers()
            # Write value
            self.client.write_registers(address, registers, unit=1)
        except Exception as ex:
            print(ex)

    def write_coil(self, address, value):
        try:
            self.client.write_coil(address, value)
        except Exception as ex:
            print(ex)

    def read_coil(self, address):
        try:
            return self.client.read_discrete_inputs(address).bits[0]
        except Exception as ex:
            print(ex)

    def read_input_registers(self, address):
        try:
            result = self.client.read_input_registers(address, 1, unit=1).registers
            decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big, wordorder=Endian.Big)
            decoded = decoder.decode_16bit_int()
            return decoded
        except Exception as ex:
            print(ex)

    def read_string(self, address, length):
        try:
            # Read register
            result = self.client.read_holding_registers(address, length, unit=1).registers
            # Set decoder
            decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big, wordorder=Endian.Big)
            # Decode and format
            decoded = decoder.decode_string(8)
            decoded = decoded.decode('UTF-8')
            decoded = decoded.replace("\x00", "")
            return decoded
        except Exception as ex:
            print(ex)