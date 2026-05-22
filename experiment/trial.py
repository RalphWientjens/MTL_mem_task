"""
Created on Thu May 21 15:00:00 2026

@author: Ralph Wientjens

Simple memory experiment to activate Medial temporal lobe/Hippocampus.

trial.py – tSNR hippocampal subfield localizer

Phases
------
start_end   : still fixation cross (baseline, 16 s)
remember    : text cue (12 s)
fixation    : rotating fixcross + beep onset (jittered 8–12 s)
"""

from exptools2.core import Trial
from psychopy import visual, sound
from psychopy.core import Clock
import os


class MemoryTrial(Trial):
    """
    Two-phase memory trial: remember → fixation (with beep + rotating cross).
    Also handles a flanking start_end baseline phase (still fixcross).
    """

    def __init__(self, session, trial_nr, phase_durations, phase_names,
                 parameters=None, timing='seconds',
                 load_next_during_phase=None, verbose=True):

        super().__init__(
            session=session,
            trial_nr=trial_nr,
            phase_durations=phase_durations,
            phase_names=phase_names,
            timing=timing,
            load_next_during_phase=load_next_during_phase,
            verbose=verbose,
        )

        self.parameters = parameters or {}
        self.is_edge_trial = self.parameters.get('is_edge_trial', False)

        stim_dir = os.path.join(os.path.dirname(__file__))

        # ── Stimuli ────────────────────────────────────────────────────

        # Still fixcross (baseline phases) - always needed
        self.fixation_still = visual.TextStim(
            self.session.win, text='+',
            height=50, color='black', font='Arial'
        )
        
        # Only initialize cue and beep for memory trials
        if not self.is_edge_trial:

            self.cue = self.parameters.get("cue", "")

            self.cue_text = visual.TextStim(
                self.session.win, text=self.cue,
                height=50, color='black', font='Arial'
            )

            # Reminder beep
            beep_path = os.path.join(stim_dir, "sounds",
                                    self.parameters.get("reminder_sound", "beep.wav"))
            self.reminder_beep = sound.Sound(beep_path)


        # Rotating fixcross: two overlapping lines rotated 45° apart
        line_kwargs = dict(
            win=self.session.win,
            start=(-15, 0), end=(15, 0),
            lineColor='black', lineWidth=8
        )
        self.fix_h = visual.Line(**line_kwargs)  # horizontal arm
        self.fix_v = visual.Line(**line_kwargs)  # vertical arm (rotated 90°)
        self._rot_angle = 0.0   # current rotation in degrees


        # Internal tracking
        self._beep_played = False
        self.block = self.parameters.get('block', 0)

    # ── Helpers ────────────────────────────────────────────────────────

    def _draw_rotating_fixcross(self):
        """Increment rotation and draw the two-line fixcross."""
        self._rot_angle = (self._rot_angle + 0.5) % 360   # 2°/frame → ~120°/s at 60 Hz; tune as needed
        self.fix_h.ori = self._rot_angle
        self.fix_v.ori = self._rot_angle + 90
        self.fix_h.draw()
        self.fix_v.draw()

    # ── Phase hooks ────────────────────────────────────────────────────

    def on_phase_start(self, phase):
        if 0 <= phase < len(self.phase_names):
            self.phase_name = self.phase_names[phase]
        else:
            raise IndexError(f"Phase index {phase} out of range.")

        if self.is_edge_trial:
            return  # nothing to set up for edge trials

        if self.phase_name == "remember":
            self.cue_text.setText(self.cue)

        elif self.phase_name == "fixation":
            self._rot_angle = 0.0
            self._beep_played = False   # beep will fire on first draw() of this phase

    def draw(self):
        # Delegate first-frame setup
        if self.last_phase is None or self.phase != self.last_phase:
            self.on_phase_start(self.phase)
            self.last_phase = self.phase
            return   

        if self.phase_name == "start_end":
            self.fixation_still.draw()

        elif self.phase_name == "remember":
            self.cue_text.draw()

        elif self.phase_name == "fixation":
            # Play beep once at the very start of this phase
            if not self._beep_played:
                self.reminder_beep.play()
                self._beep_played = True
            self._draw_rotating_fixcross()

    # ── Eyetracker messaging ───────────────────────────────────────────

    def log_phase_info(self, phase=None):
        super().log_phase_info(phase)
        if self.eyetracker_on:
            msg = f'trial {self.trial_nr} cue {self.parameters.get("cue", "")} phase {self.phase_names[self.phase] if phase is None else self.phase_names[phase]}'
            self.session.tracker.sendMessage(msg)

    def run(self):
        """Run the trial."""
        self.last_phase = None
        self.phase = 0
        self.exit_phase = False
        self.exit_trial = False

        print(f"Trial {self.trial_nr} starts at {self.session.clock.getTime():.3f}")

        trial_clock = Clock()
        trial_clock.reset()

        phase_start = 0.0
        useParallel = hasattr(self.session, "parallelPort")

        for phase_dur in self.phase_durations:

            # Marker value: use phase index (1-indexed so 0 means "off")
            marker_val = self.parameters.get("trial_nr", 99)

            # Log phase start on the flip
            self.session.win.callOnFlip(self.log_phase_info, phase=self.phase)

            if useParallel:
                self.session.win.callOnFlip(self.session.parallelPort.setData, marker_val)
                self.parallelPortStartFrame = self.session.nr_frames  # anchor to current frame count

            if self.load_next_during_phase == self.phase:
                self.load_next_trial(phase_dur)

            # ---- PHASE LOOP (seconds) ----
            if self.timing == 'seconds':
                while (
                    trial_clock.getTime() < phase_start + phase_dur
                    and not self.exit_phase
                    and not self.exit_trial
                ):
                    self.draw()
                    if self.draw_each_frame:
                        # Reset parallel port to 0 one frame after phase-start pulse
                        if useParallel and self.session.nr_frames == self.parallelPortStartFrame + 1:
                            self.session.win.callOnFlip(
                                self.session.parallelPort.setData, 0
                            )
                        self.session.win.flip()
                        self.session.nr_frames += 1
                    self.get_events()
            
            # ---- PHASE LOOP (frames) ----
            else:
                for _ in range(phase_dur):
                    if self.exit_phase or self.exit_trial:
                        break
                    self.draw()
                    self.session.win.flip()
                    self.get_events()
                    self.session.nr_frames += 1

            # Reset exit_phase for next phase
            if self.exit_phase:
                self.exit_phase = False
            if self.exit_trial:
                break

            phase_start += phase_dur
            self.phase += 1