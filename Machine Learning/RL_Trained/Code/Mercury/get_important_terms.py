'''
Run through sentiment tagged files in Mercury with different word exclusions, and record the average
decrease in probability assigned to a positive label.
'''

import pandas as pd
import numpy as np
import re
import os
import sys
import glob
from pathlib import Path

data_path = str(Path(__file__).parent / "../Data")
original_labels = pd.read_csv(f"{data_path}/full_predictions_AdamW_grains.csv")

exclusion_summary = pd.DataFrame(columns = ['Excluded_Word', 'Avg_Label_Original', 'Avg_Label_Excl', 'Avg_Pos_Diff'])
for fpath in glob.iglob(f"{data_path}/Exclusion_Tags/*.csv"):
    excl_df = pd.read_csv(fpath)
    match = re.search('predictions_(.*)_exclude.csv', fpath)
    if match:
        exclusion_word = match.group(1)
        print(f"Abstract count for excluded word {exclusion_word}: {len(excl_df)}")
        merged_df = excl_df.merge(original_labels, on="Abstract.Code")
        print(f"Matched length: {len(merged_df)}")
        assert len(merged_df) == len(excl_df)
        avg_og_label = merged_df['Prediction_y'].mean()
        avg_excl_label = merged_df['Prediction_x'].mean()
        avg_pos_diff = (merged_df['Prob_Positive_y'] - merged_df['Prob_Positive_x']).mean()
        excl_row = pd.Series({'Excluded_Word':exclusion_word, 'Avg_Label_Original':avg_og_label,
        'Avg_Label_Excl':avg_excl_label, 'Avg_Pos_Diff':avg_pos_diff})
        exclusion_summary = exclusion_summary.append(excl_row, ignore_index=True)
    else:
        raise Exception(f"{fpath} has incorrect naming convention!")

exclusion_summary = exclusion_summary.sort_values(by="Avg_Pos_Diff", ascending=False)
exclusion_summary.to_csv(f"{data_path}/exclusion_summary.csv", index=False)
