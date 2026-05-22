"""
Created on Sun Jan 4th 12:00:00 2026

@author: Ralph Wientjens

Main script to run the MTL_mem experiment.
"""
import psychopy.plugins
psychopy.plugins.activatePlugins()

import sys
import os
from session import MemorySession
from datetime import datetime

def main():
    subject = sys.argv[1]
    run =  sys.argv[2]
    # eyetracker_on = bool(sys.argv[4])
    
    output_str= "sub-" + subject+'_run-'+run
    
    output_dir = f'./logs/sub-{subject}/{output_str}'

    if len(sys.argv) < 3:
        print("Usage: python main.py <subject> <run>")
        sys.exit(1)
    
    if os.path.exists(output_dir):
        print("Warning: output directory already exists. Renaming to avoid overwriting.")
        output_dir = output_dir + datetime.now().strftime('%Y%m%d%H%M%S')
    
    settings_file='./expsettings.yml'

    ts = MemorySession(
        output_str=output_str, 
        output_dir=output_dir, 
        settings_file=settings_file,
        )
    ts.run()

if __name__ == '__main__':
    main()
