# -*- coding: utf-8 -*-
"""SciBERT_for_foodsci_sentiment_XLNetforSeqClass.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1liTqsufZQKNIfIdKuIdOkMJlxXPv-zEv

Code adapted from [this tutorial](https://mccormickml.com/2019/09/19/XLNet-fine-tuning/)

XLNet repo [here](https://github.com/zihangdai/xlnet)

Here we attempt to use XLNet-Large with 128 sequence len and HEAVY grad accumulation + checkpointing
The goal is to max out our batch size to prevent overfitting 
"""


# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x
from sklearn.model_selection import train_test_split
from pathlib import Path
from tqdm import tqdm, trange
import tensorflow as tf
import torch
import pandas as pd
import numpy as np
import time
import datetime
import random

#Import tensorflow and torch and make sure we're on a GPU

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
tokenizer = XLNetTokenizer.from_pretrained('xlnet-large-cased', do_lower_case=True)

from tensorflow.keras.preprocessing.sequence import pad_sequences
#Encode abstracts, set truncation and padding
#Sentences need to be end-padded for XLNet
def preProcess(max_len, abstracts, labels):
    abstracts = [ab + " [SEP] [CLS]" for ab in abstracts]

    #Tokenize
    abs_tokens = [tokenizer.tokenize(ab) for ab in abstracts]

    #Encode tokens
    encoded_ids = [tokenizer.convert_tokens_to_ids(x) for x in abs_tokens]
    MAX_LEN = max([len(x) for x in encoded_ids]) #Check max tokenized length
    print("Maximum id vector found: {}".format(MAX_LEN))

    #If longer than 256 ids, take first and last 128
    truncated_ids = [x[:max_len//2] + x[-max_len//2:] if len(x) > max_len else x for x in encoded_ids ]

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

    #Split out test and training sets
    train_inputs, validation_inputs, train_labels, validation_labels = train_test_split(input_ids, labels,
                                                                random_state=2020, test_size=0.1)
    train_masks, validation_masks, _, _ = train_test_split(attention_masks, input_ids,
                                                 random_state=2020, test_size=0.1)

    #Convert to tensors
    train_inputs = torch.tensor(train_inputs)
    validation_inputs = torch.tensor(validation_inputs)
    train_labels = torch.tensor(train_labels)
    validation_labels = torch.tensor(validation_labels)
    train_masks = torch.tensor(train_masks)
    validation_masks = torch.tensor(validation_masks)

    return train_inputs, validation_inputs, train_labels, validation_labels, train_masks, validation_masks

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

#Load XLNet sequence classification model
from transformers import XLNetForSequenceClassification, AdamW

def loadModel(dropout = .1, summary_dropout = .1):
    print("Loading XLNet sequence classification model...")
    model = XLNetForSequenceClassification.from_pretrained("xlnet-base-cased",
                                                          num_labels = 2,
                                                          dropout = dropout,
                                                          summary_last_dropout = summary_dropout) #Start with default dropout
    model.cuda() #Set model on GPU
    return model

from transformers import get_linear_schedule_with_warmup

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

'''!pip install GPUtil
import psutil
import humanize
import os
import GPUtil as GPU

GPUs = GPU.getGPUs()
# XXX: only one GPU on Colab and isn’t guaranteed
gpu = GPUs[0]
def printm():
    process = psutil.Process(os.getpid())
    print("Gen RAM Free: " + humanize.naturalsize(psutil.virtual_memory().available), " |     Proc size: " + humanize.naturalsize(process.memory_info().rss))
    print("GPU RAM Free: {0:.0f}MB | Used: {1:.0f}MB | Util {2:3.0f}% | Total     {3:.0f}MB".format(gpu.memoryFree, gpu.memoryUsed, gpu.memoryUtil*100, gpu.memoryTotal))
printm()'''

# Commented out IPython magic to ensure Python compatibility.
# %env CUDA_LAUNCH_BLOCKING="1"

def train(model, train_dataloader, validation_dataloader):
    # Store our loss and accuracy for plotting
    train_loss_set = []
    train_acc_set = []
    test_loss_set = []
    test_acc_set = []

    # trange is a tqdm wrapper around the normal python range
    for _ in trange(epochs, desc="Epoch"):

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
        optimizer.zero_grad()
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
        # Update parameters and take a step using the computed gradient
        optimizer.step()
        scheduler.step()

        # Update tracking variables
        tr_loss += loss.item()
        steps += 1

      avg_tr_loss = tr_loss/steps
      avg_tr_acc = tr_acc/steps
      train_loss_set.append(avg_tr_loss)
      train_acc_set.append(avg_tr_acc)
      print("Train loss: {}".format(avg_tr_loss))
      print("Train accuracy: {}".format(avg_tr_acc))

      # Validation

      # Put model in evaluation mode to evaluate loss on the validation set
      model.eval()

      # Tracking variables
      val_loss, val_acc = 0, 0
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

        # Move logits and labels to CPU
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()

        tmp_eval_accuracy = flat_accuracy(logits, label_ids)
        val_acc += tmp_eval_accuracy
        steps += 1

      avg_val_loss = val_loss/steps
      avg_val_acc = val_acc/steps
      test_loss_set.append(avg_val_loss)
      test_acc_set.append(avg_val_acc)
      print("Validation loss: {}".format(avg_val_loss))
      print("Validation Accuracy: {}".format(avg_val_acc))

    return train_loss_set, train_acc_set, test_loss_set, test_acc_set

#Plot results
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
path = str(Path(__file__).parent / "../Plots")

def plotResults(train_loss_set, train_acc_set, test_loss_set, test_acc_set):
    loss_fname = "loss_maxlen{}_dp{}_summdp{}.png".format(size, dropout, summary_dropout)
    acc_fname = "accuracy_maxlen{}_dp{}_summdp{}.png".format(size, dropout, summary_dropout)

    plt.plot(train_loss_set, 'r--')
    plt.plot(test_loss_set, 'b-')
    plt.legend(['Training Loss', 'Validation Loss'])
    plt.title("Loss by Epoch")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.savefig(path + '/' + loss_fname)
    plt.clf()

    plt.plot(train_acc_set, 'r--')
    plt.plot(test_acc_set, 'b-')
    plt.legend(['Training Accuracy', 'Validation Accuracy'])
    plt.title("Accuracy by Epoch")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.savefig(path + '/' + acc_fname)
    plt.clf()

#==============Run hyperparams loop===============

for size in [128, 256]:
    for dropout in [0, .1, .3]:
        for summary_dropout in [0, .1, .3]:
            print("Testing input ids of size {}".format(size))
            #Change max size during preprocessing
            train_inputs, validation_inputs, train_labels, validation_labels, train_masks, validation_masks = preProcess(size, abstracts, labels)

            #Mess with batch size
            train_dataloader, validation_dataloader = loadData(15, train_inputs, validation_inputs, train_labels, validation_labels, train_masks, validation_masks)

            model = loadModel(dropout, summary_dropout)

            #Set training parameters
            param_optimizer = list(model.named_parameters())
            no_decay = ['bias', 'gamma', 'beta']
            optimizer_grouped_parameters = [
                {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
                 'weight_decay_rate': 0.01},
                {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
                 'weight_decay_rate': 0.0}
            ]

            optimizer = AdamW(optimizer_grouped_parameters,
                              lr = 2e-5,
                              eps = 1e-6)

            epochs = 5 #Model typically overfits past this point
            total_steps = len(train_dataloader) * epochs

            #Create learning rate scheduler
            scheduler = get_linear_schedule_with_warmup(optimizer,
                                                        num_warmup_steps = 0,
                                                        num_training_steps = total_steps)

            train_loss_set, train_acc_set, test_loss_set, test_acc_set = train(model, train_dataloader, validation_dataloader)
            plotResults(train_loss_set, train_acc_set, test_loss_set, test_acc_set)
