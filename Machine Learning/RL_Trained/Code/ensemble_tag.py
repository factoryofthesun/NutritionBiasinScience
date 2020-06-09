'''
Check performance of ensemble model using average or majority voting.
'''

import pandas as pd
import torch
import torch.nn.functional as F
import numpy as np
from transformers import XLNetForSequenceClassification
from transformers import XLNetTokenizer
from nlp_data_prep import preProcess, createDataLoader
import time
import datetime
from pathlib import Path

# If there's a GPU available...
if torch.cuda.is_available():

    # Tell PyTorch to use the GPU.
    device = torch.device("cuda")

    print('There are %d GPU(s) available.' % torch.cuda.device_count())

    print('We will use the GPU:', torch.cuda.get_device_name(0))

# If not...
else:
    print('No GPU available, using the CPU instead.')
    device = torch.device("cpu")

# Preprocessing parameters
max_len = 128

# Load tokenizer
tokenizer = XLNetTokenizer.from_pretrained('xlnet-base-cased', do_lower_case=True)

# Read in data
data_path = str(Path(__file__).parent / "../Data")

abstracts_data = pd.read_csv(data_path + "/wos_indtagged_final_wide.csv")
print("Removing {} samples with no abstract data...".format(sum(abstracts_data['AB'].isna())))
abstracts_data = abstracts_data[abstracts_data['AB'].notna()] # Remove rows without abstract data
abstracts_data = abstracts_data[abstracts_data['AB'] != "AB"] # Also remove rows that duplicate the header

print("Original abstracts count:", len(abstracts_data['AB']))
# Remove abstracts that have already been MTurk labelled
labelled_df = pd.read_csv(f"{data_path}/labelled_with_codes.csv")

print("Abstracts to remove:", len(labelled_df))

# Keep labelled samples to append later
labelled_df['Prob_NotPositive'] = (labelled_df['Prediction'] == 0).astype(int)
labelled_df['Prob_Positive'] = (labelled_df['Prediction'] == 1).astype(int)

abstracts_data = abstracts_data[~abstracts_data['Abstract.Code'].isin(labelled_df['Abstract.Code'].tolist())]

abstracts = abstracts_data['AB'].tolist()
print("Final inputs count: {}".format(len(abstracts)))

# Preprocess
encodings_tensor, attention_masks_tensor = preProcess(max_len, tokenizer, abstracts)

# Loop through all 10 KFold models
from pathlib import Path
model_path = str(Path(__file__).parent / "models/Adam_KFold")

pred_dfs = []
for i in range(10):
    best_model_name = "/grains_original_AdamW_dp0.3_sdp0.1_bsize128.pt"
    model = XLNetForSequenceClassification.from_pretrained("xlnet-base-cased",
                                                          num_labels = 2,
                                                          dropout = 0.3,
                                                          summary_last_dropout = 0.1)
    model.load_state_dict(torch.load(model_path + best_model_name, map_location=device))
    model.cuda()
    model.eval()


    # ==== Conduct Inference ====
    # Time inference
    t0 = time.time()

    # Predict in batches
    dataloader = createDataLoader(200, encodings_tensor, attention_masks_tensor)

    probs_nonpos_full = []
    probs_pos_full = []
    preds_full = []
    for step, batch in enumerate(dataloader):
        print("Predicting on batch {}...".format(step))
        batch = tuple(t.to(device) for t in batch)
        b_inputs, b_masks = batch

        with torch.no_grad():
            outputs = model(b_inputs, token_type_ids=None, attention_mask=b_masks)
            logits = outputs[0]
            probs = F.softmax(logits, dim=1)
            probs = probs.detach().cpu().numpy()
            preds = np.argmax(probs, axis =1).flatten()
            try:
                probs_nonpos_full.extend(probs[:,0])
                probs_pos_full.extend(probs[:,1])
                preds_full.extend(preds)
            except:
                print("BROKE")
                print("Probs:", probs)
                print("Preds:",preds)

    print("Total inference took " + str(datetime.timedelta(seconds=int(round(time.time()-t0)))))

    # Output abstracts, probabilities, and predictions as dataframe

    # Save abstract code for easy merging with features later
    preds_df = pd.DataFrame({"Abstract.Code": abstracts_data['Abstract.Code'],"Food.Code":abstracts_data['Food.Code'],
                            "Food.Name":abstracts_data['Food.Name'], "Abstract": abstracts, "Prob_NotPositive": probs_nonpos_full,
                            "Prob_Positive": probs_pos_full, "Prediction": preds_full})

    # Add back in sampled labels
    preds_df = pd.concat([preds_df, labelled_df], ignore_index=True)

    preds_df.to_csv(data_path + "/KFold_Preds/full_predictions_AdamW_grains.csv", index = False)
