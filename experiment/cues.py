import pandas as pd
import os

# define cues
cue1 = "Primary School" # far away - spatial
cue2 = "Campus"         # Recent - spatial
cue3 = "Balcony"        # far away - emotional 
cue4 = "Azalea"         # Recent - positive

# make dataframe with cues and memory type to save as tsv file
cues_df = pd.DataFrame({
    "cue": [cue1, cue2, cue3, cue4],
    "memory_type": ["distant - spatial", "recent - spatial", "distant - emotional", "recent - emotional"],
    "trial_nr": [1, 2, 3, 4]
})

# save as tsv file
cues_df.to_csv(os.path.join(os.path.dirname(__file__), "cues.tsv"), sep="\t", index=False)
