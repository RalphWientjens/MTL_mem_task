# MTL Memory Localizer Experiment

PsychoPy / exptools2 experiment code for a **Medial Temporal Lobe (MTL) localizer** task. This is a simple memory cue paradigm designed to activate the hippocampus and surrounding MTL regions during fMRI scanning.

## Experiment Overview

The task presents **memory cues** (words) that participants must actively think about and mentally retrieve memories associated with those words. Between cues, a rotating fixation cross provides timing structure. The experiment begins and ends with still fixation cross baseline periods for localizer purposes.

### Trial Structure

Each memory trial consists of two phases:
1. **Remember (12s):** A word cue is displayed. Participants imagine and retrieve memories associated with the word.
2. **Fixation (8–12s, jittered):** A rotating fixation cross is shown while a reminder beep sounds at onset.

### Edge Trials (Baseline)

- **Start of experiment:** 16s still fixation cross (baseline).
- **End of experiment:** 16s still fixation cross (baseline).

These edge trials are used for localizer contrast purposes.

---

## Repository Structure

### `main.py`
Entry point that initializes and runs the session.

- Expects arguments:
  1. `subject` – participant ID
  2. `run` – run number

- Creates output directory structure: `logs/sub-{subject}/sub-{subject}_run-{run}/`
- Instantiates `MemorySession` and calls `ts.run()`

### `session.py`
Defines session logic and trial generation.

Key contents:
- `MemorySession`: main session class (inherits from `PylinkEyetrackerSession`)
  - Loads memory cues from `cues.tsv`
  - Creates memory trials organized by block
  - Manages edge trials (baseline fixation periods)
  - Handles eyetracker calibration and MRI scanner sync
- `create_mem_trials()`: generates randomized trials across blocks
- `create_edge_trials()`: generates baseline fixation trials at start/end

### `trial.py`
Implements trial rendering and phase execution.

Key classes:
- `MemoryTrial(Trial)`: a single memory trial with two phases
  - **Stimuli:**
    - Still fixation cross (baseline phases)
    - Text cue (remember phase)
    - Rotating fixation cross with beep (fixation phase)
  - **Methods:**
    - `on_phase_start()`: initializes phase-specific content
    - `draw()`: renders appropriate stimulus for current phase
    - `run()`: executes trial with frame-by-frame rendering and parallel port markers

### `expsettings.yml`
Experiment configuration (window, monitor, test settings).

Notable fields:
- `window.size`, `window.fullscr`, `window.waitBlanking`
- `monitor.distance`, `monitor.width`
- `test_settings.eyetracker_on`, `test_settings.mri_on`, `test_settings.parallel_markers_on`
- `test_settings.test_mode_on` (for fast testing with reduced durations)

### `cues.tsv`
Stimulus file containing memory cues (words).

**Required columns:**
- `cue` – the word/phrase to display
- `reminder_sound` – path to beep sound file (relative to `sounds/` directory)

**Example format:**
```
cue	reminder_sound
apple	beep.wav
bicycle	beep.wav
mountain	beep.wav
```

### `sounds/`
Directory containing audio files (e.g., `beep.wav`) referenced in `cues.tsv`.

---

## How to Run

### 1) Create/activate a Python environment

This project depends on PsychoPy + exptools2 + standard scientific Python packages.

You can use the `exptools2_environment.yml` to install dependencies, or visit https://github.com/VU-Cog-Sci/exptools2 for detailed installation instructions.

### 2) Run from the experiment folder

In the terminal, `cd` into the directory containing `main.py`, then run:

```bash
python main.py <subject> <run>
```

**Example:**
```bash
python main.py 001 1
```

This will:
- Run the experiment for subject 001, run 1
- Create output in `logs/sub-001/sub-001_run-1/`
- Save logs, eyetracking data (if enabled), and behavioral data

### 3) Configuration

Before running, ensure:
- `cues.tsv` is in the experiment directory with your word cues
- `sounds/beep.wav` exists in a `sounds/` subdirectory
- `expsettings.yml` is configured appropriately (fullscreen, MRI sync, eyetracker settings, etc.)

---

## Features

- **Block-based randomization:** Trials are randomized independently per block
- **Eyetracking integration:** Optional EyeLink eyetracker support with automatic EDF→HDF5 conversion
- **MRI/fMRI compatible:** Scanner sync support (wait for 't' pulse), parallel port markers for timing precision
- **Test mode:** Fast testing with 10% duration scaling (set `test_mode_on: true` in `expsettings.yml`)
- **Rotating fixation cross:** Dynamic visual feedback during ITI (2°/frame rotation)

---

## Output

The experiment generates:
- **Behavioral log:** `{output_str}_behavioral.tsv` – trial-by-trial data (cues, timings, responses)
- **Trial log:** `{output_str}_trial.log` – detailed frame-by-frame event log
- **Eyetracking data** (if enabled):
  - `{output_str}.edf` (raw EyeLink file)
  - `{output_str}.hdf5` (converted HDF5 format)