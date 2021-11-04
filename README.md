# Sidor8 - Freq List
 Data Mining - Swedisch Freqency List from Sidor8

## Data Mining
Get Articles from the website https://8sidor.se.
- from all kategories
- specify how many pages in `main`
- extract all links to articles
- extract articles (Title, Content)

## Natrual Language Processing
Get a Frequency List
- for each kategory
- for all collected articles
- simple normalization (all lower case)
- simple cleaning of terms (remove Names, unnecessary words, no numbers)

## Result
`result.json`
A freqency list with 2875 words from ca. 1350 articles.
- Most frequnet word: "det" - 6402 
- Limited to words appearing at least 6-times 

## Requirements
- requests
- bs4
- time
- json
- collections
- nltk