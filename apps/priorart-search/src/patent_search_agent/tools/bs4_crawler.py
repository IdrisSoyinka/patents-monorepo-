import requests
from bs4 import BeautifulSoup

def get_synonyms_context(word):
    word = word.replace(" ","-")
    print(f"Running get_synonyms_context: {word}")
    url = f"https://www.thesaurus.com/browse/{word}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Không có từ vựng trong thesaurus.com!")
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    meaning = soup.select("div.tU3uvmy24AcyNXg1gHwf")
    synonyms = soup.select("div.QXhVD4zXdAnJKNytqXmK")

    context = ""
    for mean, syn in zip(meaning, synonyms):
        context += "Meaning: " + mean.select("div.MzPkuB_wA1zt60pMer_S p")[0].get_text() + "\n"
        context += "Synonyms: "
        for word in syn.select("a"):
            if word["class"] in [['Bf5RRqL5MiAp4gB8wAZa'],['CPTwwN0qNO__USQgCKp8']]:
                context += word.get_text() + ", "
        context += "\n\n"

    return context
