# reSpeaker XVF3800 Host Control Tool

A Python implement of the `xvf_host` application, which provides the convenience of controlling and monitoring the reSpeaker XVF3800 on any platform.

## System Requirements

- Python 3.6+
- pyusb library
- libusb library

## Installation & Dependencies

```bash
# Install Python dependencies
pip install pyusb
```

## Usage

### Basic Syntax

```bash
python xvf_host.py [options] command [--values value(s)...]
```

### Options

- `-l, --list`: List all supported commands with detailed information
- `--vid`: Set USB vendor ID (default: 0x2886)
- `--pid`: Set USB product ID (default: 0x001A)
- `--values`: Provide values for write commands (optional)

### Usage Examples

#### 1. List all available commands

```bash
python xvf_host.py --list
```

#### 2. Read firmware version information

```bash
python xvf_host.py VERSION
```

#### 3. Read DOA (Direction of Arrival) values

```bash
python xvf_host.py DOA_VALUE
```

#### 4. Set LED color (hexadecimal format)

```bash
python xvf_host.py LED_COLOR --values 0xFF0000
```

#### 5. Set LED brightness

```bash
python xvf_host.py LED_BRIGHTNESS --values 50
```

#### 6. Read microphone array geometry

```bash
python xvf_host.py AEC_MIC_ARRAY_GEO
```


## USB Six-Channel Output Selection

With the reSpeaker six-channel USB firmware, each USB capture channel can be routed independently. Use USB firmware v2.1.0 or later for configurable channels 3–6; the older v2.0.8 six-channel firmware has fixed raw microphone outputs on those channels. See the [USB firmware README](../xmos_firmwares/usb/readme.md) for available images and release notes.

### Channel Commands

USB channel numbers below are 1-based. Each command reads or writes two integers: `category` selects a signal group, and `source` selects a signal within that group. Microphone and beam source indexes are 0-based.

| USB capture channel | Command |
| --- | --- |
| 1 (left) | `AUDIO_MGR_OP_L` |
| 2 (right) | `AUDIO_MGR_OP_R` |
| 3 | `AUDIO_MGR_OP_CH3` |
| 4 | `AUDIO_MGR_OP_CH4` |
| 5 | `AUDIO_MGR_OP_CH5` |
| 6 | `AUDIO_MGR_OP_CH6` |

Run the following examples from this directory. Omit `--values` to read the current selection; provide exactly two values to change it:

```bash
python xvf_host.py AUDIO_MGR_OP_CH3
python xvf_host.py AUDIO_MGR_OP_CH3 --values 1 0
```

The second command routes microphone index 0 to USB channel 3. Reading it back should return `AUDIO_MGR_OP_CH3: [1, 0]`.

### Signal Categories and Sources

The following summarizes the [XMOS Output Selection reference](https://www.xmos.com/documentation/XM-014888-PC/html/modules/fwk_xvf/doc/user_guide/03_using_the_host_application.html#output-selection). Signal availability depends on the firmware configuration.

| Category | Signal | Source |
| --- | --- | --- |
| `0` | Silence | `0` |
| `1` | Microphones without gain or delay | `0`–`3` |
| `2` | Unpacked microphones; undefined without packed input | `0`–`3` |
| `3` | Microphones with gain and delay | `0`–`3` |
| `4` | Reference, converted to 16 kHz | `0` |
| `5` | Reference with delay | `0` |
| `6` | Processed beams | `0`, `1`: focused; `2`: scanning; `3`: automatic selection |
| `7` | AEC residuals or ASR beams | `0`–`3` |
| `8` | User-selected outputs | `0`, `1` |
| `9` | Outputs after SHF DSP | `0`–`3` |
| `10` | Reference at interface rate | `0`–`5` at 48 kHz; `0`, `1` at 16 kHz |
| `11` | Microphones with gain, before delay | `0`–`3` |
| `12` | Reference with gain and delay | `0` |

Category `8` follows the firmware's user-output configuration; XMOS's reference implementation copies the automatically selected beam. Its evaluation-board defaults may differ from reSpeaker defaults. Read the current settings before changing them.

### Example: Two Processed Outputs and Four Raw Microphones

This example explicitly selects the automatically chosen processed beam on channels 1 and 2, and microphone indexes 0–3 on channels 3–6. It is an example layout, not a factory-reset command.

```bash
python xvf_host.py AUDIO_MGR_OP_L --values 6 3
python xvf_host.py AUDIO_MGR_OP_R --values 6 3
python xvf_host.py AUDIO_MGR_OP_CH3 --values 1 0
python xvf_host.py AUDIO_MGR_OP_CH4 --values 1 1
python xvf_host.py AUDIO_MGR_OP_CH5 --values 1 2
python xvf_host.py AUDIO_MGR_OP_CH6 --values 1 3
```

Configure the recording application for six-channel capture at 16 kHz to record all six streams. Routing changes the content of each channel, not the USB channel count or sample rate.

The four raw microphone streams bypass voice enhancement and normally have lower levels than processed audio. For listening or speech recognition, gain can be applied in host software. For algorithm development, acoustic measurements, or calibration, preserve the original levels and relative microphone levels.

### Change One Channel or Save the Configuration

For example, route the fourth microphone to channel 1, or silence channel 2:

```bash
python xvf_host.py AUDIO_MGR_OP_L --values 1 3
python xvf_host.py AUDIO_MGR_OP_R --values 0 0
```

Use any of the six channel commands with a valid category/source pair to change that channel independently. `AUDIO_MGR_OP_ALL` configures the packed L/R source slots; it is not a shortcut for setting USB channels 1–6.

After checking the routing, save the current configuration to flash if it should survive a restart:

```bash
python xvf_host.py SAVE_CONFIGURATION --values 1
```

This saves the current configuration, including other supported persistent settings, not just the last channel selection. Without saving, a restart restores the previously saved configuration or the firmware defaults.

## Output Format

### Read Operation Output

- **LED commands** (LED_COLOR, LED_DOA_COLOR, LED_RING_COLOR):
  ```
  LED_COLOR: [0x00FF00, 0x0000FF]
  ```

- **Floating-point numbers**: Display with 3 decimal places
  ```
  AEC_MIC_ARRAY_GEO: [0.033, -0.033, 0.000, 0.033, 0.033, 0.000, -0.033, 0.033, 0.000, -0.033, -0.033, 0.000]
  ```

- **Integers and strings**: Maintain original format
  ```
  VERSION: [2, 0, 7]
  BLD_MSG: ['u', 'a', '-', 'i', 'o', '1', '6', '-', 's', 'q', 'r']
  ```
