# reSpeaker XVF3800 I2S Firmware Changelog

## v1.0.8 (Current)

### Changed

- Swapped the resource IDs of `DOA_VALUE` and `LED_RING_COLOR` to match the USB firmware interface:
  - `DOA_VALUE`: 19 → 18
  - `LED_RING_COLOR`: 18 → 19

### Fixed

- Decoupled DOA state updates from the currently selected LED effect.
- DOA direction and speech-detection state are now updated when internal DOA data is received, ensuring that `DOA_VALUE` remains current even when the DOA LED effect is not active.

## v1.0.7 

### Audio and DSP Tuning

- Disabled the AEC 125 Hz high-pass filter by default.
- Reduced the post-processing AGC maximum gain from `64.0` to `32.0`.
- Changed the default system delay from `12` to `-30`.
- Routed both default I2S output channels to ASR ouput beam 0.
- Reduced the AIC3104 headphone and line-output gain from `6 dB` to `3 dB`.

## v1.0.6

### Added

- Added the read-only `DOA_VALUE` control command.
- The command returns two `uint16` values:
  - Direction of arrival, normalized to `0–359` degrees.
  - Speech-detection status: `1` when speech is detected and `0` otherwise.

## v1.0.5

### Added

- Added the `LED_RING` effect as LED effect mode `5`.
- Added the `LED_RING_COLOR` read/write command, allowing independent configuration of all 12 WS2812 LEDs.

### Changed

- Increased the AIC3104 headphone and line-output gain from `0 dB` to `6 dB`.

## v1.0.4 

### Fixed

- Added a 100 ms delay after a mute-button press to debounce the input and prevent repeated mute-state changes caused by switch bounce.
