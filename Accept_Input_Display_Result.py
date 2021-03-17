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

st.set_page_config(layout="wide")

def get_secret():
    '''
    code lifted from AWS Secrets Manager to securely import Twitter API credentials 
    '''
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
    '''
    chooses which page of the app to run depending on user input
    '''
    st.sidebar.title("Options for Users")
    app_mode = st.sidebar.selectbox("Choose the app mode", ["About", "How to Use", "Run Keyword Feature", "Run Twitter Handle Feature"])
    if app_mode == "About":
        about_page()

    elif app_mode == "How to Use":
        instructions_for_use()

    elif app_mode == "Run Keyword Feature":
        input_parameters_keywords()
     
    elif app_mode == "Run Twitter Handle Feature":
        input_parameters_handle()

def tweets_keywords_extract(keywords, num_of_tweets):
    '''
    extracts tweets based on keywords inputted on the app by a user
    '''
    # consumer_key and consumer_secret contain twitter API credentials
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
    '''
    extracts tweets of the handle inputted on the app by a user
    '''
    # consumer_key and consumer_secret contain twitter API credentials
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
            st.write("<font color=red>This handle does not exist</font>", unsafe_allow_html=True)
        else:
            #save most recent tweets
            alltweets.extend(new_tweets)
        
            #save the id of the oldest tweet less one
            oldest = alltweets[-1].id - 1
        
            #keep grabbing tweets until there are no tweets left to grab
            while len(new_tweets) > 0:
                print(f"getting tweets before {oldest}")
            
                #all subsequent requests use the max_id param to prevent duplicates
                new_tweets = api.user_timeline(screen_name = screen_name, count=200, max_id=oldest)
            
                #save most recent tweets
                alltweets.extend(new_tweets)
            
                #update the id of the oldest tweet less one
                oldest = alltweets[-1].id - 1
        
            #transform the tweepy tweets into a 2D array that will populate the csv 
            user_tweets = [tweet.text for tweet in alltweets]
            # c contains total number of tweets of the inputted handle
            # c also later acts as parameter to determine which function of the app to run
            c = len(user_tweets)
            filter_user_tweets(user_tweets, c)
    
    except:
        st.write("")


def filter_user_tweets(user_tweets, c):
    '''
    filters out the inputted handle's tweets not related to covid 
    '''
    #tweets not containing any of the words below will be filtered out
    keywords = ['sarscov2', 'corona', 'mask', 'masks', 'vaccine', 'vaccines', 'pfizer','moderna','astra zeneca', 'astrazeneca', 'social distancing', 'socialdistancing', 'coronavirus',
                'covid', 'covid19', 'covid-19', 'variant', 'variants', 'wuhan', 'china virus', 'china plague', 'chinavirus', 'hcq', 'hydroxychloroquine', 'shutdown', 'reopen',
                'herdimmunity', 'herd immunity', 'vaccine', 'scamdemic', 'plandemic', 'fauci', 'bill gates', 'kung flu', 'kungflu', 'quarantine', 'lockdown', 'lockdowns']

    tweets_containing_keywords = [] 
    for tweet in user_tweets:
        if any(x in tweet.lower() for x in keywords):
            tweets_containing_keywords.append(tweet)
    
    tweets_df_labels = pd.DataFrame(tweets_containing_keywords, columns = ['text'])
    
    process_tweets(tweets_df_labels, c)
    
def process_tweets(tweets_preprocessed_df, c):
    '''
    tweets processed by calling a function from the base module (Import_process_split_tweets.py)  
    '''
    import Import_process_split_tweets
    tweets_processed_df = Import_process_split_tweets.process_tweets(tweets_preprocessed_df)
    
    predict_tweets(tweets_processed_df, c)

# =============================================================================
# def process_tweets(tweets_processed_df, c):
#     '''
#     all tweets turned to lowercase, punctuation and numbers removed etc.  
#     '''
#     tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x:  re.sub(r'(pic.twitter.com.*)|(http.*?\s)|(http.*?)$|(RT\s)', "", x))
#     tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: x.encode('ascii', 'ignore').decode("utf-8"))    
#     tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: str.lower(x))
#     tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: re.sub("(&amp?)", "", x))
#     tweets_processed_df['text'] = tweets_processed_df['text'].apply(lambda x: re.sub("(@.*?)\s", "", x))
#     tweets_processed_df["text"] = tweets_processed_df["text"].apply(lambda x: re.sub('[%s]' % re.escape(string.punctuation),'',x))
# 
#     # remove "not" from stop words (helps increase model's accuracy)
#     stop_words = set(stopwords.words('english')) - set(['not'])
#     tweets_processed_df["text"] = tweets_processed_df['text'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop_words)]))
#     
#     # tweets lemmatized
#     tweets_processed_df["text"] = tweets_processed_df["text"].apply(lambda x: ''.join(lemmatizer.lemmatize(x)))
#     predict_tweets(tweets_processed_df, c)
# 
# =============================================================================
@st.cache()
def load_model():
    '''
    import model created in another module
    '''
    loaded_model = pickle.load(open('multinomialnb_model_v2.sav', 'rb'))
    return loaded_model


def predict_tweets(tweets_processed_df, c):
    '''
    import vectorizer created in another module, and predict labels of tweets
    '''
    loaded_model = load_model()
    loaded_vectorizer = pickle.load(open('count_vectorizer_v2.pickle', 'rb'))
    features = loaded_vectorizer.transform(tweets_processed_df['text'])
    # predict labels
    tweets_processed_df['label_predicted'] = loaded_model.predict(features)
    
    group_by_tweet_label(tweets_processed_df, c)

