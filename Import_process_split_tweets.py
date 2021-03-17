# -*- coding: utf-8 -*-
"""
Created on Sun Mar  7 00:06:04 2021

@author: Prabhat
"""
import pandas as pd
import numpy as np
import re
import string  

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords', quiet=True)
stop = stopwords.words('english')
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

from sklearn.model_selection import train_test_split

def import_tweets():
    '''
    read in manually-labelled tweets created for training purposes
    '''
    path = r'C:\Users\Prabhat\Documents\GitHub\Twitter-Project\Model'
    filename = r'\latest_training_data.csv'
    tweets_text_df = pd.read_csv(path + filename)
    
    process_tweets(tweets_text_df)
    
def process_tweets(tweets_text_df):
    '''
    read in manually-labelled tweets created for training purposes
    '''
    
    # convert to lowercase, remove symbols and punctuation
    tweets_text_df['text'] = tweets_text_df['text'].apply(lambda x: str.lower(x))
    tweets_text_df['text'] = tweets_text_df['text'].apply(lambda x: re.sub("(&amp?)", "", x))
    tweets_text_df['text'] = tweets_text_df['text'].apply(lambda x: re.sub("(@.*?)\s", "", x))
    tweets_text_df["text"] = tweets_text_df["text"].apply(lambda x: re.sub('[%s]' % re.escape(string.punctuation),'',x))
    
    # remove "not" from stop words (this increases accuracy of model)
    stop_words = set(stopwords.words('english')) - set(['not'])
    tweets_text_df["text"] = tweets_text_df['text'].apply(lambda x: ' '.join([word for word in x.split() if word not in stop_words]))
    
    #lemmatize cleaned tweets
    tweets_text_df["text"] = tweets_text_df["text"].apply(lambda x: ''.join(lemmatizer.lemmatize(x)))
    
    return tweets_text_df

def split_tweets():
    tweets_text_df = process_tweets() 
    x_train, x_test, y_train, y_test = train_test_split(tweets_text_df["text"], tweets_text_df["label"], test_size=0.25, random_state=1000)

    return (x_train, x_test, y_train, y_test)
