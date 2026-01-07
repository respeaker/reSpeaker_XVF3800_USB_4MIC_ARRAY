
import sys
import struct
import usb.core
import usb.util
import libusb_package
import time

# name, resid, cmdid, length, type
PARAMETERS = {
    "VERSION": (48, 0, 3, "ro", "uint8"),
    "AEC_AZIMUTH_VALUES": (33, 75, 16, "ro", "radians"),
    "DOA_VALUE": (20, 18, 4, "ro", "uint16"),
    "REBOOT": (48, 7, 1, "wo", "uint8"),
}

class ReSpeaker:
    TIMEOUT = 100000

    def __init__(self, dev):
        self.dev = dev

    def write(self, name, data_list):
        try:
            data = PARAMETERS[name]
        except KeyError:
            return
        
        if data[3] == "ro":
            raise ValueError('{} is read-only'.format(name))
        
        if len(data_list) != data[2]:
            raise ValueError('{} value count is not {}'.format(name, data[2]))

        windex = data[0] # resid
        wvalue = data[1] # cmdid
        data_type = data[4] # type
        data_cnt = data[2] # cnt
        payload = []

        if data_type == 'float' or data_type == 'radians':
            for i in range(data_cnt):
                payload += struct.pack(b'f', float(data_list[i]))
        elif data_type == 'char' or data_type == 'uint8':
            for i in range(data_cnt):
                payload += data_list[i].to_bytes(1, byteorder='little')
        else:
            for i in range(data_cnt):
                payload += struct.pack(b'i', data_list[i])
        
        print("WriteCMD: cmdid: {}, resid: {}, payload: {}".format(wvalue, windex, payload))

        self.dev.ctrl_transfer(
            usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, wvalue, windex, payload, self.TIMEOUT)


    def read(self, name):
        try:
            data = PARAMETERS[name]
        except KeyError:
            return

        resid = data[0]
        cmdid = 0x80 | data[1]
        length = data[2] + 1 # 1 byte for status

        response = self.dev.ctrl_transfer(
            usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, cmdid, resid, length, self.TIMEOUT)

        if data[4] == 'uint8':
            result = response.tolist()
        elif data[4] == 'radians':
            byte_data = response.tobytes()
            num_values = ( length - 1 ) / 4
            match_str = '<'
            for i in range(int(num_values)):
                match_str += 'f'
            result = struct.unpack(match_str, byte_data[1:length])
        elif data[4] == 'uint16':
            result = response.tolist()

        return result

    def close(self):
        """
        close the interface
        """
        usb.util.dispose_resources(self.dev)


def find(vid=0x2886, pid=0x001A):
    if sys.platform.startswith('win'):
        dev = libusb_package.find(idVendor=vid, idProduct=pid)
    else:
        dev = usb.core.find(idVendor=vid, idProduct=pid)
    if not dev:
        return

    return ReSpeaker(dev)

def main():
    dev = find()
    if not dev:
        print('No device found')
        sys.exit(1)

    print('{}: {}'.format("VERSION", dev.read("VERSION")))
    while True:
        result = dev.read("DOA_VALUE")
        print('{}: {}, {}: {}'.format("SPEECH_DETECTED", result[3], "DOA_VALUE", result[1]))
        time.sleep(1)

    dev.close()

if __name__ == '__main__':
    main()
