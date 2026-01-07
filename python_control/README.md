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
python xvf_host.py [options] command [value(s)...]
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

## Parameter Limitations

**Note:** The `AEC_FIXEDBEAMSONOFF` parameter does not currently support being set to 1. Setting this value may cause unexpected behavior.

