
import bs4 as bs
from urllib.request import Request, urlopen
import pandas as pd
import numpy as np

# careful, this is old code. it isn't optimal and will
# take a very long time
# a newer version is available in this repo
# https://github.com/nicolas-gervais/6-607-Algorithms-for-Big-Data-Analysis

website = "https://www.rottentomatoes.com"
letters = "abcdefghijklmnopqrstuwyz"

def fetch(page, addition):
    # fetches the website html data
    req = Request(page + addition, headers={'User-Agent': 'Mozilla/4.0'})
    web_page = urlopen(req).read()
    soup = bs.BeautifulSoup(web_page, 'lxml')
    return soup

def critics_letters(letter):
    # creates url for 26 pages of critics, based on the first letter of their name
    letters_url = []
    letters_url.append("/critics/authors?letter=" + letter)
    return letters_url

def critics_list(letter):
    # fetches the url of all listed critics
    critics_url = []
    for letter_pages in critics_letters(letter):
        for p in fetch(website, letter_pages).find_all("p", {"class":"critic-names"}):
            for a in p.find_all("a"):
                href_critic = a['href']
                if str(href_critic)[:7] != "/source":
                    critics_url.append(href_critic + "/movies")
    return critics_url

def movies(letter):
    # fetches the url of the movies reviewed by the critic
    movies_url = []
    for critic_profile in critics_list(letter):
        checker = fetch(website, critic_profile).find_all("h2", {"class": "panel-heading js-review-type"})
        if len(checker) > 0:
            if checker[0].text == "Movie Reviews Only":
                for td in fetch(website, critic_profile).find_all("td", 
                                {"class": "col-xs-12 col-sm-6 critic-review-table__title-column"}):
                    for a in td.find_all("a"):
                        if a['href'] not in movies_url:
                            movies_url.append(a['href'])
    return movies_url

folder_paths = []

for letter in letters:
    # makes 26 csv files from the previous function
    df = pd.DataFrame(movies(letter))
    folder_paths.append("C:/Users/Nicolas/Documents/RottenTomatoScraping/Letters/movies_" + letter + ".csv")
    df.to_csv(r"C:/Users/Nicolas/Documents/RottenTomatoScraping/Letters/movies_" + letter + ".csv", header=False)

unique_list = []

for path in folder_paths:
    # exports all unique films into a csv
    for item in pd.read_csv(path, index_col=0, header=None).values:
        if item not in unique_list:
            unique_list.append(item[0])

unique_df = pd.DataFrame(unique_list)

unique_df.to_csv(r"C:/Users/Nicolas/Documents/RottenTomatoScraping/all_movies.csv", index=False, header=None)

movies = pd.read_csv('C:/Users/Nicolas/Documents/RottenTomatoScraping/all_movies.csv', header=None)

def review_pages(k):
    # list the pages of reviews from all movies in chunks of 1000 and exports 17 csv files
    review_pages_list = []
    for movie in movies[0][(k-1)*1000:1000*k]:
        soup_2 = fetch(movie, "/reviews/?page=").find_all("span", {"class", "pageInfo"})
        if len(soup_2) >= 1:
            for n in range(1, int(soup_2[0].text[-2:]) + 1):
                review_pages_list.append(movie + "/reviews/?page=" + str(n))
    return review_pages_list

for i in range(1, 18):
    pd.DataFrame(review_pages(i)).to_csv(r"C:/Users/Nicolas/Documents/RottenTomatoScraping/Final/all_movies_and_pages_"
                                         + str(i) + ".csv", index=False, header=None)

def rating_review(number):
    # scrapes all the reviews and rating from the pages
    reviews = []
    pages = pd.read_csv('C:/Users/Nicolas/Documents/RottenTomatoScraping/Final/all_movies_and_pages_' + str(number) + '.csv', 
                        header=None)
    for page in pages[0]:
        soup_2 = fetch(page, "").find_all("div", {"class": "col-xs-16 review_container"})
        for comment in soup_2:
            comment_text = comment.find_all("div", {"class": "the_review"})[0].text
            icon = str(comment.find_all("div")[0])
            if "fresh" in icon:
                reviews.append(["fresh"] + [comment_text])
            elif "rotten" in icon:
                reviews.append(["rotten"] + [comment_text])
    return reviews

for i in range(1, 18):
    pd.DataFrame(rating_review(i)).to_csv(r"C:/Users/Nicolas/Documents/RottenTomatoScraping/reviews/reviews_"
                                         + str(i) + ".csv", index=False, header=None)

df = pd.DataFrame()

for i in range(1, 18):
    df = pd.concat([df, pd.read_csv('C:/Users/Nicolas/Documents/RottenTomatoScraping/Reviews/reviews_' +
                                    str(i) + '.csv', header=None)])

df = df.reset_index()

df['Freshness'] = df.iloc[:, 1]
df['Review'] = df.iloc[:, 2]
df = df.iloc[:, -2:]

df.to_csv(r"C:/Users/Nicolas/Documents/RottenTomatoScraping/full_dataset.csv", index=False)

df = pd.read_csv(r"C:/Users/Nicolas/Documents/RottenTomatoScraping/full_dataset.csv")

# removing empty reviews, and setting an equal number of fresh/rotten ratings

df.mask = (df['Review'].str.len() >= 18)
df = df.loc[df.mask == True]

np.random.seed(42)

rotten = df.loc[df.Freshness == 'rotten']
rotten_index = np.random.choice(rotten.index, 240000)
rotten_df = df.loc[rotten_index]

fresh = df.loc[df.Freshness == 'fresh']
fresh_index = np.random.choice(fresh.index, 240000)
fresh_df = df.loc[fresh_index]

full_df = pd.concat([fresh_df, rotten_df])

df = full_df.sample(frac=1).reset_index(drop=True)

df.to_csv(r"C:/Users/Nicolas/Documents/RottenTomatoScraping/clean_dataset.csv", index=False)