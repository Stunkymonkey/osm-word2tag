#!/usr/bin/env python3

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from nltk.corpus import stopwords
import numpy as np
import json

document_0 = "China has a strong economy that is growing at a rapid pace. However politically it differs greatly from the US Economy."
document_1 = "At last, China seems serious about confronting an endemic problem: domestic violence and corruption."
document_2 = "Japan's prime minister, Shinzo Abe, is working towards healing the economic turmoil in his own country for his view on the future of his people."
document_3 = "Vladimir Putin is working hard to fix the economy in Russia as the Ruble has tumbled."
document_4 = "What's the future of Abenomics? We asked Shinzo Abe for his views"
document_5 = "Obama has eased sanctions on Cuba while accelerating those against the Russian Economy, even as the Ruble's value falls almost daily."
document_6 = "Vladimir Putin is riding a horse while hunting deer. Vladimir Putin always seems so serious about things - even riding horses. Is he crazy?"


def tokenize(doc):
    return doc.split(" ")


def find_similar(tfidf_matrix, index, top_n=5):
    cosine_similarities = linear_kernel(tfidf_matrix[index:index + 1], tfidf_matrix).flatten()
    related_docs_indices = [i for i in cosine_similarities.argsort()[::-1] if i != index]
    return [(index, cosine_similarities[index]) for index in related_docs_indices][0:top_n]


def read_json(filename):
    if filename:
        with open(filename, 'r') as f:
            return json.load(f)


def main():
    filename = "tags.json"
    datastore = read_json(filename)
    for doc in datastore:
        print(doc["title"].replace("Tag:", "").replace("Key:", ""))
        for item in doc:
            print(item, "\t", doc[item])
    # print(datastore)

    all_documents = [document_0, document_1, document_2, document_3, document_4, document_5, document_6]

    tfidf = TfidfVectorizer(norm='l2', min_df=0, use_idf=True, smooth_idf=False,
                            sublinear_tf=True, tokenizer=tokenize, stop_words=stopwords.words('english'),
                            lowercase=True)
    tfidf_matrix = tfidf.fit_transform(all_documents)
    idf = tfidf.transform(["Putin Ruble country"])
    for index, score in find_similar(tfidf_matrix, 3):
        print(score, all_documents[index])
    return


if __name__ == '__main__':
    main()
