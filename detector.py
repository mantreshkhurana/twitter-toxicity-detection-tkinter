# Author: Mantresh Khurana

import os
import pickle
import tkinter as tk
from tkinter import Menu, PhotoImage, ttk
from tkinter import messagebox
import webbrowser
import tweepy
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from dotenv import load_dotenv
import urllib.request

# check if the internet is available
try:
    urllib.request.urlopen('http://www.google.com')
    pass
except:
    messagebox.showerror("Error", "Internet connection not available.")
    exit()

# load the .env file if it exists
if os.path.exists(".env"):
    load_dotenv()
else:
    messagebox.showerror(
        "Error", "Please create a .env file with the required environment variables, check .env.example for more info")
    exit()

# --------------APIs & auth--------------- # DO NOT UNCOMMENT THIS SECTION
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
# --------------APIs & auth END--------------- # DO NOT UNCOMMENT THIS SECTION

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication Working.")
except:
    messagebox.showerror(
        "Error", "Error during authentication, check your .env file.")
    exit()

# load the data into a pandas dataframe, ***YOU CAN USE YOUR OWN DATASET HERE, REMEMBER TO CHANGE THE COLUMN NAMES IN X & Y VARIABLES***
df = pd.read_csv('datasets/hate_speech.csv')

# split the data into feature and target variables
x = df['text']
y = df['is_toxic']

# convert the text data into numerical vectors using a CountVectorizer
vectorizer = CountVectorizer()
x = vectorizer.fit_transform(x)

# split the data into training and testing sets
x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42)

# train a logistic regression model on the training data
model = LogisticRegression()
model.fit(x_train, y_train)

# use the model to make predictions on the test data
predictions = model.predict(x_test)

# calculate the accuracy of the model by comparing the predicted labels to the true labels
accuracy = sum(predictions == y_test) / len(y_test)
print("Model Accuracy(from datasets/hate_speech.csv):", accuracy * 100, "%\n")

# function to search for tweets
def search_tweets():
    # get the username from the entry widget
    username = username_entry.get()

    # get the number of tweets to retrieve
    count = int(count_entry.get())

    # retrieve the tweets using the API object
    tweets = api.user_timeline(screen_name=username, count=count)

    # clear any existing tweet widgets
    for widget in tweet_frame.winfo_children():
        widget.destroy()

    # create a canvas widget to hold the tweet frame and scrollbar
    canvas = tk.Canvas(tweet_frame)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(
        tweet_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.config(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>", lambda event: canvas.configure(
        scrollregion=canvas.bbox("all")))
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(
        int(-1 * (event.delta / 120)), "units"))

    # create a frame inside the canvas to hold the tweets
    canvas_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=canvas_frame, anchor="nw")
    canvas_frame.columnconfigure(0, weight=1)

    # create a widget for each tweet
    for tweet in tweets:
        tweet_widget = ttk.Frame(canvas_frame, padding=10, relief="groove")
        tweet_widget.grid(sticky="ew", pady=10)
        tweet_widget.columnconfigure(1, weight=1)
        user_label = ttk.Label(
            tweet_widget, text=f"{tweet.user.name} (@{tweet.user.screen_name})")
        user_label.grid(row=0, column=0, sticky="w")
        text_label = ttk.Label(tweet_widget, text=tweet.text,
                               wraplength=400, justify="left")
        text_label.grid(row=1, column=0, columnspan=2, sticky="w")
        created_label = ttk.Label(
            tweet_widget, text=tweet.created_at.strftime("%B %d, %Y at %I:%M %p"))
        created_label.grid(row=2, column=0, sticky="w")

        if tweet.favorite_count >= 1000000000:
            favorite_label = ttk.Label(
                tweet_widget, text=f"❤ {round((tweet.favorite_count/1000000000), 1)}B")
        elif tweet.favorite_count >= 1000000:
            favorite_label = ttk.Label(
                tweet_widget, text=f"❤ {round((tweet.favorite_count/1000000), 1)}M")
        elif tweet.favorite_count >= 1000:
            favorite_label = ttk.Label(
                tweet_widget, text=f"❤ {round((tweet.favorite_count/1000), 1)}K")
        else:
            favorite_label = ttk.Label(
                tweet_widget, text=f"❤ {tweet.favorite_count}")
        favorite_label.grid(row=2, column=1, sticky="e")

        retweet_label = ttk.Label(
            tweet_widget, text=f"♺ {tweet.retweet_count}")
        retweet_label.grid(row=2, column=1, sticky="w")

        # check if the tweet is toxic
        tweet_text = tweet.text
        tweet_text = vectorizer.transform([tweet_text])

        percentage = round((model.predict_proba(tweet_text)[0][1] * 100), 2)

        if percentage >= 65.00:
            print(f"Toxicity: {percentage}%")
            text_label.config(foreground="red")
            percentage_label = ttk.Label(
                tweet_widget, text=f"{percentage}% Toxic", foreground="red", font="bold")
            percentage_label.grid(row=3, column=0, sticky="w")
        else:
            print(f"Toxicity: {percentage}%")
            text_label.config(foreground="green")
            percentage_label = ttk.Label(
                tweet_widget, text=f"{percentage}% Toxic", foreground="green", font="bold")
            percentage_label.grid(row=3, column=0, sticky="w")

    # save the model
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)

    # update the canvas to reflect the changes
    canvas_frame.update_idletasks()
    canvas.config(scrollregion=canvas_frame.bbox("all"))

