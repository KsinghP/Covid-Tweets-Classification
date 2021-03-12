## How to Use

This project is my attempt to enable users to understand and navigate the problem of Covid-related misinformation on Twitter. It works by accepting user inputs on a web app (http://). There are two inputs that users can give:

1. Covid-related keyword(s) and number of tweets: users can input one or more keywords (list provided on the “How to use” page of the app) and a certain number of tweets. The app will work on the backend to pull the same number of latest tweets based on the provided keywords, and inform users of the percentage breakup of conspiratorial and non-conspiratorial tweets. 

2. Twitter handle: users can input a handle to check whether its Covid-related tweets are conspiratorial or non-conspiratorial. On the backend, the app achieves this by pulling in 3200 of the given handle’s latest tweets related to Covid - tweets are filtered by keywords to select Covid-related ones, and the number might be less than 3200 depending on how many such tweets can be found – and analysing them to see how many of those are conspiratorial. If the proportion is > 25%, the handle is reported as tweeting conspiratorially about Covid. Users can also see a wordcloud of the given handle’s covid-related tweets.

## Demo



## What does a “conspiratorial” tweet mean?

In order to better appreciate the information provided by the app, it’s important to understand that I have labelled a tweet “conspiratorial” only if it explicitly promotes Covid-related misinformation, and not if it simply uses language – for example, using “China virus” to describe the coronavirus – that has come to be associated with misinformation. The examples below should throw more light.

<ins>Conspiratorial tweets</ins>
1. The United States graduated with chemical weapons, it leaked the virus and could not hide its mistakes. the virus threatened the United States itself only then did the virus spread to china and drag china into the water so that Americans would not be condemned by the world
2. Our savior Trump was cheated out of billions of votes by the radical socialist left who planned the corona virus with china. So much proof suppressed by fake news media. Trump is the one true beacon of truth and decency. All votes against my president is fraud. MAGA for life

<ins>Non-conspiratorial tweets</ins>
1. All this suffering if only China didnt lie about what was happening in Wuhan where the virus started
2. 

# Limitations and scope for improvement

I think the source of most, if not all, limitations in my model is the small size of training data (~500 tweets). Despite this, however, my model achieves a respectable 77% accuracy on the test set (~160 tweets). As the recall and precision metrics suggest, the non-conspiratorial label is predicted with greater accuracy than the conspiratorial one. 

Another limitation is the model’s strong dependence on keywords. For instance, the presence of “scamdemic” in a tweet almost ensures its prediciton as conspiratorial (because in the training set almost all tweets associated with this word are conspiratorial), even if reading the whole tweet – “covid is not a scamdemic”, for example – would suggest that that isn’t the case. This is also likely due to limited training data.

The model also fails to catch more subtle misinformation which involves a shrewd manipulation of statistics. An example would be this tweet (I'm referring to the tweet by @MLevitt_NP2013): https://twitter.com/CT_Bergstrom/status/1357998390680821764

The Keras deep learning model I’ve used returns slightly lower accuracy than the standard machine learning models - which eventually led me to choose one of those to output results to the app - perhaps again due to not enough training data.

In order to improve the accuracy and mitigate other problems, I’m working on preparing a much bigger training set.

## Technologies Used

Python 3.6 (pandas, nltk, sklearn, plotly, streamlit and others)
AWS (EC2, S3, Secrets Manager, Route 53)

