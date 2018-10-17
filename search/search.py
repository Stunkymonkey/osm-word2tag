#!/usr/bin/env python3

from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import numpy as np
import json
import sys

import gensim

from http.server import BaseHTTPRequestHandler, HTTPServer

index = []
index_amount = []

main_k = 0.4
side_k = 0.35
content_k = 1 - (main_k + side_k)

gmodel = gensim.models.KeyedVectors.load_word2vec_format(
    './GoogleNews-vectors-negative300.bin', binary=True)


def tokenize(doc):
    return doc.lower().split(" ")


def read_json(filename):
    if filename:
        with open(filename, 'r') as f:
            return json.load(f)


def no_duplicates(doc):
    global index
    if (doc["title"] in index):
        return None
    else:
        return doc


def only_main_desc(doc):
    r = {}
    r["main_description"] = doc.get("main_description", None)
    return r


def only_content(doc):
    r = {}
    r["content"] = doc.get("content", None)
    r["tables"] = doc.get("tables", None)
    return r


def only_side_desc(doc):
    r = {}
    r["side_desc"] = doc.get("side", None).get("description", None)
    return r


def create_index(filter, datastore):
    global index
    index = []
    global index_amount
    index_amount = []
    all_documents = []
    for doc in datastore:
        d = doc
        side = doc.get("side", None)
        sum = 0
        if side is not None:
            numbers = side.get("tag_info", None)
            if numbers is not None and len(numbers) != 0:
                for v in numbers.values():
                    sum += int(v[0])
        if not (doc["title"].startswith("Tag:")):
            continue
        d = filter(d)
        if d is None:
            continue
        index.append(d["title"])
        if sum == 0:
            index_amount.append(0)
        else:
            index_amount.append(np.log(sum))
        all_documents.append(d)
    return all_documents


def tfidf(filter, all_documents):
    specific_docs = []
    for doc in all_documents:
        d = filter(doc)
        specific_docs.append(json.dumps(d))

    tfidf = TfidfVectorizer(norm='l2', min_df=0, use_idf=True, smooth_idf=False,
                            sublinear_tf=True, tokenizer=tokenize, stop_words=stopwords.words('english'),
                            lowercase=True)
    return tfidf, tfidf.fit_transform(specific_docs)


def query(q, tfidf, tf_matrix):
    tfidf_response = tfidf.transform(q)

    if tfidf_response.size:
        result = tf_matrix * tfidf_response.T
        result_sum = result.sum(axis=1)
        return result_sum
    else:
        return np.zeros((tf_matrix.shape[0], 1))


def limit(result):
    for k in range(0, len(result)):
        if (index_amount[k] == 0):
            continue
        result[k] = result[k] * index_amount[k]
    return result


def handle_query(q):
    main_desc = query(q, tfidf_main_desc, matrix_main_desc)
    content = query(q, tfidf_content, matrix_content)
    side_desc = query(q, tfidf_side_desc, matrix_side_desc)

    result = main_desc * main_k + content * content_k + side_desc * side_k
    return limit(result)


def get_best(result, amount):
    output = []
    for _ in range(amount):
        highest_score = np.argmax(result)
        if result[highest_score] == 0:
            break
        result[highest_score] = 0
        output.append(index[highest_score])
    return output


def summarize(query, amount, ms):
    q1 = handle_query(query)
    vectors = []

    for q in [i[0] for i in ms]:
        vectors.append(handle_query([q]))
    sum = q1
    for v, similarity in zip(vectors, [i[1] for i in ms]):
        sum += similarity * v
    return get_best(sum, amount)


def load():
    global tfidf_main_desc, matrix_main_desc
    global tfidf_content, matrix_content
    global tfidf_side_desc, matrix_side_desc

    datastore = read_json("tags.json")

    all_documents = create_index(no_duplicates, datastore)

    tfidf_main_desc, matrix_main_desc = tfidf(only_main_desc, all_documents)
    tfidf_content, matrix_content = tfidf(only_content, all_documents)
    tfidf_side_desc, matrix_side_desc = tfidf(only_side_desc, all_documents)


class OSMHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        q = str(post_data.decode('utf-8'))

        request = json.loads(q)
        user_input = request["query"].split(" ")

        ms = gmodel.most_similar(positive=user_input, topn=int(request["nearest_neighbor"]))
        result = summarize(user_input, int(request["amount"]), ms)

        result_s = json.dumps(result) + "\n"
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(result_s.encode('utf-8'))


def run():
    server_address = ('127.0.0.1', 8080)
    httpd = HTTPServer(server_address, OSMHTTPRequestHandler)
    print('http server is running...')
    httpd.serve_forever()


def cli():
    while True:
        try:
            q = input("Search: ").split(" ")
        except KeyboardInterrupt as e:
            print()
            exit()
        if not q[0]:
            continue
        ms = gmodel.most_similar(positive=q, topn=10)
        result = summarize(q, 5, ms)
        if result:
            for r in result:
                print(r)


if __name__ == '__main__':
    load()
    if sys.argv[1].lower() == "cli":
        cli()
    else:
        run()
