# -*- coding: utf-8 -*-
"""
Implement 10-fold CV ensemble and use average predictions

Code adapted from [this tutorial](https://mccormickml.com/2019/09/19/XLNet-fine-tuning/)

XLNet repo [here](https://github.com/zihangdai/xlnet)
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x
from sklearn.model_selection import train_test_split, KFold
from tqdm import tqdm, trange
import tensorflow as tf
import torch
import pandas as pd
import numpy as np
import time
import datetime
import random
import torch.nn.functional as F

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

#Load data and apply polarity rule
from pathlib import Path

data_path = str(Path(__file__).parent / "../Data")
mturk_abstracts = pd.read_csv(data_path + "/mturk_train.csv")

#Polarity rule: If >=2 positive ratings, then label positive
mturk_abstracts['polarity'] = (mturk_abstracts['count_pos'] >= 2).astype(int)

abstracts = mturk_abstracts['inputtext'].tolist()
labels = mturk_abstracts['polarity'].tolist()

assert len(abstracts) == len(labels)

"""We will use the large XLNet pretrained model given its superior performance on SST2 Binary Classification. http://nlpprogress.com/english/sentiment_analysis.html"""

#Load XLNet tokenizer
from transformers import XLNetTokenizer

print("Loading XLNet tokenizer...")
tokenizer = XLNetTokenizer.from_pretrained('xlnet-base-cased', do_lower_case=True)

from tensorflow.keras.preprocessing.sequence import pad_sequences
#Encode abstracts, set truncation and padding
#Sentences need to be end-padded for XLNet
def kfoldpreProcess(max_len, abstracts, labels):
    #Tokenize
    abs_tokens = [tokenizer.tokenize(ab) + ["<sep>", "<cls>"] for ab in abstracts]

    #Encode tokens
    encoded_ids = [tokenizer.convert_tokens_to_ids(x) for x in abs_tokens]
    MAX_LEN = max([len(x) for x in encoded_ids]) #Check max tokenized length
    print("Maximum id vector found: {}".format(MAX_LEN))

    #If longer than MAX_LEN ids, take first and last MAX_LEN//2
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

    # Get 10-Fold indices
    input_tensors_list = []
    kf = KFold(n_splits= 10)
    for train_ind, test_ind in kf.split(labels):
        train_inputs, validation_inputs = input_ids[train_ind], input_ids[test_ind]
        train_labels, validation_labels = np.array(labels)[train_ind], np.array(labels)[test_ind]
        train_masks, validation_masks = np.array(attention_masks)[train_ind], np.array(attention_masks)[test_ind]
        input_tensors = [train_inputs, validation_inputs, train_labels, validation_labels,
                                    train_masks, validation_masks]
        input_tensors = [torch.tensor(x) for x in input_tensors]
        input_tensors_list.append(input_tensors)

    return input_tensors_list

from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler

#Create dataloaders
def loadData(batch_size, train_inputs, validation_inputs, train_labels, validation_labels, train_masks, validation_masks):
    train_data = TensorDataset(train_inputs, train_masks, train_labels)
    train_sampler = RandomSampler(train_data)
    train_dataloader = DataLoader(train_data, sampler=train_sampler, batch_size=batch_size)

    validation_data = TensorDataset(validation_inputs, validation_masks, validation_labels)
    validation_sampler = SequentialSampler(validation_data)
    validation_dataloader = DataLoader(validation_data, sampler=validation_sampler, batch_size=batch_size)

    #Confirm positive counts
    train_pos_count = sum([int(torch.eq(x[2], 1)) for x in train_data])
    test_pos_count = sum([int(torch.eq(x[2], 1)) for x in validation_data])
    print("Training data has {} positive polarity out of {} samples".format(train_pos_count, len(train_data)))
    print("Testing data has {} positive polarity out of {} samples".format(test_pos_count, len(validation_data)))

    return train_dataloader, validation_dataloader

from transformers import XLNetForSequenceClassification, AdamW

#Load XLNet base model
def loadModel(dropout = .1, summary_dropout = .1):
    print("Loading XLNet sequence classification model...")
    model = XLNetForSequenceClassification.from_pretrained("xlnet-base-cased",
                                                          num_labels = 2,
                                                          dropout = dropout,
                                                          summary_last_dropout = summary_dropout)
    model.cuda() #Set model on GPU
    return model

#Define helper functions

#Accuracy function
def flat_accuracy(preds, labels):
    pred_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()
    return np.sum(pred_flat == labels_flat) / len(labels_flat)

def format_time(elapsed):
    '''
    Takes a time in seconds and returns a string hh:mm:ss
    '''
    # Round to the nearest second.
    elapsed_rounded = int(round((elapsed)))

    # Format as hh:mm:ss
    return str(datetime.timedelta(seconds=elapsed_rounded))

