# How to control reSpeaker XVF3800

The reSpeaker XVF3800 is equipped with a control interface that allows users to configure the device's operation, set or read parameter data and save parameter data on the device. Users can control the device via the USB or I2C interface. A sample host application, `xvf_host` (for Linux, macOS, and Raspberry Pi OS) or `xvf_host.exe` (for Windows), is provided to easily connect to the control interface of the reSpeaker XVF3800.

## Introducing xvf_host

The sample host application `xvf_host` can be found in the `host_control/<platform>/` subdirectory of this repository. Supported platforms include linux_x86_64, mac_x86_64, mac_arm64, rpi_32bit, rpi_64bit, and win32. The entire directory needs to be transferred to the host computer and can be placed anywhere convenient. This directory should contain the following files:

```
.
├── (lib)command_map.(so/dll/dylib) # All platforms
├── libdevice_i2c.so                # RPi only
├── libdevice_spi.so                # RPi only
├── dfu_cmds.yaml                   # RPi only
├── transport_config.yaml           # RPi only
├── (lib)device_usb.(so/dll/dylib)  # All platforms
├── libusb-1.0.0.dylib              # mac_x86_64 and mac_arm64 only
├── xvf_dfu                         # RPi only
└── xvf_host(.exe)                  # All platforms
```

To verify the installation of the xvf_host application, navigate to the directory and run the application as shown in the examples below. On Windows:
```
xvf_host.exe --help
```

On Linux, macOS, and Raspberry Pi OS, appropriate permissions must be set first:
```
sudo chmod +x xvf_host
sudo ./xvf_host --help
```

## Accessing reSpeaker XVF3800

After connecting the reSpeaker XVF3800 to the host device(e.g. Windows PC) via USB (or I2C for RPi), run the following command to verify that the host application can access the control interface of the reSpeaker XVF3800:
```
./xvf_host(.exe) VERSION
// or use other specific control protocol, like i2c, spi, usb
./xvf_host(.exe) --use i2c VERSION  
```
This command should return the software version of the reSpeaker XVF3800, like:
```
./xvf_host VERSION   
Device (USB)::device_init() -- Found device VID: 10374 PID: 26 interface: 3
VERSION 2 0 2 
```

## Introducing Control Commands

### LED Control
These Commands Control the WS2812 LED Ring of the reSpeaker XVF3800.
| Command name   | Read/Write | Params | Param format | Description                                                                                            |   |   |   |   |   |
|----------------|------------|--------|--------------|--------------------------------------------------------------------------------------------------------|---|---|---|---|---|
| LED_EFFECT     | RW         | 1      | uint8_t      | Set the LED effect mode, 0 = off, 1 = breath, 2 = rainbow, 3 = single color, 4 = doa                   |   |   |   |   |   |
| LED_BRIGHTNESS | RW         | 1      | uint8_t      | Set the brightness value of the LED for the breath and rainbow mode                                    |   |   |   |   |   |
| LED_GAMMIFY    | RW         | 1      | uint8_t      | Set to enable gamma correction, 0 = disable, 1 = enable                                                |   |   |   |   |   |
| LED_SPEED      | RW         | 1      | uint8_t      | Set the effect speed of breath and rainbow mode                                                        |   |   |   |   |   |
| LED_COLOR      | RW         | 1      | uint32_t     | Set the LED color of breath mode and single color mode                                                 |   |   |   |   |   |
| LED_DOA_COLOR  | RW         | 2      | uint32_t     | Set the LED color of doa mode, the first value is the base color and the second value is the doa color |   |   |   |   |   |
|                |            |        |              |                                                                                                        |   |   |   |   |   |

By default, reSpeaker XVF3800 runs `rainbow` mode when boot, and then switch to `doa` mode after 2seconds. Here is an example to set a `breath` mode:
```
./xvf_host led_effect 1
./xvf_host led_color 0xff8800
./xvf_host led_speed 1
./xvf_host led_brightness 255
```

### Save Configuration

These commands are for saving/clearing all the writable parameters on the reSpeaker XVF3800.

| Command name        | Read/Write | Params | Param format | Description                                                                                  |   |   |   |   |   |
|---------------------|------------|--------|--------------|----------------------------------------------------------------------------------------------|---|---|---|---|---|
| SAVE_CONFIGURATION  | RW         | 1      | uint8_t      | Set to any value to save the current configuration to flash.                                 |   |   |   |   |   |
| CLEAR_CONFIGURATION | RW         | 1      | uint8_t      | Set to any value to clear the current configuration and revert to the default configuration. |   |   |   |   |   |
|                     |            |        |              |                                                                                              |   |   |   |   |   |

Here are the examples to save/clear configuration:
```
// To save configuration
./xvf_host save_configuration 1
// To clear configuration, send the following command, and reboot the reSpeaker XVF3800
./xvf_host clear_configuration 1
```

