# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 21:19:40 2020

@author: Prabhat
"""
import boto3
import base64
from botocore.exceptions import ClientError
import streamlit as st
import tweepy
import json
import sys
import jsonpickle
import os
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from nltk.corpus import stopwords
import re
import string
stop = stopwords.words('english')
import nltk

from sklearn.feature_extraction.text import CountVectorizer
count_vect = CountVectorizer()

#os.chdir(r'C:\Users\Prabhat')

def main():
    st.sidebar.title("Options for Users")
    app_mode = st.sidebar.selectbox("Choose the app mode", ["About", "How to Use", "Run the App"])
    if app_mode == "About":
        about_page()

    elif app_mode == "How to Use":
        instructions_for_use()

    elif app_mode == "Run the App":
        input_parameters()
        
def tweets_API_extract(keywords, num_of_tweets):
    with open('creds.json') as creds:
        credentials = json.load(creds)
    
    auth = tweepy.AppAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
    #auth.set_access_token(access_token_key, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    if (not api):
            print ("Can't Authenticate")
            sys.exit(-1)

    maxTweets = num_of_tweets # Some arbitrary large number
    tweetsPerQry = 100

    fName = 'tweets_trial_csv.txt'

    sinceId = None
    tweets = []

    max_id = -1
    tweetCount = 0

    with open(fName, 'w') as f:
            while tweetCount < maxTweets:
                try:
                    if (max_id <= 0):
                        if (not sinceId):
                            new_tweets = api.search(q= keywords + ' -filter:retweets', count=tweetsPerQry, lang='en', include_retweets=False, tweet_mode='extended')
                        else:
                            new_tweets = api.search(q=keywords + ' -filter:retweets', count=tweetsPerQry,
                                            since_id=sinceId, lang='en', include_retweets=False, tweet_mode='extended')
                    else:
                        if (not sinceId):
                            new_tweets = api.search(q=keywords + ' -filter:retweets', count=tweetsPerQry,lang='en',
                                            max_id=str(max_id - 1), include_retweets=False, tweet_mode='extended')
                        else:
                            new_tweets = api.search(q=keywords + ' -filter:retweets', count=tweetsPerQry,
                                            max_id=str(max_id - 1),
                                            since_id=sinceId, lang='en', include_retweets=False, tweet_mode='extended')
                    if not new_tweets:
                        print("No more tweets found")
                        break
            
                    for tweet in new_tweets:
                        f.write(jsonpickle.encode(tweet._json, unpicklable=False) +
                        '\n')

                        tweets.append([tweet._json['created_at'], tweet._json['full_text'], tweet._json['user']['screen_name'], 
                                tweet._json['user']['name'], tweet._json['user']['location'], tweet._json['user']['description'], 
                                tweet._json['user']['created_at'], tweet._json['user']['favourites_count'], 
                                tweet._json['user']['statuses_count'], tweet._json['user']['followers_count'], tweet._json['user']['friends_count']])
                
                        json_str = tweet._json

                    tweetCount += len(new_tweets)
                    #print("Downloaded {0} tweets".format(tweetCount))
                    max_id = new_tweets[-1].id
                except tweepy.TweepError as e:
            # Just exit if any error
                    print("some error : " + str(e))
                    break
    tweets_preprocessed_df = pd.DataFrame(tweets, columns = ['date', 'text', 'handle', 'name', 'location', 'profile_description', 'profile_creation_date', 'tweets_favourited', 'num_of_tweets', 'num_of_followers', 'num_of_following'])
    
    process_tweets(tweets_preprocessed_df)

def process_tweets(tweets_processed_df):    
    tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: str.lower(x))
    tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: re.sub("(&amp?)", "", x))
    tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: re.sub("(@.*?)\s", "", x))
    tweets_processed_df["text"] = tweets_processed_df["text"].apply(lambda x: re.sub('[%s]' % re.escape(string.punctuation),'',x))

    # remove "not" from stop words
    stop_words = set(stopwords.words('english')) - set(['not'])
    tweets_processed_df["text"] = tweets_processed_df['text'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop)]))
    # tweets_processed_df["text"] = tweets_processed_df["text"].apply(lambda x: ' '.join(lemmatize_sentence(x)))
    
    predict_tweets(tweets_processed_df)

@st.cache()
def load_model():
    loaded_model = pickle.load(open('finalized_model.sav', 'rb'))
    return loaded_model

def predict_tweets(tweets_processed_df):
    loaded_model = load_model()
    loaded_vectorizer = pickle.load(open('vectorizer.pickle', 'rb'))
    features_x = loaded_vectorizer.transform(tweets_processed_df['text'])
    tweets_processed_df['label_cv'] = loaded_model.predict(features_x)
    # tweets_processed_df['label_tfidf'] = loaded_model.predict(features_done_x)
    group_by_tweet_label(tweets_processed_df)

def group_by_tweet_label(tweets_processed_df):    
    grouped_df = tweets_processed_df.groupby(['label_cv']).size().reset_index(name='num_of_tweets_by_type').sort_values('num_of_tweets_by_type', ascending=False)
    
    st.write(tweets_processed_df.head())
    st.bar_chart(grouped_df['num_of_tweets_by_type'])


def input_parameters():
      keywords = st.text_input('Enter keywords')
      num_of_tweets = st.number_input('enter number of tweets', value = 100)
      num_of_tweets = int(num_of_tweets)
    
      tweets_API_extract(keywords, num_of_tweets)

def display_results(tweets_processed_df, grouped_df):   
    st.write(tweets_processed_df.head())
    st.bar_chart(grouped_df['num_of_tweets_by_type'])    

def about_page():
    st.title("What Does Twitter Say About Covid-19?")
    st.markdown("<b>Misinformation</b> has surged in light of the outbreak of Covid-19, and Twitter has been a major global medium for it.", unsafe_allow_html=True)
    st.markdown("This app is an <i>attempt to analyse</i> covid-related misinformation circulating on Twitter.", unsafe_allow_html=True)
    st.info("This app collect covid-related tweets, and classifies them as either scientific or conspiratorial.")
    

def instructions_for_use():
    st.info("Users can enter two parameters: 1. number of tweets the keywords based on which they want tweets to be collected.")
    st.markdown("To extract tweets based on one or more of multiple keywords, please separate them by OR.")
    st.markdown("To extract tweets based on multiple keywords together, please separate them only by a space.")
    st.info("For example, to extract tweets based on at least one of the keywords mask, social distancing and lockdown, enter: mask OR social distancing OR lockdown")
    st.info("Similarly, to extract tweets based on all of the keywords mask, social distancing and lockdown, enter: mask social distancing lockdown")

if __name__ == "__main__":
    main()
