#!/usr/bin/env python3

from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import numpy as np
import json
import itertools

index = []


def tokenize(doc):
    return doc.lower().split(" ")


def read_json(filename):
    if filename:
        with open(filename, 'r') as f:
            return json.load(f)


def no_filter(doc):
    return doc


def only_tags(doc):
    if (doc["title"].startswith("Key:")):
        return None
    else:
        return doc


def only_keys(doc):
    if (doc["title"].startswith("Tag:")):
        return None
    else:
        return doc


def no_duplicates(doc):
    global index
    if (doc["title"] in index):
        return None
    else:
        return doc


def only_main_desc(doc):
    r = {}
    r["title"] = doc["title"]
    r["main_description"] = doc.get("main_description", None)
    return r


def has_table(doc):
    if doc.get("tables", None) is not None:
        return doc
    else:
        return None


def only_table(doc):
    if doc.get("tables", None) is not None:
        r = {}
        r["title"] = doc["title"]
        r["tables"] = doc.get("tables", None)
        return r
    else:
        return None


def over_50_times(doc):
    side = doc.get("side", None)
    if side is None:
        return None
    numbers = side.get("tag_info", None)
    if numbers is None or len(numbers) == 0:
        return None
    sum = 0
    for v in numbers.values():
        sum += int(v[0])
    if sum > 50:
        return doc
    else:
        return None


def over_100_times(doc):
    side = doc.get("side", None)
    if side is None:
        return None
    numbers = side.get("tag_info", None)
    if numbers is None or len(numbers) == 0:
        return None
    sum = 0
    for v in numbers.values():
        sum += int(v[0])
    if sum > 100:
        return doc
    else:
        return None


def over_200_times(doc):
    side = doc.get("side", None)
    if side is None:
        return None
    numbers = side.get("tag_info", None)
    if numbers is None or len(numbers) == 0:
        return None
    sum = 0
    for v in numbers.values():
        sum += int(v[0])
    if sum > 200:
        return doc
    else:
        return None


def tfidf(query, filter, amount, datastore):
    print()
    s_filter = ""
    for f in filter:
        s_filter += f.__name__ + " "
    print(s_filter + ":")

    global index
    index = []
    all_documents = []
    for doc in datastore:
        d = doc
        for f in filter:
            d = f(d)
            if (d is None):
                break
        if (d is None):
            continue
        index.append(d["title"])
        all_documents.append(json.dumps(d))
    if len(all_documents) == 0:
        print("no result")
        return

    tfidf = TfidfVectorizer(norm='l2', min_df=0, use_idf=True, smooth_idf=False,
                            sublinear_tf=True, tokenizer=tokenize, stop_words=stopwords.words('english'),
                            lowercase=True)
    tf_matrix = tfidf.fit_transform(all_documents)

    tfidf_response = tfidf.transform(query)

    if tfidf_response.size:
        result = tf_matrix * tfidf_response.T
        result_sum = result.sum(axis=1)
        for i in range(amount):
            highest_score = np.argmax(result_sum)
            result_sum[highest_score] = 0
            print(i + 1, index[highest_score])
    else:
        print("no result")


def main():
    datastore = read_json("tags.json")
    filters = [no_filter, only_tags, only_keys, no_duplicates,
               only_main_desc, has_table, only_table, over_50_times, over_100_times, over_200_times]

    while True:
        try:
            query = input("Search: ").split(" ")
        except KeyboardInterrupt as e:
            print()
            exit()
        for L in range(1, 3):
            for f in itertools.combinations(filters, L):
                tfidf(query, list(f), 3, datastore)


if __name__ == '__main__':
    main()