def group_by_tweet_label(tweets_processed_df, c):  
    '''
    group tweets by the two labels (conspiratorial, non-conspiratorial)
    '''
    grouped_df = tweets_processed_df.groupby(['label_predicted']).size().reset_index(name='num_of_tweets_by_type').sort_values('num_of_tweets_by_type', ascending=False)
    
    display_results(tweets_processed_df, grouped_df, c)
    

def input_parameters_keywords():
      '''
      accept user input of keywords
      '''
      keywords = st.text_input('Enter keywords (not case sensitive and # not needed)')
      num_of_tweets = st.number_input('enter number of tweets', value = 100)
      num_of_tweets = int(num_of_tweets)
    
      tweets_keywords_extract(keywords, num_of_tweets)


def input_parameters_handle():
    '''
     accept user input of twitter handle
     '''
    screen_name = st.text_input('Enter twitter handle without "@" (not case sensitive)')

    tweets_user_extract(screen_name)


def display_results(tweets_processed_df, grouped_df, c):   
    '''
     display results on the app depending on user input
     c acts as paramter to determine whether user input is handle or keyword(s)
     '''
    
    total_tweets = grouped_df['num_of_tweets_by_type'].sum()
    # if user input is keyword(s)
    if (c == 0):
        fig = px.pie(grouped_df, values='num_of_tweets_by_type', names='label_predicted')
        st.plotly_chart(fig)
        percentage_conspiratorial = round((grouped_df[grouped_df['label_predicted'] == 'conspiratorial']['num_of_tweets_by_type'][1]/total_tweets)*100,1)
        st.write("Of the latest {} tweets based on the inputted keywords {}% are conspiratorial".format(total_tweets, percentage_conspiratorial))
    
    # if user input is twitter handle
    if (c != 0):
       	st.write("Of the last {} tweets made by this handle, {} are covid-related".format(c,total_tweets))	
        if (grouped_df[grouped_df['label_predicted'] == 'conspiratorial']['num_of_tweets_by_type'].get(key = 1) > int(total_tweets/4)):
            st.info("More than a quarter of this handle's covid-related tweets are conspiratorial")
        else:
            st.info("This handle's covid-related tweets are usually non-conspiratorial")
        combined_string = ' '.join(tweets_processed_df['text'])
       	wordcloud = WordCloud().generate(combined_string)
       	fig, ax = plt.subplots()
       	plt.imshow(wordcloud, interpolation='bilinear')
       	plt.axis("off")
       	st.write ("The wordcloud below is made from the inputted handle's Covid-related tweets")
        plt.show()
       	st.pyplot(fig)
        

def about_page():
    '''
    Display messages on the app's landing page
    '''
    st.title("Navigating Covid Misinformation on Twitter")
    st.write("Hello, welcome to my app, an attempt to understand and combat Covid-related misinformation on Twitter. Given the sea of covid misinformation out there, there's a good chance you've encountered tweets that are either borderline or outright misinformation. No one can fault you for peeking at handles making these tweets to check whether they're first-time offenders or serious vectors of misinformation. But of course it's near-impossible to go through a handle's tweet history, which is where this app comes in.")
    st.write("**You can simply input the handle of concern and know whether or not it regularly tweets covid misinformation**. In addition, you can also **enter certain keywords and check to what extent they're associated with conspiratorial covid tweets.**")
    st.write("This app works by running [my project](https://github.com/KsinghP/Covid-Tweets-Classification) in the background.**")
    st.info('To understand how to use the app, navigate to the **How to Use** section from the side bar menu 👈')

    
def instructions_for_use():
    '''
    Display messages on the app's second page
    '''
    st.write("<u><font color=blue>Users can provide two inputs:</font></u>", unsafe_allow_html=True)
    st.text("")
    st.write("1.In the **Run Twitter Handle Feature** 👈, they can enter a twitter handle.")
    st.write("2.In the **Run Keyword Feature** 👈, they can enter one or more keywords from the list below and the number of tweets whose conspiratorial vs. non-conspiratorial breakup they want to see.")
    st.markdown ("<font color=blue><u>List of keywords to choose from</u></font>👇(no need to use #)", unsafe_allow_html=True)
    st.info("[sars-cov-2, sarscov2 corona, mask, vaccine, pfizer, moderna, astra zeneca, astrazeneca, social distancing, socialdistancing, coronavirus, covid, covid19, covid-19, wuhan, china virus, china plague, chinavirus, hcq, hydroxychloroquine, shutdown, herdimmunity, herd immunity, vaccine, scamdemic, plandemic, fauci, bill gates, kung flu, kungflu, quarantine, lockdown]")
    st.text("")
    st.write("<font color=blue><u>Guidelines for entering keywords</u></font>", unsafe_allow_html=True)
    st.markdown("1.To extract tweets based on at least one of multiple keywords, please separate them by **OR** (in caps). For example, *mask OR lockdown* would search for tweets with either or both of those two words.")
    st.markdown("2.To extract tweets based on multiple keywords, simply separate them by a space. For example, *social distancing* would search for tweets with both those words.")
    st.markdown("3.To exclude a keyword, use **-**. For example, *coronavirus -covid* would search for tweets with the first word but not the second.")
    
    
if __name__ == "__main__":
    main()  
