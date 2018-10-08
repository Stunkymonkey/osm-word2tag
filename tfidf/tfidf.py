#!/usr/bin/env python3

from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import numpy as np
import json

from http.server import BaseHTTPRequestHandler, HTTPServer

index = []
index_amount = []


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
    r["title"] = doc["title"]
    r["main_description"] = doc.get("main_description", None)
    return r


def only_content(doc):
    r = {}
    r["title"] = doc["title"]
    r["content"] = doc.get("content", None)
    r["tables"] = doc.get("tables", None)
    return r


def only_side_desc(doc):
    r = {}
    r["title"] = doc["title"]
    r["side_desc"] = doc.get("side", None).get("description", None)
    return r


def tfidf(filter, datastore):
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
        if not (doc["title"].startswith("Tag:") or doc["title"].startswith("Key:")):
            continue
        # TODO use Keys to generate all tags
        if doc["title"].startswith("Key:"):
            continue
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
    return tfidf, tfidf.fit_transform(all_documents)


def query(q, tfidf, tf_matrix):
    tfidf_response = tfidf.transform(q)

    if tfidf_response.size:
        result = tf_matrix * tfidf_response.T
        result_sum = result.sum(axis=1)
        return result_sum
    else:
        return []


def get_best(result, limiting, amount):
    output = []
    for k in range(0, len(result)):
        if (index_amount[k] == 0):
            continue
        result[k] = result[k] * limiting(index_amount[k])
    for _ in range(amount):
        highest_score = np.argmax(result)
        if result[highest_score] == 0:
            break
        result[highest_score] = 0
        output.append(index[highest_score])
    return output


def cli():
    while True:
        try:
            q = input("Search: ").split(" ")
        except KeyboardInterrupt as e:
            print()
            exit()
        if not q[0]:
            continue
        output = handle_query(q)
        if output:
            for o in output:
                print(o)


def handle_query(q):
    main_desc = query(q, tfidf_main_desc, matrix_main_desc)
    content = query(q, tfidf_content, matrix_content)
    side_desc = query(q, tfidf_side_desc, matrix_side_desc)

    if len(main_desc) == 0:
        main_desc = 0
    if len(content) == 0:
        content = 0
    if len(side_desc) == 0:
        side_desc = 0

    result = main_desc * main_k + content * content_k + side_desc * side_k
    if isinstance(result, float) or (len(result) == 0):
        print("no results")
        return [""]
    return get_best(result, np.log, 5)


def main():
    global main_k
    global side_k
    global content_k

    global tfidf_main_desc
    global matrix_main_desc
    global tfidf_content
    global matrix_content
    global tfidf_side_desc
    global matrix_side_desc

    datastore = read_json("tags.json")

    main_desc_f = [no_duplicates, only_main_desc]
    content_f = [no_duplicates, only_content]
    side_desc_f = [no_duplicates, only_side_desc]
    main_k = 0.4
    side_k = 0.35
    content_k = 1 - (main_k + side_k)

    tfidf_main_desc, matrix_main_desc = tfidf(main_desc_f, datastore)
    tfidf_content, matrix_content = tfidf(content_f, datastore)
    tfidf_side_desc, matrix_side_desc = tfidf(side_desc_f, datastore)


class OSMHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        # print("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n", str(
        #     self.path), str(self.headers), post_data.decode('utf-8'))

        q = str(post_data.decode('utf-8'))
        result = handle_query(q.split(" "))
        result_s = '\n'.join(result) + "\n"

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(result_s.encode('utf-8'))


def run():
    server_address = ('127.0.0.1', 8080)
    httpd = HTTPServer(server_address, OSMHTTPRequestHandler)
    print('http server is running...')
    httpd.serve_forever()


if __name__ == '__main__':
    main()
    run()
