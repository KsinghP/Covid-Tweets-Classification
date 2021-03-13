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
import re
import string
import plotly.express as px
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer
count_vect = CountVectorizer()
import nltk
nltk.download('wordnet')
from nltk.corpus import stopwords
nltk.download('stopwords')
stop = stopwords.words('english')
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()


def get_secret():

    secret_name = "twitter_creds"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    return secret

def main():
    st.sidebar.title("Options for Users")
    app_mode = st.sidebar.selectbox("Choose the app mode", ["About", "How to Use", "Run keyword feature", "Run twitter handle feature"])
    if app_mode == "About":
        about_page()

    elif app_mode == "How to Use":
        instructions_for_use()

    elif app_mode == "Run keyword feature":
        input_parameters_keywords()
     
    elif app_mode == "Run twitter handle feature":
        input_parameters_handle()

def tweets_keywords_extract(keywords, num_of_tweets):
    secret_key = get_secret()
    consumer_key = secret_key[17:42]
    consumer_secret = secret_key[63:113]
    
    auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    
    if keywords:
        maxTweets = num_of_tweets
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
                    max_id = new_tweets[-1].id
                except tweepy.TweepError as e:
            # Just exit if any error
                    print("some error : " + str(e))
                    break
        tweets_preprocessed_df = pd.DataFrame(tweets, columns = ['date', 'text', 'handle', 'name', 'location', 'profile_description', 'profile_creation_date', 
                                                                 'tweets_favourited', 'num_of_tweets', 'num_of_followers', 'num_of_following'])
    
        c = 0
        process_tweets(tweets_preprocessed_df, c = 0)
    
    elif not keywords:
        st.write("")
        
def tweets_user_extract(screen_name):
    secret_key = get_secret()  	
    consumer_key = secret_key[17:42]
    consumer_secret = secret_key[63:113]
    
    auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    
    
    alltweets = []  
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    try:
        new_tweets = api.user_timeline(screen_name = screen_name, count=200)
        if not new_tweets:
            st.write("This handle does not exist")
        else:
            #save most recent tweets
            alltweets.extend(new_tweets)
        
            #save the id of the oldest tweet less one
            oldest = alltweets[-1].id - 1
        
            #keep grabbing tweets until there are no tweets left to grab
            while len(new_tweets) > 0:
                print(f"getting tweets before {oldest}")
            
                #all subsiquent requests use the max_id param to prevent duplicates
                new_tweets = api.user_timeline(screen_name = screen_name, count=200, max_id=oldest)
            
                #save most recent tweets
                alltweets.extend(new_tweets)
            
                #update the id of the oldest tweet less one
                oldest = alltweets[-1].id - 1
        
            #transform the tweepy tweets into a 2D array that will populate the csv 
            user_tweets = [tweet.text for tweet in alltweets]
        
            filter_user_tweets(user_tweets)
    
    except:
        st.write("")


def filter_user_tweets(user_tweets):
    keywords = ['sarscov2', 'corona', 'mask', 'vaccine', 'pfizer','moderna','astra zeneca', 'astrazeneca', 'social distancing', 'socialdistancing', 'coronavirus',
                'covid', 'covid19', 'covid-19', 'wuhan', 'china virus', 'china plague', 'chinavirus', 'hcq', 'hydroxychloroquine', 'shutdown', 'reopen',
                'herdimmunity', 'herd immunity', 'vaccine', 'scamdemic', 'plandemic', 'fauci', 'bill gates', 'kung flu', 'kungflu', 'quarantine', 'lockdown']

    tweets_containing_keywords = [] 
    for tweet in user_tweets:
        if any(x in tweet.lower() for x in keywords):
            tweets_containing_keywords.append(tweet)
    
    tweets_df_labels = pd.DataFrame(tweets_containing_keywords, columns = ['text'])
    
    c = 1
    total_tweets = len(user_tweets)
    process_tweets(tweets_df_labels, c)
    

