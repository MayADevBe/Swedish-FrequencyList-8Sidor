import requests
from bs4 import BeautifulSoup
import time
import json

# amount of articles and content in one file (JSON format)
ARTICLES_PER_FILE = 50
KATEGORIES = ["sverige", "varlden", "sport", "kultur", "vardags", "kronika"]
# words, that should not be counted in freq list
REMOVE = ["sidor", "ttdela", "sidordela", "r", "tt", "rolling", "s", "d", "a", "t", "p4", "ttgå", "wake", "up", "tmz", "sidors", "hbtqidela", 
        "play8", "em", "c", "v", "eu", "svt", "nhl", "nhls", "gt", "sdhl", "www", "b", "k2", "k1", "aiks", "ap", "shl", "g", "sofia", "xi"]

"""
Data Mining Part
"""
# sleep time after every request to the website
SLEEP_TIME = 20

# go through category website + pagination to get all links to articles
def extract_article_links(kategory, startpage = 1, endpage = 100 ):
    # start websites

    #websites = ["https://8sidor.se/kategori/sverige/page/", "https://8sidor.se/kategori/varlden/page/", "https://8sidor.se/kategori/sport/page/", "https://8sidor.se/kategori/kultur/page/", "https://8sidor.se/kategori/vardags/page/", "https://8sidor.se/kategori/kronika/page/"]

    website = "https://8sidor.se/kategori/" + kategory + "/page/"
    
    # request website
    print("Looking at website: " + website)
    pagination_done = False
    i = startpage
    article_links = []
    # go through pagination
    while pagination_done == False and i<=endpage:
        print("Getting Links from Page: " + str(i))
        r = requests.get(website + str(i) + "/")
        data = r.text
        soup = BeautifulSoup(data, 'html.parser')

        # check if valid site
        h2_first = soup.find("h2").text
        if h2_first == "Sidan kunde inte hittas":
            pagination_done = True

        # get articles on website
        articles = soup.find_all("article", class_="article")

        # extract links for actual articles
        for article in articles:
            link = article.find("h2").find("a")['href']
            #article_links.append(link)
            if link != "https://8sidor.se/demokratin-100-ar/" and link != "https://8sidor.se/viruset-corona/":
                article_links.append(link)

        # write links to file:
        with open('links/sidor8_links' + "_" + kategory + '.txt', 'a', encoding='UTF-8' ) as f:
            for link in article_links:
                f.write(link + "\n")

        i += 1

        # wait a little bit
        print("Sleeping...")
        time.sleep(SLEEP_TIME)


# from a list of article links in a file, return links in a specific range of lines
def extract_articles(kategory, start, end):
    #choose articles
    links = []
    with open('links/sidor8_links' + "_" + kategory + '.txt', 'r') as f:
        for position, line in enumerate(f):
            if position >= start and position <= end:
                links.append(line)
    #for each link get article contents
    articles = []
    for link in links:
        article_content = extract_article_content(link)
        articles.append(article_content)

    with open('articles/sidor8_articles_' + kategory + "_" + str(start) + "-" + str(end) + ".json", "w", encoding='UTF-8' ) as f:
        json.dump(articles, f, indent=3, ensure_ascii=False)

# given a link to an article, return a json object with link, title and text
def extract_article_content(link):
    # get article content
    print("Getting Article from: " + link)
    r = requests.get(link)
    data = r.text
    soup = BeautifulSoup(data, 'html.parser')
    title = soup.find("h1").text
    text = soup.find("div", class_="content").get_text()
    # save article content in dictionary
    article = {"link": link, "title": title, "text": text}
    # wait a little bit
    print("Sleeping...")
    time.sleep(SLEEP_TIME)
    return article 

