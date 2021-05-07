# -*- coding: utf-8 -*-
"""
Created on Fri May  7 03:57:07 2021
@author: Prabhat
"""
import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import boto3
import time


#Variables that contains the user credentials to access Twitter API
consumer_key = '8cK5vc4B4mgGbAhAihlFHwluO'
consumer_secret ='WMqOdc6R74KL5Jo5FaDXRiXx02V3vTYIZUiD0y6EbSGxnu8WwN'
access_token = '976708394370310144-xLkTTjTzYueNg8sHZ6kpXIHyfyC6lQx'
access_token_secret = 'Am8UL5jOWmLyFBIN9P88Vhua3TvhUB9tcp9guzaB6yOQQ'

class StdOutListener(StreamListener):

    def on_data(self, data):
        tweet = json.loads(data)
        print ('ok1')
        try:
            if 'extended_tweet' in tweet.keys():
                print ('ok2')
                message_lst = [str(tweet['id']),
                       str(tweet['user']['name']),
                       str(tweet['user']['screen_name']),
                       tweet['extended_tweet']['full_text'],
                       str(tweet['user']['followers_count']),
                       str(tweet['user']['location']),
                       str(tweet['geo']),
                       str(tweet['created_at']),
                       '\n'
                       ]
                message = '\t'.join(message_lst)
                print ('ok3')
                print(message)
                client.put_record(
                    DeliveryStreamName=delivery_stream,
                    Record={
                    'Data': message
                    }
                )
            elif 'text' in tweet.keys():
                #print (tweet['text'])
                message_lst = [str(tweet['id']),
                       str(tweet['user']['name']),
                       str(tweet['user']['screen_name']),
                       tweet['text'].replace('\n',' ').replace('\r',' '),
                       str(tweet['user']['followers_count']),
                       str(tweet['user']['location']),
                       str(tweet['geo']),
                       str(tweet['created_at']),
                       '\n'
                       ]
                message = '\t'.join(message_lst)
                print ('ok4')
                print(message)
                client.put_record(
                    DeliveryStreamName=delivery_stream,
                    Record={
                    'Data': message
                    }
                )
        except (AttributeError, Exception) as e:
                print ('ok5')
                print (e)
        return True

    def on_error(self, status):
        print ('ok6')
        print (status)
        
if __name__ == '__main__':

    #This handles Twitter authetification and the connection to Twitter Streaming API
    listener = StdOutListener()
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    #tweets = Table('tweets_ft',connection=conn)
    client = boto3.client('firehose', 
                          region_name='us-east-2',
                          aws_access_key_id='AKIAX64DZMOZHSTPCYUF',
                          aws_secret_access_key='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', 
                          endpoint_url='https://kinesis.us-east-2.amazonaws.com/')

    delivery_stream = 'covid-help-tweets'
    #This line filter Twitter Streams to capture data by the keywords: 'python', 'javascript', 'ruby'
    #stream.filter(track=['trump'], stall_warnings=True)
    while True:
        try:
            print('Twitter streaming...')
            stream = Stream(auth, listener)
            stream.filter(track=['covid'], languages=['en'], stall_warnings=True)
        except Exception as e:
            print(e)
            print('Disconnected...')
            time.sleep(5)
            continue  