# Commented out IPython magic to ensure Python compatibility.
# %env CUDA_LAUNCH_BLOCKING="1"

from sklearn.metrics import roc_auc_score

def train(model, train_dataloader, validation_dataloader, bsize_iter):

    # Store our loss and accuracy for plotting
    train_loss_set = []
    train_acc_set = []
    test_loss_set = []
    test_acc_set = []
    loss_fail = 0
    best_dict = {"Val acc":0,"Val acc epoch":0,"Train acc":0, "Train acc epoch":0,
                "Val loss":100,"Val loss epoch":0,"Train loss":100,"Train loss epoch":0}

    # trange is a tqdm wrapper around the normal python range
    for i in trange(epochs, desc="Epoch"):

      # Training
      # Set our model to training mode (as opposed to evaluation mode)
      model.train()

      # Tracking variables
      tr_loss = 0
      tr_acc = 0
      steps = 0

      # Train the data for one epoch
      for step, batch in enumerate(train_dataloader):
        # Add batch to GPU
        batch = tuple(t.to(device) for t in batch)
        # Unpack the inputs from our dataloader
        b_input_ids, b_input_mask, b_labels = batch
        # Clear out the gradients (by default they accumulate)
        #optimizer.zero_grad()

        # Forward pass
        outputs = model(b_input_ids, token_type_ids=None, attention_mask=b_input_mask, labels=b_labels)
        loss = outputs[0]
        logits = outputs[1]

        #Compute accuracy
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()

        tmp_eval_accuracy = flat_accuracy(logits, label_ids)
        tr_acc += tmp_eval_accuracy

        # Backward pass
        loss.backward()

        # Update tracking variables
        tr_loss += loss.item()
        steps += 1

        # Update parameters and take a step using the computed gradient
        # Accumulated gradient: step and clear grad every 8 batches = 64 inputs
        if (step+1) % bsize_iter == 0:
          optimizer.step()
          scheduler1.step()
          optimizer.zero_grad()

      avg_tr_loss = tr_loss/steps
      avg_tr_acc = tr_acc/steps
      train_loss_set.append(avg_tr_loss)
      train_acc_set.append(avg_tr_acc)
      print("Train loss: {}".format(avg_tr_loss))
      print("Train accuracy: {}".format(avg_tr_acc))
      if avg_tr_acc > best_dict["Train acc"]:
          best_dict["Train acc"] = avg_tr_acc
          best_dict['Train acc epoch'] = i
      if avg_tr_loss < best_dict['Train loss']:
          best_dict["Train loss"] = avg_tr_loss
          best_dict['Train loss epoch'] = i
      # Validation

      # Put model in evaluation mode to evaluate loss on the validation set
      model.eval()

      # Tracking variables
      val_loss, val_acc = 0, 0
      val_labels = []
      val_preds = []
      steps = 0

      # Evaluate data for one epoch
      for batch in validation_dataloader:
        # Add batch to GPU
        batch = tuple(t.to(device) for t in batch)
        # Unpack the inputs from our dataloader
        b_input_ids, b_input_mask, b_labels = batch
        # Telling the model not to compute or store gradients, saving memory and speeding up validation
        with torch.no_grad():
          # Forward pass, calculate loss/logit predictions
          outputs = model(b_input_ids, token_type_ids=None, attention_mask=b_input_mask, labels=b_labels)
          loss = outputs[0]
          logits = outputs[1]

        #Save loss
        val_loss += loss.item()

        #Softmax for probabilities
        probs = F.softmax(logits, dim = 1)

        # Move logits and labels to CPU
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()
        probs = probs.detach().cpu().numpy()

        tmp_eval_accuracy = flat_accuracy(logits, label_ids)
        val_acc += tmp_eval_accuracy
        steps += 1

        #Softmax and compute AUC

      avg_val_loss = val_loss/steps
      avg_val_acc = val_acc/steps
      test_loss_set.append(avg_val_loss)
      test_acc_set.append(avg_val_acc)
      print("Validation loss: {}".format(avg_val_loss))
      print("Validation Accuracy: {}".format(avg_val_acc))
      if avg_val_acc > best_dict["Val acc"]:
          best_dict["Val acc"] = avg_val_acc
          best_dict['Val acc epoch'] = i
      if avg_val_loss < best_dict['Val loss']:
          best_dict["Val loss"] = avg_val_loss
          best_dict['Val loss epoch'] = i

      #Check early stopping condition
      #scheduler2.step(avg_val_loss)
      if avg_val_loss > avg_tr_loss:
        loss_fail += 1
      else:
        loss_fail = 0
      if loss_fail >= 5:
        print("Early stopping triggered at epoch {}".format(i))
        break

    print(best_dict)
    return train_loss_set, train_acc_set, test_loss_set, test_acc_set

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plots_path = str(Path(__file__).parent / "../Plots/XLNet_10Fold")
def plotResults(train_loss_set, train_acc_set, test_loss_set, test_acc_set):
    loss_fname = "/loss_final_fold{}.png".format(i)
    acc_fname = "/accuracy_final_fold{}.png".format(i)

    plt.plot(train_loss_set, 'r--')
    plt.plot(test_loss_set, 'b-')
    plt.legend(['Training Loss', 'Validation Loss'])
    plt.title("Loss by Epoch")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.savefig(plots_path + loss_fname)
    plt.clf()

    plt.plot(train_acc_set, 'r--')
    plt.plot(test_acc_set, 'b-')
    plt.legend(['Training Accuracy', 'Validation Accuracy'])
    plt.title("Accuracy by Epoch")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.savefig(plots_path + acc_fname)
    plt.clf()