# extract articles of a kategory (specific range of lines of links)
def extract_kategory(kategory, start, end):
    print("Extract Links...")
    extract_article_links(kategory, start, end)
    print("Links extracted.")
    print("Extract Articles...")
    num_lines = sum(1 for line in open('links/sidor8_links' + "_" + kategory + '.txt'))
    i = start
    while True:
        print("Article Batch " + str(i))
        extract_articles(kategory, 1+(i-1)*ARTICLES_PER_FILE, i*ARTICLES_PER_FILE)   
        i += 1
        if i > end:
            break



"""
Natural Language Processing
"""

import collections
#from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree
# next lines need to be run once
#import nltk
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')
#nltk.download('maxent_ne_chunker')
#nltk.download('words')

# get the article json objects
def get_articles(file_name):
    with open(file_name, 'r', encoding='UTF-8') as f:
        articles = json.load(f)
    return articles

# need a json object with article title and text
def article_tokens(article):
    content = article["title"] + article["text"]
    #tokens = word_tokenize(content)
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(content)
    return tokens

# freqency of tokens of a file
def freq_tokens_file(file_name):
    articles = get_articles(file_name)
    # count tokens
    tokens_freq = {}
    for article in articles:
        tokens = article_tokens(article)
        for token in tokens:
            if token in tokens_freq:
                tokens_freq[token] += 1
            else:
                tokens_freq[token] = 1
    # sort descending 
    sorted_dic = collections.OrderedDict(sorted(tokens_freq.items(), key=lambda item: item[1], reverse=True))
    with open(file_name[:len(file_name) - 4] + "_freq.json", "w", encoding='UTF-8' ) as f:
        json.dump(sorted_dic, f, indent=3, ensure_ascii=False)

# freqency for all kategory files
def freq_kategory(kategory, start):
    exists = True
    frequency = {}
    # combine all files
    i = start
    while exists:
        try:
            with open("articles_freq/sidor8_articles_" + kategory + "_" + str(1+(i-1)*ARTICLES_PER_FILE) + "-" + str(i*ARTICLES_PER_FILE) + "._freq.json", "r", encoding='UTF-8') as f:
                tokens_freq = json.load(f)

            for token in tokens_freq:
                if token in frequency:
                    frequency[token] += tokens_freq[token]
                else:
                    frequency[token] = tokens_freq[token]

            i += 1
        except Exception as e:
            #print(str(e))
            exists = False
    # sort descending 
    sorted_dic = collections.OrderedDict(sorted(frequency.items(), key=lambda item: item[1], reverse=True))
    with open("kategory_freq/sidor8_freq" + "_" + kategory + ".json", "w", encoding='UTF-8' ) as f:
        json.dump(sorted_dic, f, indent=3, ensure_ascii=False)

# calculate all freqencies of a kategory
def calculate_partial_freqs(kategory, start):
    i = start
    exists = True
    while exists:
        try:
            file_name = "articles/sidor8_articles_" + kategory + "_" + str(1+(i-1)*ARTICLES_PER_FILE) + "-" + str(i*ARTICLES_PER_FILE) + ".json"
            freq_tokens_file(file_name)
            i += 1
        except Exception as e:
            #print(str(e))
            exists = False
        freq_kategory(kategory, start)

#normalize, make lower case, remove numbers and other non usefull words
def normalize(kategory):
    with open("kategory_freq/sidor8_freq" + "_" + kategory + ".json", "r", encoding='UTF-8' ) as f:
        freq_dict = json.load(f)
    # get list of names, that should be removed
    with open("names,json", "r", encoding='UTF-8' ) as f:
        names_dict = json.load(f)
    names_list = []
    for name in names_dict:
        names_list = list(set(names_list + name.lower().split()))
    #start normalization
    new_dict = {}
    for key in freq_dict:
        # make lower key
        lowerkey = key.lower()
        # remove terms with a number
        if any(i.isdigit() for i in lowerkey):
            continue
        # remove predefined terms (specific to this data), that should not be part of freq list
        if lowerkey in REMOVE:
            continue
        # remove names
        if lowerkey in names_list:
            continue
        #make new freq list
        if lowerkey in new_dict:
            new_dict[lowerkey] += freq_dict[key]
        else:
            new_dict[lowerkey] = freq_dict[key]
    # sort descending 
    sorted_dic = collections.OrderedDict(sorted(new_dict.items(), key=lambda item: item[1], reverse=True))
    with open("kategory_freq/sidor8_freq" + "_" + kategory + "_norm.json", "w", encoding='UTF-8' ) as f:
        json.dump(sorted_dic, f, indent=3, ensure_ascii=False)

