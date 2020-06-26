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
labelled_df = pd.read_csv(f"{data_path}/labelled_with_codes.csv").sort_values(by=['Abstract.Code'])

print("Abstracts to remove:", len(labelled_df))

training_abs = labelled_df['Abstract'].tolist()
training_labs = labelled_df['Prediction'].tolist()

# Keep labelled samples to append later
labelled_df['Prob_NotPositive'] = (labelled_df['Prediction'] == 0).astype(int)
labelled_df['Prob_Positive'] = (labelled_df['Prediction'] == 1).astype(int)

abstracts_data = abstracts_data[~abstracts_data['Abstract.Code'].isin(labelled_df['Abstract.Code'].tolist())]

abstracts = abstracts_data['AB'].tolist()
print("Final inputs count: {}".format(len(abstracts)))

# Preprocess
encodings_tensor, attention_masks_tensor = preProcess(max_len, tokenizer, abstracts)
encodings_train, attention_train = preProcess(max_len, tokenizer, training_abs)

# Loop through all 10 KFold models
from pathlib import Path
model_path = str(Path(__file__).parent / "models/Adam_KFold")

train_df_list = []
preds_df_list = []
for i in range(10):
    print(f"Running tagging with model {i}")
    best_model_name = f"/AdamW_dp0.3_sdp0.1_bsize128_fold{i}.pt"
    model = XLNetForSequenceClassification.from_pretrained("xlnet-base-cased",
                                                          num_labels = 2,
                                                          dropout = 0.3,
                                                          summary_last_dropout = 0.1)
    model.load_state_dict(torch.load(model_path + best_model_name, map_location=device))
    model.cuda()
    model.eval()

    # ======== PREDICT ON TRAINING DATA ===========
    dataloader = createDataLoader(200, encodings_train, attention_train)
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

    train_df = pd.DataFrame({"Abstract.Code": labelled_df['Abstract.Code'],"Food.Code":labelled_df['Food.Code'],
                            "Food.Name":labelled_df['Food.Name'], "Abstract": training_abs, "Prob_NotPositive": probs_nonpos_full,
                            "Prob_Positive": probs_pos_full, "Prediction": preds_full})
    train_df_list.append(train_df)

    # ======== PREDICT ON FULL SAMPLE ===========
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

    preds_df_list.append(preds_df)

    #preds_df.to_csv(data_path + f"/KFold_Preds/AdamW_grains_preds{i}.csv", index = False)

# Evaluate
train_df_full = pd.concat(train_df_list)
grouped_train = train_df_full.groupby(['Abstract.Code']).agg(Committee_Vote = ('Prediction', 'mean'),
                                                            Committee_Avg = ('Prob_Positive', 'mean')).reset_index().sort_values(by=['Abstract.Code'])
grouped_train['Label'] = training_labs
grouped_train['Committee_Vote_Pred'] = grouped_train['Committee_Vote'].round() # 0.5 rounds down
grouped_train['Committee_Avg_Pred'] = grouped_train['Committee_Avg'].round() # 0.5 rounds down

# Compute accuracy
vote_acc = (grouped_train['Committee_Vote_Pred'] == grouped_train['Label']).astype(int).mean()
avg_acc = (grouped_train['Committee_Avg_Pred'] == grouped_train['Label']).astype(int).mean()

print(f"Committee vote accuracy: {vote_acc}, Committee average confidence accuracy: {avg_acc}")

# Save full predictions
preds_df_full = pd.concat(preds_df_list)
preds_df_grouped = preds_df_full.groupby(['Abstract.Code', 'Abstract', 'Food.Code', 'Food.Name']).agg(Committee_Vote_Pred = pd.NamedAgg(column = 'Prediction', aggfunc=lambda x: x.mean().round()),
                                                                Committee_Avg_Pred = pd.NamedAgg(column='Prob_Positive',aggfunc=lambda x: x.mean().round())).\
                                                                reset_index()
preds_df_grouped['MTurk'] = 0
labelled_df['Committee_Vote_Pred'], labelled_df['Committee_Avg_Pred'] = labelled_df['Prediction'], labelled_df['Prediction']
labelled_df['MTurk'] = 1

preds_df_final = pd.concat([preds_df_grouped, labelled_df[['Abstract.Code', 'Abstract', 'Food.Code', 'Food.Name',
                                                        'Committee_Vote_Pred', 'Committee_Avg_Pred', 'MTurk']]]).sort_values(by='Abstract.Code')
preds_df_final.to_csv(data_path + "/AdamW_grains_preds_ensemble.csv", index=False)
