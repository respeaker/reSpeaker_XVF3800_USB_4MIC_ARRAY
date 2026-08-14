
# reSpeaker XVF3800 USB Firmware Changelog

## v2.1.0 (Current)

### Added

- Added configurable USB direct-output routing for channels 3 through 6. The new `AUDIO_MGR_OP_CH3`, `AUDIO_MGR_OP_CH4`, `AUDIO_MGR_OP_CH5`, and `AUDIO_MGR_OP_CH6` commands allow each channel's source to be selected independently, with support for product defaults and saved configurations.
- Added runtime control of the AIC3104 headphone and line-output levels through the `AIC3104_HP_LEVEL` and `AIC3104_LINEOUT_LEVEL` commands. Both outputs support gains from 0 dB to 9 dB.
- Added flash persistence for the AIC3104 output levels. The values are included in `SAVE_CONFIGURATION` and restored during startup.

### Changed

- Changed the default AIC3104 headphone and line-output gain to 8 dB.

## v2.0.10 

### Fixed

- Fixed USB audio recovery after bus resets and speed changes. High-speed and full-speed endpoint descriptors, packet sizes, FIFOs, buffers, alternate settings, and software-PLL state are now restored for the active bus speed.
- Fixed a Linux capture failure that could report isochronous `EOVERFLOW` errors after the device changed from full-speed back to high-speed operation.
- Decoupled DOA state tracking from the active LED effect, allowing DOA status to remain current even when the LED ring is using a non-DOA effect.

## v2.0.9

### Fixed

- Fixed restoration of saved fixed-beam settings after startup. Fixed-beam enable and gating settings are reapplied after AEC initialization, and changes to fixed-beam azimuth, elevation, and gating are retained in the runtime configuration.

## v2.0.8

### Added

- Added the `ua-io16-6ch-sqr` USB Audio Class profile for six-channel, 16 kHz capture.
- Added raw microphone signals to USB capture channels 3 through 6; channels 1 and 2 retain the normal configured stereo outputs.

## v2.0.7

### Added

- Added LED ring mode (`LED_EFFECT = 5`).
- Added the `LED_RING_COLOR` command for setting the color of each of the 12 LEDs independently.

## v2.0.6 

### Added

- Added the read-only `DOA_VALUE` command. It returns the detected direction from 0 to 359 degrees together with a speech-detected flag.

### Changed

- Increased the default AIC3104 headphone and line-output gain from 0 dB to 6 dB.

### Fixed

- Fixed incorrect color output on WS2812-2020 LEDs by correcting channel ordering and improving signal timing.
- Avoided unnecessary writes to GPIO output ports that have no configured output pins.

## v2.0.5

### Fixed

- Added a 100 ms debounce delay to the mute button handler to prevent repeated or unintended mute state changes.
