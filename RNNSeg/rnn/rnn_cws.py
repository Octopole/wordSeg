# -*- coding: utf-8 -*-

'''
python test_keras_model.py cws_info_file keras_model_file keras_model_weights_file test_data_file output_file
'''
import os.path as op
import numpy as np
import json
import h5py
import codecs
import time
import sys
import rnn.pretrain as cws
import warnings
warnings.filterwarnings("ignore")

from rnn.utils import viterbi
from sklearn import model_selection
from keras.preprocessing import sequence
from keras.optimizers import SGD, RMSprop, Adagrad
from keras.utils import np_utils
from keras.models import Sequential, model_from_json
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM, GRU, SimpleRNN
from gensim.models import Word2Vec

def loadModel(modelPath, weightPath):

    fd = open(modelPath, 'r', encoding='utf-8')
    j = fd.read()
    fd.close()

    model = model_from_json(j)
    model.load_weights(weightPath)
    return model

# 根据输入得到标注推断
def cwsSent(sent, model, cwsInfo):
    (initProb, tranProb), (vocab, indexVocab) = cwsInfo
    vec = cws.sent2vec(sent, vocab, ctxWindows = 7)
    vec = np.array(vec)
    probs = model.predict_proba(vec)
    #classes = model.predict_classes(vec)
    prob, path = viterbi.viterbi(vec, cws.corpus_tags, initProb, tranProb, probs.transpose())

    ss = ''
    for i, t in enumerate(path):
        ss += '%s/%s '%(sent[i], cws.corpus_tags[t])
    ss = []
    word = ''
    for i, t in enumerate(path):
        if cws.corpus_tags[t] == 'S':
            ss += [sent[i]]
            word = ''
        elif cws.corpus_tags[t] == 'B':
            word += sent[i]
        elif cws.corpus_tags[t] == 'E':
            word += sent[i]
            ss += [word]
            word = ''
        elif cws.corpus_tags[t] == 'M': 
            word += sent[i]
    return ss

def test_cws(test_line):
    
    cws_info_file = op.dirname(op.abspath(__file__))+"/cws.info"
    keras_model_file = op.dirname(op.abspath(__file__))+"/cws_keras_model"
    keras_model_weights_file = op.dirname(op.abspath(__file__))+"/keras_model_weights"
    cwsInfo = cws.loadCwsInfo(cws_info_file)
    start_time = time.time()
    model = loadModel(keras_model_file, keras_model_weights_file)
    out = cwsSent(test_line.strip(), model, cwsInfo)
    return out