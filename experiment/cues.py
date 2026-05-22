import pandas as pd
import os

# define cues
cue1 = "School"         # far away
cue2 = "Park"           # spatial
cue3 = "Restaurant"     # emotional - negative
cue4 = "Supermarket"    # emotional - positive

# make dataframe with cues and memory type to save as tsv file
cues_df = pd.DataFrame({
    "cue": [cue1, cue2, cue3, cue4],
    "memory_type": ["far_away", "spatial", "emotional_negative", "emotional_positive"],
    "trial_nr": [1, 2, 3, 4]
})

# save as tsv file
cues_df.to_csv(os.path.join(os.path.dirname(__file__), "cues.tsv"), sep="\t", index=False)
