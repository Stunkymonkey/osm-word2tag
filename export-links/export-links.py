#!/usr/bin/env python3


import xml.etree.ElementTree as ET

languages = ["Ar", "Az", "Bg", "Ca", "Cs", "Da", "El", "Eo", "Et", "Fa", "Fi",
             "Gl", "HU", "Hr", "Ht", "Id", "En", "Ko", "Lt", "Lv", "Ms", "My",
             "Ne", "No", "Oc", "Pl", "Pt", "Ro", "Sk", "Sq", "Sv", "Tr", "Uk",
             "Vi", "Zh-hans", "Zh-hant", "Pt-br", "Sh", "Zh", "De", "Es", "Fr",
             "It", "Ja", "NL", "Ru"]
url = "https://wiki.openstreetmap.org/wiki/"


def filter_keys(link):
    for lang in languages:
        if not link.startswith(url + "Key:"):
            return None
        else:
            lenght = len(url + "Key:")
            if link[lenght].isupper():
                return None
        if link.startswith(url + lang):
            return None
    return link


def filter_tags(link):
    for lang in languages:
        if not link.startswith(url + "Tag:"):
            return None
        else:
            lenght = len(url + "Tag:")
            if link[lenght].isupper():
                return None
        if link.startswith(url + lang):
            return None
    return link


def filter_languages(link):
    for lang in languages:
        if link.startswith(url + lang):
            return None
    if len(link) >= len(url) + 3 and link[len(url) + 2] == ":":
        return None
    return link


def read_xml():
    tree = ET.parse('sitemap-wiki-NS_0-0.xml')
    global root
    root = tree.getroot()


def filter(use_filter, links):
    for url in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        result = use_filter(loc.text)
        if result:
            links.append(loc.text)


def write_file(file_name, links):
    with open(file_name, 'w') as the_file:
        for link in links:
            the_file.write(link + "\n")


def export(use_filter, file_name):
    links = []
    filter(use_filter, links)
    write_file(file_name, links)


if __name__ == '__main__':
    read_xml()
    export(filter_languages, "languages.txt")
    export(filter_keys, "keys.txt")
    export(filter_tags, "tags.txt")
