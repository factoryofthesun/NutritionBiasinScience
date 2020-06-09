'''
This script loops through a list of sentiment words to exclude, and relabels the subset of the
abstracts which contain that word. The relative change in positive classification provides
a measure of how sensitive the model is to that word.
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

# Use the currently best performing model to tag abstract senetiment
from pathlib import Path
model_path = str(Path(__file__).parent / "models")
best_model_name = "/AdamW_dp0.3_sdp0.1_bsize128.pt"
model = XLNetForSequenceClassification.from_pretrained("xlnet-base-cased",
                                                      num_labels = 2,
                                                      dropout = 0.3,
                                                      summary_last_dropout = 0.1)
model.load_state_dict(torch.load(model_path + best_model_name, map_location=device))
model.cuda()
model.eval()

# Load tokenizer
tokenizer = XLNetTokenizer.from_pretrained('xlnet-base-cased', do_lower_case=True)

# Read in data
data_path = str(Path(__file__).parent / "../Data")

pos_words = []
with open(f"{data_path}/pos_words_cleaned.txt", 'r') as f:
    for line in f:
        currentline = line.split(',')
        pos_words.append(currentline[0])

print(pos_words)

abstracts_data = pd.read_csv(data_path + "/wos_indtagged_final_wide.csv")
print("Removing {} samples with no abstract data...".format(sum(abstracts_data['AB'].isna())))
abstracts_data = abstracts_data[abstracts_data['AB'].notna()] # Remove rows without abstract data
abstracts_data = abstracts_data[abstracts_data['AB'] != "AB"] # Also remove rows that duplicate the header

from tensorflow.keras.preprocessing.sequence import pad_sequences

for word in pos_words:
    abstracts_data_temp = abstracts_data[abstracts_data['AB'].str.contains(word, regex=False, case = False)]
    abstracts = abstracts_data_temp['AB'].tolist()
    abstracts = [ab.replace(word, "<mask>") for ab in abstracts]
    print("Inputs count: {}".format(len(abstracts)))
    word_stripped = word.strip()
    # Preprocess
    abs_tokens = [tokenizer.tokenize(ab) + ["<sep>", "<cls>"] for ab in abstracts]

    #Encode tokens
    encoded_ids = [tokenizer.convert_tokens_to_ids(x) for x in abs_tokens]
    MAX_LEN = max([len(x) for x in encoded_ids]) #Check max tokenized length
    print("Maximum length tokens vector found: {}".format(MAX_LEN))

    #If longer than max_len ids, take first and last MAX_LEN//2
    print("Middle-out truncating tokens to length {}".format(max_len))
    truncated_ids = [x[:max_len//2] + x[-max_len//2:] if len(x) > max_len else x for x in encoded_ids]

    for x in truncated_ids:
        if len(x) > max_len:
            print("Found inconsistent length {}".format(len(x)))
            print(x)

    #Need standardized input lengths - pad to maximum length encoded vector
    input_ids = pad_sequences(truncated_ids, maxlen = max_len, dtype = "long", truncating ="pre", padding = "post", value = 0)

    #Create attention masks
    attention_masks = []
    for seq in input_ids:
      seq_mask = [float(i>0) for i in seq]
      attention_masks.append(seq_mask)

    encodings_tensor = torch.tensor(input_ids)
    attention_masks_tensor = torch.tensor(attention_masks)


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
    # Output asbtracts, probabilities, and predictions as dataframe
    # Save abstract code for easy merging with features later
    preds_df = pd.DataFrame({"Abstract.Code": abstracts_data_temp['Abstract.Code'],"Food.Code":abstracts_data_temp['Food.Code'],
                            "Food.Name":abstracts_data_temp['Food.Name'], "Abstract": abstracts, "Prob_NotPositive": probs_nonpos_full,
                            "Prob_Positive": probs_pos_full, "Prediction": preds_full})

    preds_df.to_csv(f"{data_path}/Exclusion_Tags/predictions_{word_stripped}_exclude.csv", index = False)
