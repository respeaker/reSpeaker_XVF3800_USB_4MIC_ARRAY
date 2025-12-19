
import sys
import struct
import argparse
import usb.core
import usb.util
import libusb_package
import time

CONTROL_SUCCESS = 0
SERVICER_COMMAND_RETRY = 64

# name, resid, cmdid, length, type, description
PARAMETERS = {
    # APPLICATION_SERVICER_RESID commands   
    "VERSION": (48, 0, 3, "ro", "uint8", "The version number of the firmware. The format is VERSION_MAJOR VERSION_MINOR VERSION_PATCH"),
    "BLD_MSG": (48, 1, 50, "ro", "char", "Retrieve the build message built in to the firmware, normally the build configuration name"),
    "BLD_HOST": (48, 2, 30, "ro", "char", "Retrieve details of the CI build host used to build the firmware"),
    "BLD_REPO_HASH": (48, 3, 40, "ro", "char", "Retrieve the GIT hash of the sw_xvf3800 repo used to build the firmware"),
    "BLD_MODIFIED": (48, 4, 6, "ro", "char", "Show whether or not the current firmware repo has been modified from the official release. Requires use of a GIT repo"),
    "BOOT_STATUS": (48, 5, 3, "ro", "char", "Shows whether or not the firmware has been booted via SPI or JTAG/FLASH"),
    "TEST_CORE_BURN": (48, 6, 1, "rw", "uint8", "Set to enable core burn to exercise worst case timing. This will reboot the chip, reset all parameters to default and significantly increase power consumption."),
    "REBOOT": (48, 7, 1, "wo", "uint8", "Set to any value to reboot the chip and reset all parameters to default."),
    "USB_BIT_DEPTH": (48, 8, 2, "rw", "uint8", "Only relevant for the UA device variant. For the UA device, set or get the USB bit depth IN, OUT to either 16, 24 or 32. Setting will reboot the chip, resetting all other parameters to default. If issued to the INT device, a set is ignored and the device is not rebooted while a get always returns 0 as both IN and OUT bit depths."),
    "SAVE_CONFIGURATION": (48, 9, 1, "wo", "uint8", "Set to any value to save the current configuration to flash."),
    "CLEAR_CONFIGURATION": (48, 10, 1, "wo", "uint8", "Set to any value to clear the current configuration and revert to the default configuration."),
    
    # AEC_RESID commands
    "SHF_BYPASS": (33, 70, 1, "rw", "uint8", "AEC bypass"),
    "AEC_NUM_MICS": (33, 71, 1, "ro", "int32", "Number of microphone inputs into the AEC"),
    "AEC_NUM_FARENDS": (33, 72, 1, "ro", "int32", "Number of farend inputs into the AEC"),
    "AEC_MIC_ARRAY_TYPE": (33, 73, 1, "ro", "int32", "Microphone array type (1 - linear, 2 - squarecular)"),
    "AEC_MIC_ARRAY_GEO": (33, 74, 12, "ro", "float", "Microphone array geometry. Each microphone is represented by 3 XYZ coordinates in m."),
    "AEC_AZIMUTH_VALUES": (33, 75, 4, "ro", "radians", "Azimuth values in radians - beam 1, beam 2, free-running beam, 3 - auto-select beam"),
    "TEST_AEC_DISABLE_CONTROL": (33, 76, 1, "wo", "uint32", "Disable Control processing in the AEC resource. Only to be used for internal testing! Do not use in normal operation. When disabled, there's no way to bring back control without restarting the device."),
    "AEC_CURRENT_IDLE_TIME": (33, 77, 1, "ro", "uint32", "AEC processing current idle time in 10ns ticks"),
    "AEC_MIN_IDLE_TIME": (33, 78, 1, "ro", "uint32", "AEC processing minimum idle time in 10ns ticks"),
    "AEC_RESET_MIN_IDLE_TIME": (33, 79, 1, "wo", "uint32", "Reset the AEC minimum idle time. The value of the argument passed is ignored."),
    "AEC_SPENERGY_VALUES": (33, 80, 4, "ro", "float", "Speech energy level values for each beam. Any value above 0 indicates speech. Higher values indicates louder or closer speech, however noise, echo and reverb can cause the energy level to decrease. 0 - beam 1, 1 - beam 2, 2 - free-running beam, 3 - auto-select beam"),
    "AEC_FIXEDBEAMSAZIMUTH_VALUES": (33, 81, 2, "rw", "radians", "Azimuth values in radians for beams in fixed mode - fixed beam 1, fixed beam 2"),
    "AEC_FIXEDBEAMSELEVATION_VALUES": (33, 82, 2, "rw", "radians", "Elevation angles in radians for the beams in fixed mode. 0 - fixed beam 1, 1 - fixed beam 2"),
    "AEC_FIXEDBEAMSGATING": (33, 83, 1, "rw", "uint8", "Enables/disables gating for beams in fixed mode. When enabled, speech energy is used to determine which beam should be active; inactive beams are silenced."),
    "SPECIAL_CMD_AEC_FAR_MIC_INDEX": (33, 90, 2, "wo", "int32", "Set Far and Mic index for AEC filter read. Also used as a trigger command that starts a new filter read"),
    "SPECIAL_CMD_AEC_FILTER_COEFF_START_OFFSET": (33, 91, 1, "rw", "int32", "start offset to get or set the filter coefficients from"),
    "SPECIAL_CMD_AEC_FILTER_COEFFS": (33, 92, 15, "rw", "float", "get or set AEC filter coefficients"),
    "SPECIAL_CMD_AEC_FILTER_LENGTH": (33, 93, 1, "ro", "int32", "get AEC filter length"),
    "AEC_FILTER_CMD_ABORT": (33, 94, 1, "wo", "int32", "Reset the special command state machine. Used for safely exiting from an AEC filter read/write command sequence that has gone wrong."),
    "AEC_AECPATHCHANGE": (33, 0, 1, "ro", "int32", "AEC Path Change Detection. Valid range: 0,1 (false,true)"),
    "AEC_HPFONOFF": (33, 1, 1, "rw", "int32", "High-pass Filter on microphone signals. Valid range: 0,1,2,3,4 (0:Off, 1:on70, 2:on125, 3:on150, 4:on180)"),
    "AEC_AECSILENCELEVEL": (33, 2, 2, "rw", "float", "Power threshold for signal detection in adaptive filter.(set,cur),  Valid range (set): [0.0 .. 1.0] Valid range (cur): 0.05*set, 1e-6f or set."),
    "AEC_AECCONVERGED": (33, 3, 1, "ro", "int32", "Flag indicating whether AEC is converged. Valid range: 0,1 (false,true)"),
    "AEC_AECEMPHASISONOFF": (33, 4, 1, "rw", "int32", "Pre-emphasis and de-emphasis filtering for AEC. Valid range: 0,1,2 (off,on,on_eq)on: Emphasis filter for speech signals without modification of far-end ref. on_eq: Emphasis filter for far-end reference signals where the low frequencies are boosted by e.g. an equalizer."),
    "AEC_FAR_EXTGAIN": (33, 5, 1, "rw", "float", "External gain in dB applied to the far-end reference signals. Valid range: [-inf .. inf]"),
    "AEC_PCD_COUPLINGI": (33, 6, 1, "rw", "float", "Sensitivity parameter for PCD. Valid range: [0.0 .. 1.0]PCD can be disabled by setting a value outside the range"),
    "AEC_PCD_MINTHR": (33, 7, 1, "rw", "float", "Minimum threshold value used in PCD. Valid range: [0.0 .. 0.02]"),
    "AEC_PCD_MAXTHR": (33, 8, 1, "rw", "float", "Maximum threshold value used in PCD. Valid range: [0.025 .. 0.2]"),
    "AEC_RT60": (33, 9, 1, "ro", "float", "Current RT60 estimate. Valid range: [0.250 .. 0.900] (seconds) A negative value indicates that the RT60 estimation is invalid."),
    "AEC_ASROUTONOFF": (33, 35, 1, "rw", "int32", "Enables the automatic speech recognition (ASR) output: if set to 0, the AEC residuals are output, one channel per microphone, if set to 1, the ASR processed output is used, where each channel is associated with a beam from the beamformer. Valid range: 0,1 (off, on)"),
    "AEC_ASROUTGAIN": (33, 36, 1, "rw", "float", "Fixed gain applied to qsr output, i.e., only applied if ASROUTONOFF==1.. Valid range: [0.0 .. 1000.0] (linear gain factor)"),
    "AEC_FIXEDBEAMSONOFF": (33, 37, 1, "rw", "int32", "Enables or disables fixed focused beam mode. Valid range: 0,1 (off, on)"),
    "AEC_FIXEDBEAMNOISETHR": (33, 38, 2, "rw", "float", "Threshold value for updating the noise canceller when fixed beam mode is enabled. A higher value indicates that the noise canceller may update when the free running beam is close to the fixed beam. A lower value indicates that the noise canceller may update when the free running beam is further away from the focused beam.[BECLEAR_NUMBER_OF_BEAMS],  Valid range: [0.0 .. 1.0]"),
    
    # AUDIO_MGR_RESID commands
    "AUDIO_MGR_MIC_GAIN": (35, 0, 1, "rw", "float", "Audio Mgr pre SHF microphone gain"),
    "AUDIO_MGR_REF_GAIN": (35, 1, 1, "rw", "float", "Audio Mgr pre SHF reference gain"),
    "AUDIO_MGR_CURRENT_IDLE_TIME": (35, 2, 1, "ro", "int32", "Get audio manager current idle time in 10ns ticks"),
    "AUDIO_MGR_MIN_IDLE_TIME": (35, 3, 1, "ro", "int32", "Get audio manager min idle time in 10ns ticks"),
    "AUDIO_MGR_RESET_MIN_IDLE_TIME": (35, 4, 1, "wo", "int32", "Reset audio manager min idle time. The value of the argument passed is ignored."),
    "MAX_CONTROL_TIME": (35, 5, 1, "ro", "int32", "Get audio manager max control time"),
    "RESET_MAX_CONTROL_TIME": (35, 6, 1, "wo", "int32", "Reset audio manager max control time. The value of the argument passed is ignored."),
    "I2S_CURRENT_IDLE_TIME": (35, 7, 1, "ro", "int32", "Get I2S current idle time in 10ns ticks"),
    "I2S_MIN_IDLE_TIME": (35, 8, 1, "ro", "int32", "Get I2S min idle time in 10ns ticks"),
    "I2S_RESET_MIN_IDLE_TIME": (35, 9, 1, "wo", "int32", "I2S reset idle time. The value of the argument passed is ignored."),
    "I2S_INPUT_PACKED": (35, 10, 1, "rw", "uint8", "Will expect packed input on both I2S or USB channels if this is not 0. Note, could take up to 3 samples to take effect."),
    "AUDIO_MGR_SELECTED_AZIMUTHS": (35, 11, 2, "ro", "radians", "This returns the azimuths determined by the beam_selection function in post_shf_dsp.c. The default implementation will provide a processed DoA at index 0 and the DoA of the auto select beam at index 1. The processed DoA uses speech energy to select from the DoA on each fixed beam to provide the direction of a speaker. NAN will be returned if neither of the fixed beams contain speech. Versions 2.0.0 and earlier of XVF3800 had a different default implementation of beam_selection which returned the DoA associated with the AUDIO_MGR_SELECTED_CHANNELS"),
    "AUDIO_MGR_SELECTED_CHANNELS": (35, 12, 2, "rw", "uint8", "Default implementation of post processing will use this to select which channels should be output to MUX_USER_CHOSEN_CHANNELS. Note that a customer implementation of the beam selection stage could override this command. How this channel selection aligns with actual output depends on the mux configuration"),
    "AUDIO_MGR_OP_PACKED": (35, 13, 2, "rw", "uint8", "<L>, <R>; Sets/gets packing status for L and R output channels"),
    "AUDIO_MGR_OP_UPSAMPLE": (35, 14, 2, "rw", "uint8", "<L>, <R>; Sets/gets upsample status for L and R output channels, where appropriate"),
    "AUDIO_MGR_OP_L": (35, 15, 2, "rw", "uint8", "<category>, <source>; Sets category and source for L output channel. Equivalent to AUDIO_MGR_OP_L_PK0"),
    "AUDIO_MGR_OP_L_PK0": (35, 16, 2, "rw", "uint8", "<category>, <source>; Sets category and source for first (of three) sources on the L channel in packed mode. Equivalent to AUDIO_MGR_OP_L"),
    "AUDIO_MGR_OP_L_PK1": (35, 17, 2, "rw", "uint8", "Sets category and source for second (of three) sources on the L channel in packed mode"),
    "AUDIO_MGR_OP_L_PK2": (35, 18, 2, "rw", "uint8", "Sets category and source for third (of three) sources on the L channel in packed mode"),
    "AUDIO_MGR_OP_R": (35, 19, 2, "rw", "uint8", "<category>, <source>; Sets category and source for R output channel. Equivalent to AUDIO_MGR_OP_R_PK0"),
    "AUDIO_MGR_OP_R_PK0": (35, 20, 2, "rw", "uint8", "<category>, <source>; Sets category and source for first (of three) sources on the R channel in packed mode. Equivalent to AUDIO_MGR_OP_R"),
    "AUDIO_MGR_OP_R_PK1": (35, 21, 2, "rw", "uint8", "Sets category and source for second (of three) sources on the R channel in packed mode"),
    "AUDIO_MGR_OP_R_PK2": (35, 22, 2, "rw", "uint8", "Sets category and source for third (of three) sources on the R channel in packed mode"),
    "AUDIO_MGR_OP_ALL": (35, 23, 12, "rw", "uint8", "Sets category and source for all 3 sources on L channel and all 3 sources for R channel. Equivalent to AUDIO_MGR_OP_[L,R]_PK[0,1,2] with successive pairs of arguments"),
    "I2S_INACTIVE": (35, 24, 1, "ro", "uint8", "Returns whether the main audio loop is exchanging samples with I2S (0). If not (1), I2S is inactive"),
    "AUDIO_MGR_FAR_END_DSP_ENABLE": (35, 25, 1, "rw", "uint8", "Enables/disables XVF3800 far-end DSP (if implemented). Write a 1 to enable, 0 to disable"),
    "AUDIO_MGR_SYS_DELAY": (35, 26, 1, "rw", "int32", "Delay, measured in samples, that is applied to the reference signal before passing to SHF algorithm"),
    "I2S_DAC_DSP_ENABLE": (35, 27, 1, "rw", "uint8", "Indicates if the DAC performs DSP on the far-end reference signal. If enabled (1), use the I2S signal as input to the audio pipeline, even in the UA configuration"),


    # GPO_SERVICER_RESID commands 
    "GPO_READ_VALUES": (20, 0, 5, "ro", "uint8", "Get current logic level of all GPO pins, in order of Pin X0D11, X0D30, X0D31, X0D33 and X0D39."),
    "GPO_WRITE_VALUE": (20, 1, 2, "wo", "uint8", "Set current logic level of selected GPO pin. Supports Pin X0D11, X0D30, X0D31, X0D33 and X0D39."),
    "GPO_PORT_PIN_INDEX": (20, 2, 2, "rw", "uint32", "GPO port index and pin index that the following commands would be directed to"),
    "GPO_PIN_VAL": (20, 3, 3, "wo", "uint8", "value to write to one pin of a GPO port. Payload specifies port_index, pin_index and value to write to the pin"),
    "GPO_PIN_ACTIVE_LEVEL": (20, 4, 1, "rw", "uint32", "Active level of the port/pin specified by the GPO_PORT_PIN_INDEX command. 1 = ACTIVE_HIGH, 0 = ACTIVE_LOW"),
    "LED_EFFECT": (20, 12, 1, "rw", "uint8", "Set the LED effect mode, 0 = off, 1 = breath, 2 = rainbow, 3 = single color, 4 = doa, 5 = ring"),
    "LED_BRIGHTNESS": (20, 13, 1, "rw", "uint8", "Set the brightness value of the LED for the breath and rainbow mode"),
    "LED_GAMMIFY": (20, 14, 1, "rw", "uint8", "Set to enable gamma correction, 0 = disable, 1 = enable"),
    "LED_SPEED": (20, 15, 1, "rw", "uint8", "Set the effect speed of breath and rainbow mode"),
    "LED_COLOR": (20, 16, 1, "rw", "uint32", "Set the LED color of breath mode and single color mode"),
    "LED_DOA_COLOR": (20, 17, 2, "rw", "uint32", "Set the LED color of doa mode, the first value is the base color and the second value is the doa color"),
    "DOA_VALUE": (20, 18, 2, "ro", "uint16", "Get the doa value and if speech is detected, payload[0] = doa value, from 0 to 359, payload[1] = 1 if speech is detected, 0 if not"),
    "LED_RING_COLOR": (20, 19, 12, "rw", "uint32", "Set the LED color of ring mode, each value is the color of one LED"),

    # PP_RESID commands
    "PP_CURRENT_IDLE_TIME": (17, 70, 1, "ro", "uint32", "PP processing current idle time in 10ns ticks"),
    "PP_MIN_IDLE_TIME": (17, 71, 1, "ro", "uint32", "PP processing minimum idle time in 10ns ticks"),
    "PP_RESET_MIN_IDLE_TIME": (17, 72, 1, "wo", "uint32", "Reset the PP minimum idle time. The value of the argument passed is ignored."),
    "PP_NL_MODEL_CMD_ABORT": (17, 94, 1, "wo", "int32", "Reset the special command state machine. Used for safely exiting from a NL model read/write sequence that has gone wrong."),
    "PP_EQUALIZATION_CMD_ABORT": (17, 100, 1, "wo", "int32", "Reset the special command state machine. Used for safely exiting from an equalization read/write sequence that has gone wrong."),
    "PP_AGCONOFF": (17, 10, 1, "rw", "int32", "Automatic Gain Control. Valid range: 0,1 (off,on)"),
    "PP_AGCMAXGAIN": (17, 11, 1, "rw", "float", "Maximum AGC gain factor. Valid range: [1.0 .. 1000.0] (linear gain factor)"),
    "PP_AGCDESIREDLEVEL": (17, 12, 1, "rw", "float", "Target power level of the output signal. Valid range: [1e-8 .. 1.0] (power level)"),
    "PP_AGCGAIN": (17, 13, 1, "rw", "float", "Current AGC gain factor. Valid range: [1.0 .. 1000.0] (linear gain factor)"),
    "PP_AGCTIME": (17, 14, 1, "rw", "float", "Ramp-up/down time-constant. Valid range: [0.5 .. 4.0] (seconds)"),
    "PP_AGCFASTTIME": (17, 15, 1, "rw", "float", "Ramp down time-constant in case of peaks. Valid range: [0.05 .. 4.0] (seconds)"),
    "PP_AGCALPHAFASTGAIN": (17, 16, 1, "rw", "float", "Gain threshold enabling fast alpha mode. Valid range: [0.0 .. 1000.0] (linear gain factor)"),
    "PP_AGCALPHASLOW": (17, 17, 1, "rw", "float", "Slow memory parameter for speech power. Valid range [0.0 .. 1.0]"),
    "PP_AGCALPHAFAST": (17, 18, 1, "rw", "float", "Fast memory parameter for speech power. Valid range [0.0 .. 1.0]"),
    "PP_LIMITONOFF": (17, 19, 1, "rw", "int32", "Limiter on communication output. Valid range: 0,1 (off,on)"),
    "PP_LIMITPLIMIT": (17, 20, 1, "rw", "float", "Maximum limiter power. Valid range: [1e-8 .. 1.0] (power level)"),
    "PP_MIN_NS": (17, 21, 1, "rw", "float", "Gain-floor for stationary noise suppression. Valid range: [0.0 .. 1.0]"),
    "PP_MIN_NN": (17, 22, 1, "rw", "float", "Gain-floor for non-stationary noise suppression. Valid range: [0.0 .. 1.0]"),
    "PP_ECHOONOFF": (17, 23, 1, "rw", "int32", "Echo suppression. Valid range: 0,1 (off,on)"),
    "PP_GAMMA_E": (17, 24, 1, "rw", "float", "Over-subtraction factor of echo (direct and early components). Valid range: [0.0 .. 2.0]"),
    "PP_GAMMA_ETAIL": (17, 25, 1, "rw", "float", "Over-subtraction factor of echo (tail components). Valid range: [0.0 .. 2.0]"),
    "PP_GAMMA_ENL": (17, 26, 1, "rw", "float", "Over-subtraction factor of non-linear echo. Valid range: [0.0 .. 5.0]"),
    "PP_NLATTENONOFF": (17, 27, 1, "rw", "int32", "Non-Linear echo attenuation. Valid range: 0,1 (off,on)"),
    "PP_NLAEC_MODE": (17, 28, 1, "rw", "int32", "Non-Linear AEC training mode. Valid range: 0,1,2 (normal,train,train2)"),
    "PP_MGSCALE": (17, 29, 3, "rw", "float", "Minimum gain scale for acoustic echo suppression.(max,min,cur),  Valid range (max,min): [(1.0,0.0) .. (1e5,max)] Valid range (cur): min or max."),
    "PP_FMIN_SPEINDEX": (17, 30, 1, "rw", "float", "In case of double talk, frequencies below SPEINDEX are more suppressed than frequencies above SPEINDEX. The actual suppression is depending on the setting of DTSENSITIVE. The parameter is not a taste parameter but needs to be tuned for a specific device. Valid range: [0.0 .. 7999.0]"),
    "PP_DTSENSITIVE": (17, 31, 1, "rw", "int32", "Tradeoff between echo suppression and doubletalk performance. A lower value prefers high echo suppression (possibly at the cost of less doubletalk performance), a higher value prefers better doubletalk performance (possibly at the cost of good echo suppression). Good doubletalk performance is only possible for hardware without much non-linearities. When the value has 2 digits, for robustness an extra near-end speech detector is used. Valid range: [0 .. 5, 10 .. 15]"),
    "PP_ATTNS_MODE": (17, 32, 1, "rw", "int32", "Additional reduction of AGC gain during non-speech. Valid range: 0,1 (off, on)"),
    "PP_ATTNS_NOMINAL": (17, 33, 1, "rw", "float", "Amount of additional reduction during non-speech at nominal speech level. Valid range: [0.0 .. 1.0]"),
    "PP_ATTNS_SLOPE": (17, 34, 1, "rw", "float", "Determines the extra amount of suppression during non-speech when the AGC level increases at lower speech level. The extra attenuation is given by (agcgain_nominal/agcgain_current)^attns_slope. With a value of 1.0 the amount of noise in the output remains approximately the same, independent of the agc gain. Valid range: [0.0 .. 5.0]"),
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
        data_cnt = data[2] # cnt
        data_type = data[4] # data type
        payload = []

        if data_type == 'float' or data_type == 'radians':
            for i in range(data_cnt):
                payload += struct.pack(b'f', float(data_list[i]))
        elif data_type == 'char':
            # For char arrays, convert string to bytes
            payload = bytearray(data_list, 'utf-8') if isinstance(data_list, str) else bytearray(data_list)
        elif data_type == 'uint8':
            for i in range(data_cnt):
                payload += data_list[i].to_bytes(1, byteorder='little')
        elif data_type == 'uint32' or data_type == 'int32':
            for i in range(data_cnt):
                payload += struct.pack(b'I' if data_type == 'uint32' else b'i', data_list[i])
        else:
            # Default to int32 for other types
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

        read_attempts = 1
        windex = data[0] # resid
        wvalue = 0x80 | data[1] # cmdid
        data_cnt = data[2] # cnt
        data_type = data[4] # data type
        if data_type == 'uint8' or data_type == 'char':
            length = data_cnt + 1 # 1 byte for status
        elif data_type == 'float' or data_type == 'radians' or data_type == 'uint32' or data_type == 'int32':
            length = data_cnt * 4 + 1 # 1 byte for status
        elif data_type == 'uint16':
            length = data_cnt * 2 + 1 # 1 byte for status

        response = self.dev.ctrl_transfer(
            usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, wvalue, windex, length, self.TIMEOUT)
        while True:
            if read_attempts > 100:
                raise ValueError('Read attempt exceeds 100 times')
            if response[0] == CONTROL_SUCCESS:
                break
            elif response[0] == SERVICER_COMMAND_RETRY:
                read_attempts += 1
                response = self.dev.ctrl_transfer(
                    usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
                    0, wvalue, windex, length, self.TIMEOUT)
            else:
                raise ValueError('Unknown status code: {}'.format(response[0]))
            time.sleep(0.01)
        
        print("ReadCMD: cmdid: {}, resid: {}, payload: {}".format(wvalue, windex, response.tolist()))

        if data_type == 'uint8':
            byte_data = response.tobytes()
            match_str = '<'
            for i in range(data_cnt):
                match_str += 'B'
            result = struct.unpack(match_str, byte_data[1:])
        elif data_type == 'char':
            # For char arrays, convert bytes to string
            byte_data = response.tobytes()
            # Remove status byte and null terminators
            result = byte_data[1:].rstrip(b'\x00').decode('utf-8', errors='ignore')
        elif data_type == 'radians' or data_type == 'float':
            byte_data = response.tobytes()
            match_str = '<'
            for i in range(data_cnt):
                match_str += 'f'
            result = struct.unpack(match_str, byte_data[1:])
        elif data_type == 'uint32':
            byte_data = response.tobytes()
            match_str = '<'
            for i in range(data_cnt):
                match_str += 'I'
            result = struct.unpack(match_str, byte_data[1:])
        elif data_type == 'int32':
            byte_data = response.tobytes()
            match_str = '<'
            for i in range(data_cnt):
                match_str += 'i'
            result = struct.unpack(match_str, byte_data[1:])
        elif data_type == 'uint16':
            byte_data = response.tobytes()
            match_str = '<'
            for i in range(data_cnt):
                match_str += 'H'
            result = struct.unpack(match_str, byte_data[1:])
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



def parse_value(value_str):
    """Parse a value string that can be decimal, hex (0x prefix), or hex ($ prefix)"""
    try:
        # Try hex formats first (0x prefix or $ prefix)
        if value_str.startswith(('0x', '0X')):
            return int(value_str, 16)
        elif value_str.startswith('$'):
            return int(value_str[1:], 16)
        else:
            # Try as decimal float first, then decimal int
            try:
                return float(value_str)
            except ValueError:
                return int(value_str)
    except ValueError:
        raise ValueError(f"Cannot parse '{value_str}' as a number (supports decimal and hex formats like 0xFF or $FF)")

def case_insensitive_command(value):
    """Convert command to uppercase and validate it exists"""
    if not isinstance(value, str):
        raise argparse.ArgumentTypeError(f"Command must be a string, got {type(value)}")
    
    upper_value = value.upper()
    
    # Check if the uppercase version exists in PARAMETERS
    if upper_value not in PARAMETERS:
        # Provide helpful error message with similar commands
        available_commands = list(PARAMETERS.keys())
        similar_commands = [cmd for cmd in available_commands if upper_value in cmd.upper()]
        if similar_commands:
            raise argparse.ArgumentTypeError(
                f"Invalid command '{value}'. Did you mean one of: {similar_commands}? "
            )
        else:
            raise argparse.ArgumentTypeError(
                f"Invalid command '{value}'. "
            )
    
    return upper_value

def list_commands():
    """Display all supported commands with their detailed information."""
    print("\n=== Supported Commands ===\n")
    print(f"{'Command':<30} {'RESID':<6} {'CMDID':<6} {'Length':<7} {'Type':<12} {'Access':<8} {'Description'}")
    print("-" * 120)
    
    for name, info in PARAMETERS.items():
        resid, cmdid, length, param_type, access, description = info
        print(f"{name:<30} {resid:<6} {cmdid:<6} {length:<7} {param_type:<12} {access:<8} {description}")

def main():
    parser = argparse.ArgumentParser(description='ReSpeaker Host Control Script')
    parser.add_argument('-l', '--list', action='store_true',
                       help='list all supported commands with detailed information')
    parser.add_argument('COMMAND', nargs='?', type=case_insensitive_command, 
                       help='command to execute (e.g., VERSION, DOA_VALUE, etc.)')
    parser.add_argument('--vid', type=lambda x: int(x, 0), default=0x2886,
                       help='usb vendor ID (default: 0x2886)')
    parser.add_argument('--pid', type=lambda x: int(x, 0), default=0x001A,
                       help='usb product ID (default: 0x001A)')
    parser.add_argument('--values', nargs='+', type=parse_value,
                       help='values for write commands (only for write operations). Supports decimal (123, 1.5) and hex (0x7B, $7B) formats')
    
    args = parser.parse_args()
    
    # Handle list command
    if args.list:
        list_commands()
        sys.exit(0)
    
    dev = find(vid=args.vid, pid=args.pid)
    if not dev:
        print('No device found')
        sys.exit(1)

    try:
        if args.values:
            if PARAMETERS[args.COMMAND][3] == "ro":
                print(f"Error: {args.COMMAND} is read-only and cannot be written to")
                sys.exit(1)
            
            # Convert values to appropriate types based on parameter type
            param_type = PARAMETERS[args.COMMAND][4]
            if param_type == "float" or param_type == "radians":
                args.values = [float(v) for v in args.values]
            else:
                args.values = [int(v) for v in args.values]
            
            if PARAMETERS[args.COMMAND][2] != len(args.values):
                print(f"Error: {args.COMMAND} value count is {PARAMETERS[args.COMMAND][2]}, but {len(args.values)} values provided")
                sys.exit(1)

            dev.write(args.COMMAND, args.values)
        else:
            if PARAMETERS[args.COMMAND][3] == "wo":
                print(f"Error: {args.COMMAND} is write-only and cannot be read")
                resid, cmdid, length, param_type, access, description = PARAMETERS[args.COMMAND]
                print(f"{'Command':<30} {'RESID':<6} {'CMDID':<6} {'Length':<7} {'Type':<12} {'Access':<8} {'Description'}")
                print("-" * 120)
                print(f"{args.COMMAND:<30} {resid:<6} {cmdid:<6} {length:<7} {param_type:<12} {access:<8} {description}")
                sys.exit(1)
            
            result = dev.read(args.COMMAND)
            if args.COMMAND == "LED_COLOR" or args.COMMAND == "LED_DOA_COLOR" or args.COMMAND == "LED_RING_COLOR":
                formatted_result = []
                for val in result:
                    formatted_result.append(f"0x{val:06X}")
                print(f"{args.COMMAND}: [{', '.join(formatted_result)}]")
            else:
                formatted_result = []
                for val in result:
                    if isinstance(val, float):
                        formatted_result.append(f"{val:.3f}")
                    elif isinstance(val, str):
                        formatted_result.append(f"'{val}'")
                    else:
                        formatted_result.append(str(val))
                print(f"{args.COMMAND}: [{', '.join(formatted_result)}]")

        print(f"Done!")
            
    except Exception as e:
        print(f"Error executing command {args.COMMAND}: {e}")
        sys.exit(1)
    finally:
        dev.close()

if __name__ == '__main__':
    main()