def process_tweets(tweets_processed_df, c):
    tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x:  re.sub(r'(pic.twitter.com.*)|(http.*?\s)|(http.*?)$|(RT\s)', "", x))
    tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: x.encode('ascii', 'ignore').decode("utf-8"))    
    tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: str.lower(x))
    tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: re.sub("(&amp?)", "", x))
    tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: re.sub("(@.*?)\s", "", x))
    tweets_processed_df["text"] = tweets_processed_df["text"].apply(lambda x: re.sub('[%s]' % re.escape(string.punctuation),'',x))

    # remove "not" from stop words
    stop_words = set(stopwords.words('english')) - set(['not'])
    tweets_processed_df["text"] = tweets_processed_df['text'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop_words)]))
    tweets_processed_df["text"] = tweets_processed_df["text"].apply(lambda x: ''.join(lemmatizer.lemmatize(x)))
    predict_tweets(tweets_processed_df, c)

@st.cache()
def load_model():
    loaded_model = pickle.load(open('finalized_model.sav', 'rb'))
    return loaded_model

def predict_tweets(tweets_processed_df, c):
    loaded_model = load_model()
    loaded_vectorizer = pickle.load(open('vectorizer.pickle', 'rb'))
    features = loaded_vectorizer.transform(tweets_processed_df['text'])
    tweets_processed_df['label_cv'] = loaded_model.predict(features)
    
    group_by_tweet_label(tweets_processed_df, c)

def group_by_tweet_label(tweets_processed_df, c):  
    grouped_df = tweets_processed_df.groupby(['label_cv']).size().reset_index(name='num_of_tweets_by_type').sort_values('num_of_tweets_by_type', ascending=False)
    
    display_results(tweets_processed_df, grouped_df, c)
    

def input_parameters_keywords():
      keywords = st.text_input('Enter keywords')
      num_of_tweets = st.number_input('enter number of tweets', value = 100)
      num_of_tweets = int(num_of_tweets)
    
      tweets_keywords_extract(keywords, num_of_tweets)


def input_parameters_handle():
    screen_name = st.text_input('Enter twitter handle without "@"')

    tweets_user_extract(screen_name)


def display_results(tweets_processed_df, grouped_df, c):   
        
    if (c == 0):
        fig = px.pie(grouped_df, values='num_of_tweets_by_type', names='label_cv')
        st.plotly_chart(fig)
        
    if (c == 1):
        if tweets_processed_df.empty:
            st.write("This handle does not exist")
        else:   
        	total_tweets = grouped_df['num_of_tweets_by_type'].sum()
        	st.write("Of the last approx 3200 tweets, this user has made", total_tweets, "covid-related tweets")
        	category = grouped_df.loc[grouped_df['num_of_tweets_by_type'] == grouped_df['num_of_tweets_by_type'].max(), 'label_cv'].iloc[0]
        	if (category == 'non-conspiratorial'): 
            		st.info("this handle's covid-related tweets are usually non-conspiratorial")
        	elif (category == 'conspiratorial'):
            		st.info("this handle's covid-related tweets are usually conspiratorial")
        
        	combined_string = ' '.join(tweets_processed_df['text'])
        	wordcloud = WordCloud().generate(combined_string)
        	fig, ax = plt.subplots()
        	plt.imshow(wordcloud, interpolation='bilinear')
        	plt.axis("off")
        	plt.show()
        	st.pyplot(fig)
        

def about_page():
    st.title("Navigating Covid Misinformation on Twitter")
    st.write("Hello, welcome to my app, a humble attempt to understand and combat Covid-related misinformation on Twitter. Given the sea of covid misinformation out there, you might want to know which handle tweets conspiratorially about the pandemic")		
    st.write("This app runs [my project](https://github.com/KsinghP/Covid-Tweets-Classification)")
    st.markdown("Confused if a handle tweets conspiratorially about Covid? This app will tell you.")
    st.info('To know more about how it works, navigate to the "How to Use" section using the menu on the left hand side')

    
def instructions_for_use():
    st.info("Users can enter two parameters: 1. number of tweets the keywords based on which they want tweets to be collected.")
    st.markdown("To extract tweets based on one or more of multiple keywords, please separate them by OR.")
    st.markdown("To extract tweets based on multiple keywords, please separate them only by a space.")
    st.info("For example, to extract tweets based on at least one of the keywords mask, social distancing and lockdown, enter: mask OR social distancing OR lockdown")
    st.info("Similarly, to extract tweets based on all of the keywords mask, social distancing and lockdown, enter: mask social distancing lockdown")

if __name__ == "__main__":
    main()