root = tk.Tk()
root.geometry("490x700")
root.resizable(False, False)
app_icon = PhotoImage(file='images/logo.png')
root.iconphoto(False, app_icon)
root.title(
    "Twitter Toxicity Detector - Accuracy {:.2f}%\n".format(accuracy * 100))

menubar = Menu(root)
root.config(menu=menubar)
file_menu = Menu(menubar, tearoff=False)
help_menu = Menu(menubar, tearoff=False)

# file menu item
menubar.add_cascade(
    label="File",
    menu=file_menu,
    underline=0
)

file_menu.add_command(
    label='Exit',
    command=root.destroy,
)

# help menu item
menubar.add_cascade(
    label="About",
    menu=help_menu
)
help_menu.add_command(
    label='Visit Website',
    command=lambda: webbrowser.open('https://www.mantreshkhurana.com'),
)
help_menu.add_separator()
help_menu.add_command(
    label='Source Code',
    command=lambda: webbrowser.open('https://github.com/mantreshkhurana/twitter-toxicity-detection-python'),
)
help_menu.add_command(
    label='View License',
    command=lambda: webbrowser.open(
        'https://github.com/mantreshkhurana/twitter-toxicity-detection-python/blob/stable/LICENSE'),
)

search_frame = ttk.Frame(root, padding=10)
search_frame.pack(fill="x")
search_frame.columnconfigure(0, weight=1)

username_label = ttk.Label(search_frame, text="Username:")
username_label.grid(row=0, column=0, sticky="w")

username_entry = ttk.Entry(search_frame)
username_entry.grid(row=0, column=1, sticky="ew")
username_entry.focus()

author_label = ttk.Label(search_frame, text="This project was created by Mantresh Khurana", foreground="grey")
author_label.grid(row=2, column=0, columnspan=5, sticky="w", pady=5, padx=90)
author_label.configure(anchor="center")

post_label = ttk.Label(search_frame, text="Posts:")
post_label.grid(row=0, column=2, sticky="w")

count_entry = ttk.Entry(search_frame, width=5)
count_entry.grid(row=0, column=3, sticky="w")
count_entry.insert(0, "10")

search_button = ttk.Button(search_frame, text="Search", command=search_tweets)
search_button.grid(row=0, column=4, sticky="e")

# accuracy_label = ttk.Label(search_frame, text="Model Accuracy: {:.2f}%\n".format(accuracy * 100))
# accuracy_label.grid(row=1, column=0, columnspan=3, sticky="we")

tweet_frame = ttk.Frame(root, padding=10)
tweet_frame.pack(fill="both", expand=True)

root.mainloop()
