# reSpeaker XVF3800 I2S Firmware

## Introduction

This directory contains I2S firmware images for the reSpeaker XVF3800. The current firmware variants operate either as an I2S master at 48 kHz or as an I2S slave at 16 kHz. Select the image whose sample rate and clock role match the connected host or audio device.

- With the **I2S master firmware**, the XVF3800 generates the bit clock (`BCLK`) and word-select/left-right clock (`LRCLK`/`WS`). The connected device must be configured as an I2S slave and receive these clocks.
- With the **I2S slave firmware**, the XVF3800 receives `BCLK` and `LRCLK`/`WS`. The connected host or audio device must be configured as an I2S master and provide stable clocks at the required sample rate.

The master/slave designation describes clock ownership only; it does not describe the direction of the audio data. The two devices must use complementary roles. Connecting two masters causes clock contention, while connecting two slaves leaves the bus without a clock source.

## Changelog

### v1.0.9 (Current)

#### Added

- Added the `MUTE_FUNCTION_ENABLE` read/write control command (command ID `8` of the IO config servicer; existing command IDs are unchanged):
  - `1` (default): the onboard Mute button performs the built-in mute action, same as before.
  - `0`: disables the built-in mute action, turning the button into a pure event source so the host can own the mute semantics. Edge detection and event reporting stay active.
  - The setting is not persisted to flash: it resets to `1` on every boot, so the host must re-send the command after startup if the built-in action should stay disabled.

#### Fixed

- Fixed `GPI_EVENT_PENDING_ALL` always returning `0`. The event bitmap was accumulated with `&=` instead of `|=`, so the host never saw any pending events through this command.

### v1.0.8

#### Changed

- Swapped the resource IDs of `DOA_VALUE` and `LED_RING_COLOR` to match the USB firmware interface:
  - `DOA_VALUE`: 19 → 18
  - `LED_RING_COLOR`: 18 → 19

#### Fixed

- Decoupled DOA state updates from the currently selected LED effect.
- DOA direction and speech-detection state are now updated when internal DOA data is received, ensuring that `DOA_VALUE` remains current even when the DOA LED effect is not active.

### v1.0.7

#### Audio and DSP Tuning

- Disabled the AEC 125 Hz high-pass filter by default.
- Reduced the post-processing AGC maximum gain from `64.0` to `32.0`.
- Changed the default system delay from `12` to `-30`.
- Routed both default I2S output channels to ASR ouput beam 0.
- Reduced the AIC3104 headphone and line-output gain from `6 dB` to `3 dB`.

### v1.0.6

#### Added

- Added the read-only `DOA_VALUE` control command.
- The command returns two `uint16` values:
  - Direction of arrival, normalized to `0–359` degrees.
  - Speech-detection status: `1` when speech is detected and `0` otherwise.

### v1.0.5

#### Added

- Added the `LED_RING` effect as LED effect mode `5`.
- Added the `LED_RING_COLOR` read/write command, allowing independent configuration of all 12 WS2812 LEDs.

#### Changed

- Increased the AIC3104 headphone and line-output gain from `0 dB` to `6 dB`.

### v1.0.4

#### Fixed

- Added a 100 ms delay after a mute-button press to debounce the input and prevent repeated mute-state changes caused by switch bounce.
