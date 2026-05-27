"""
Created on Sun Jan 4th 12:00:00 2026

@author: Ralph Wientjens

Session class for Episodic Extinction experiment.
"""

from exptools2.core import PylinkEyetrackerSession #Set on if eyetracker is used, otherwise use Session
from exptools2.core import Session
from trial import MemoryTrial
import numpy as np
import pandas as pd
from psychopy import core, visual, event, logging
import random
# from psychopy.core import getMouse
import os
import sys
import yaml
from pathlib import Path
import hedfpy

PHASES_trial = ["remember", "fixation"]   # just names now
PHASE_edge   = ["start_end"]

class MemorySession(PylinkEyetrackerSession):
    """
    Session class for the Hippocampus localizer experiment.
    Manages the experimental session.
    """

    def __init__(self,
                 output_str,
                 output_dir=None,
                 settings_file="expsettings.yml",
                 OS="windows",
                 test_mode=False,
                 blocks=2,
                 enable_eyetracker=False,
                 enable_parallel_markers=False,
                 enable_mri=False):
        """
        Initialize Session.

        Parameters
        ----------
        output_str : str
            Basename for output files
        output_dir : str, optional
            Directory for output files
        settings_file : str, optional
            Path to settings filealright
        """
        
        # With this:
        with open(settings_file, 'r') as f:
            tempSettings = yaml.safe_load(f)

        super().__init__(
            output_str,
            output_dir=output_dir,
            settings_file=settings_file,
            eyetracker_on = tempSettings["test_settings"]["eyetracker_on"])

        # Hide mouse cursor based on settings
        self.win.mouseVisible = self.settings["mouse"]["visible"]
        self.mri_on = self.settings["test_settings"]["mri_on"]

        if sys.platform == 'win32':
            from ctypes import windll

        self.enable_parallel_markers = self.settings["test_settings"]["parallel_markers_on"]
        if self.enable_parallel_markers:
            currentDir = os.path.dirname(os.path.realpath(__file__))
            windll.LoadLibrary(currentDir + "/inpoutx64.dll")     # uncomment when running on Windows and using parallel port, make sure to have the inpoutx64.dll in the same directory as this script
            from psychopy import parallel
            self.parallelPort = parallel.ParallelPort(address='0x3FF8')

        self.test_mode = self.settings["test_settings"]["test_mode_on"]  # Store test mode flag

        stimset_path = os.path.join(
            os.path.dirname(__file__),
            "cues.tsv"
        )

        self.stimset = pd.read_csv(stimset_path, sep="\t")
        self.n_trials = len(self.stimset)
        self.TR = self.settings["mri"]["TR"] if self.mri_on else None
    
    def jittered_iti(self, fixed_duration, min_iti=2, max_iti=8, TR: float=1.6):
        """Return an ITI that brings total trial duration to a TR multiple."""
        total_min = fixed_duration + min_iti
        total_max = fixed_duration + max_iti
        
        # All TR multiples in the valid range
        n_min = int(np.ceil(total_min / TR))
        n_max = int(np.floor(total_max / TR))
        
        if n_min > n_max:
            raise ValueError(f"No TR multiple in ITI range [{min_iti}, {max_iti}] for fixed duration {fixed_duration}")
        
        chosen_n = random.randint(n_min, n_max)
        return chosen_n * TR - fixed_duration
    
    def create_mem_trials(self):
        """Create memory trials for the session."""

        TR = self.TR if self.TR is not None else 1.6
        # main trials, by block
        self.trials_by_block = []

        for block in range(2):

            # Randomize order uniquely per block
            randomized_stimset = self.stimset.sample(frac=1).reset_index(drop=True)

            block_trials = []

            for trial_nr, stim_row in randomized_stimset.iterrows():

                params = stim_row.to_dict()
                params["block"] = block + 1

                # Total duration should be in line with TR lengths, so we choose from a set of durations that are multiples of TR. In test mode, we use shorter durations to speed up the experiment.   
                mem_duration = 12.0 
                iti = self.jittered_iti(fixed_duration=mem_duration, min_iti=8, max_iti=12, TR=TR)
                durations = [mem_duration, iti]  # remember phase followed by fixation (ITI)
                phase_durs = [d*0.1 for d in durations] if self.test_mode else durations

                trial = MemoryTrial(
                    session=self,
                    phase_names=PHASES_trial,
                    phase_durations=phase_durs,
                    trial_nr=trial_nr,
                    parameters=params
                )

                block_trials.append(trial)

            self.trials_by_block.append(block_trials)

    def create_edge_trials(self):
        """Create edge trial for the session. This is a single trial with only the start_end phase, used for localizer purposes.
        
        The trial should be made once for the start and once for the end of the experiment."""

        TR = self.TR if self.TR is not None else 1.6

        self.edge_trials = []

        for trial_nr in range(2):  # Create two edge trials, one for the start and one for the end of the experiment
                
            phase_durs = [1 * TR] if self.test_mode else [10 * TR]  # Short duration in test mode, longer in actual experiment

            trial = MemoryTrial(
                session=self,
                phase_names=PHASE_edge,
                phase_durations=phase_durs,
                trial_nr=trial_nr,
                parameters={"edge_trial": True,
                            "trial_nr": 99,
                            "block": 0}  # Mark as edge trial
            )

            self.edge_trials.append(trial)

    def show_text_screen(self, text, wait_keys=None, duration=None):
        msg = visual.TextStim(
            self.win, text=text, height=28, color='black',
            font='Arial', wrapWidth=0.9 * self.win.size[0]
        )
        msg.draw()
        self.win.flip()
        event.clearEvents(eventType='keyboard')
        if duration is not None:
            core.wait(duration)
        else:
            self.win.winHandle.activate()  # ensure window has focus
            event.waitKeys(keyList=list(wait_keys or ['space']))

    def run(self):
        """Run the experimental session."""

        # Create trials
        self.create_mem_trials()
        self.create_edge_trials()

        # Tracker calibration
        if self.eyetracker_on:
            self.calibrate_eyetracker()

            # Start recording
            self.start_recording_eyetracker()

        if self.mri_on:
            self.show_text_screen(
                text="Waiting for scanner...",
                wait_keys=[self.settings['mri'].get('sync', 't')]
            )

        # start_experiment() sets session clock t=0 and logs experiment start
        self.start_experiment()

        # Run edge trial at the start of the experiment (localizer purposes)
        self.edge_trials[0].run()

        for block_trials in self.trials_by_block:

            for trial in block_trials:
                trial.run()
        
        # Run edge trial at the end of the experiment (localizer purposes)
        self.edge_trials[1].run()

        # End experiment (also stops eyetracking recording)
        self.close()

    def close(self):
        # Close base - PylinkEyeTrackerSession will download the EDF file from the EyeLink Host PC and save it in the session output directory.
        super().close()

        # Check for EDF file
        if isinstance(self, PylinkEyetrackerSession) and self.eyetracker_on:
            # Note that following filename is taken from PylinkEyetrackerSession::close() and will thus break if dependency is changed.
            edfFile = Path(self.output_dir).joinpath(self.output_str + '.edf')
            if not edfFile.exists() or not edfFile.is_file():
                logging.warning(f"Expected EyeLink EDF file {edfFile} does not exist")
                return

            hdf5Filename = edfFile.with_suffix(".hdf5")
            # Convert to HDF5
            eyeOperator = hedfpy.HDFEyeOperator(str(hdf5Filename))
            eyeOperator.add_edf_file(str(edfFile))
            eyeOperator.edf_message_data_to_hdf()
            eyeOperator.edf_gaze_data_to_hdf()