from transformers import get_linear_schedule_with_warmup
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.optim import RMSprop

#Model Parameters
mini_bsize = 8
bsize_iter = 16
bsize = mini_bsize * bsize_iter
dropout = 0.3
summary_dropout = 0.1
learning_rate = 2e-5
layerdecay = False
eps = 1e-8
optim = "AdamW"
warmup = 0.1

#KFold Preprocess
input_tensors_list = kfoldpreProcess(128, abstracts, labels)

for i in range(len(input_tensors_list)):
    model = loadModel(dropout, summary_dropout)

    #Use gradient accumulation for batch size
    train_dataloader, validation_dataloader = loadData(mini_bsize, *input_tensors_list[i])

    #Set training parameters
    if layerdecay:
        lr_layer_decay = 0.75
        n_layers = 12
        no_lr_layer_decay_group = []
        lr_layer_decay_groups = {k:[] for k in range(n_layers)}
        for n, p in model.named_parameters():
        	name_split = n.split(".")
        	if name_split[1] == "layer":
        		lr_layer_decay_groups[int(name_split[2])].append(p)
        	else:
        		no_lr_layer_decay_group.append(p)

        optimizer_grouped_parameters = [{"params": no_lr_layer_decay_group, "lr": learning_rate}]
        for i in range(n_layers):
        	parameters_group = {"params": lr_layer_decay_groups[i], "lr": learning_rate * (lr_layer_decay ** (n_layers - i - 1))}
        	optimizer_grouped_parameters.append(parameters_group)

    else:
        param_optimizer = list(model.named_parameters())
        no_decay = ['bias', 'gamma', 'beta']
        optimizer_grouped_parameters = [
                      {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
                      'weight_decay_rate': 0.01},
                      {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
                      'weight_decay_rate': 0.0}
                  ]
    if optim == 'AdamW':
        optimizer = AdamW(optimizer_grouped_parameters,
                        lr = learning_rate,
                        eps = eps)
    if optim == 'RMSprop':
        optimizer = RMSprop(optimizer_grouped_parameters,
                            lr = learning_rate,
                            weight_decay = 0.01,
                            eps = eps)

    epochs = 65 #Solved overfitting with gradient accumulation - now implement early stopping
    total_steps = len(train_dataloader) * epochs
    n_warmup_steps = total_steps * warmup

    #Create learning rate scheduler
    scheduler1 = get_linear_schedule_with_warmup(optimizer,
                                              num_warmup_steps = n_warmup_steps,
                                              num_training_steps = total_steps)

    train_loss_set, train_acc_set, test_loss_set, test_acc_set = train(model, train_dataloader, validation_dataloader, bsize_iter)
    plotResults(train_loss_set, train_acc_set, test_loss_set, test_acc_set)

    #Evaluate final model AUC
    model.eval()
    with torch.no_grad():
      validation_inputs = input_tensors_list[i][1].to(device)
      validation_masks = input_tensors_list[i][5].to(device)
      validation_labels = input_tensors_list[i][3].to(device)

      outputs = model(validation_inputs, token_type_ids=None, attention_mask=validation_masks, labels=validation_labels)
      loss = outputs[0]
      logits = outputs[1]

      #Compute probabilities
      probs = F.softmax(logits, dim = 1)

      # Move logits and labels to CPU
      probs = probs.detach().cpu().numpy()
      logits = logits.detach().cpu().numpy()
      label_ids = validation_labels.to('cpu').numpy()
      pos_preds = probs[:,1]

      #Compute accuracy and AUC
      accuracy = flat_accuracy(probs, label_ids)
      auc = roc_auc_score(label_ids, pos_preds)
      print("Final validation accuracy: {}".format(accuracy))
      print("Final validation loss: {}".format(loss.item()))
      print("Final validation AUC: {}".format(auc))


    # Save model
    model_path = str(Path(__file__).parent / "models/Adam_KFold")
    torch.save(model.state_dict(), model_path + f"/AdamW_dp0.3_sdp0.1_bsize128_fold{i}.pt")
