#!/usr/bin/env python3

from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import numpy as np
import json
import itertools

index = []
index_amount = []


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


def only_table(doc):
    if doc.get("tables", None) is not None:
        r = {}
        r["title"] = doc["title"]
        r["tables"] = doc.get("tables", None)
        return r
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
    index_amount = []
    for doc in datastore:
        d = doc
        side = doc.get("side", None)
        sum = 0
        if side is not None:
            numbers = side.get("tag_info", None)
            if numbers is not None and len(numbers) != 0:
                for v in numbers.values():
                    sum += int(v[0])
        for f in filter:
            d = f(d)
            if (d is None):
                break
        if (d is None):
            continue
        index.append(d["title"])
        index_amount.append(sum)
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
        for k in range(0, len(result_sum)):
            if (index_amount[k] == 0):
                continue
            result_sum[k] = result_sum[k] * np.log(index_amount[k])
        for i in range(amount):
            highest_score = np.argmax(result_sum)
            result_sum[highest_score] = 0
            print(i + 1, index[highest_score])
    else:
        print("no result")


def main():
    datastore = read_json("tags.json")
    filters = [no_filter, only_tags, only_keys, no_duplicates,
               only_main_desc, only_table]

    """for L in range(1, 3):
        for f in itertools.combinations(filters, L):
            tfidf("bath highway".split(" "), list(f), 3, datastore)
    return"""

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