# find person names in a text (NER)
def names_in_text(text):
    name_list = []
    chunks = ne_chunk(pos_tag(word_tokenize(text)))
    for chunk in chunks:
        if hasattr(chunk, 'label'):
            if chunk.label() == "PERSON":
                name_list.append(' '.join(c[0] for c in chunk))
    return name_list
    # doesnt work well for swedish, not just names

#return freq list of person entities
def find_names(kategory, start, name_freq):
    i = start
    exists = True
    while exists:
        try:
            file_name = "articles/sidor8_articles_" + kategory + "_" + str(1+(i-1)*ARTICLES_PER_FILE) + "-" + str(i*ARTICLES_PER_FILE) + ".json"
            articles = get_articles(file_name)
            for article in articles:
                name_list = names_in_text(article["text"])
                for name in name_list:
                    if name in name_freq:
                        name_freq[name] += 1
                    else:
                        name_freq[name] = 1
            i += 1
        except Exception as e:
            #print(str(e))
            exists = False
    return name_freq

def total_freq():
    frequency = {}
    norm_frequency = {}
    for kategory in KATEGORIES:
        try:
            # for freqency
            with open("kategory_freq/sidor8_freq" + "_" + kategory + ".json", "r", encoding='UTF-8' ) as f:
                freq_dict = json.load(f)

            for token in freq_dict:
                if token in frequency:
                    frequency[token] += freq_dict[token]
                else:
                    frequency[token] = freq_dict[token]

            # for norm frequency
            with open("kategory_freq/sidor8_freq" + "_" + kategory + "_norm.json", "r", encoding='UTF-8' ) as f:
                freq_dict = json.load(f)

            for token in freq_dict:
                if token in norm_frequency:
                    norm_frequency[token] += freq_dict[token]
                else:
                    norm_frequency[token] = freq_dict[token]

        except Exception as e:
            #print(str(e))
            exists = False
    # sort descending 
    sorted_dic = collections.OrderedDict(sorted(frequency.items(), key=lambda item: item[1], reverse=True))
    with open("sidor8_freq.json", "w", encoding='UTF-8' ) as f:
        json.dump(sorted_dic, f, indent=3, ensure_ascii=False)
    sorted_dic = collections.OrderedDict(sorted(norm_frequency.items(), key=lambda item: item[1], reverse=True))
    with open("sidor8_norm_freq.json", "w", encoding='UTF-8' ) as f:
        json.dump(sorted_dic, f, indent=3, ensure_ascii=False)

"""
Main
"""

def main():
    for kategory in KATEGORIES:
        start = 1
        end = 5
        print("Data Mining Part: " + kategory)
        extract_kategory(kategory, start, end)
        print("Natural Language Processing Part: " + kategory)
        calculate_partial_freqs(kategory, start)

    #find names, to see which ones to manually remove
    # name_freq = {}
    # for kategory in KATEGORIES:
    #     start = 1
    #     name_freq = find_names(kategory, start, name_freq)
    # sorted_dic = collections.OrderedDict(sorted(name_freq.items(), key=lambda item: item[1], reverse=True))
    # with open("kategory_freq/sidor8_freq" + "_names" + ".json", "w", encoding='UTF-8' ) as f:
    #     json.dump(sorted_dic, f, indent=3, ensure_ascii=False)

    for kategory in KATEGORIES:
        normalize(kategory)

    total_freq()


if __name__ == "__main__":
    main()