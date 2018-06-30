# -*- coding: utf-8 -*-
import scrapy
from os import listdir
from scrapy.item import Item, Field
from bs4 import BeautifulSoup, Comment, Tag, NavigableString
from urllib.request import urlopen
import logging


logger = logging.getLogger('OsmwikiSpider')
folder = "./osmwiki/"
start_fresh = True


class OsmwikiItem(Item):
    title = Field()
    url = Field()
    side = Field()
    main_description = Field()
    content = Field()
    related_terms = Field()
    tables = Field()


def filter(string):
    return string.replace("\u2009", " ").replace("\u2014", " - ").strip()


class OsmwikiSpider(scrapy.Spider):
    name = "osmWiki"
    allowed_domains = ["wiki.openstreetmap.org"]
    custom_settings = {
        "CONCURRENT_REQUESTS": "3",
        "DOWNLOAD_DELAY": "1",
        "MAIL_FROM": "server@buehler.rocks",
        "LOG_LEVEL": "WARNING"
    }
    start_urls = []
    with open("links.txt", "rt") as f:
        if start_fresh:
            start_urls = [url.strip() for url in f.readlines()]
        else:
            link_list = [url.strip() for url in f.readlines()]
            files = listdir(folder)
            for link in link_list:
                if link.split("/")[-1] + ".html" in files:
                    continue
                else:
                    start_urls.append(link)

    def parse(self, response):
        """
        # self.save_to_file(response)
        page = response.url.split("/")[-1]
        filename = "%s%s.html" % (folder, page)
        with open(filename, "wb") as f:
            f.write(response.body)
        logger.warn("Saved file %s" % filename)
        """
        logger.warn(response.url)

        item = OsmwikiItem()
        soup = BeautifulSoup(response.text, 'lxml')
        title = soup.title.string.replace(" - OpenStreetMap Wiki", "")

        item["title"] = title
        item["url"] = response.url

        # get content from wiki-page
        content = soup.find(
            "div", {"class": "mw-content-ltr", "id": "mw-content-text"})

        # remove comments
        for element in content(text=lambda text: isinstance(text, Comment)):
            element.extract()

        # remove languages
        for div in soup.find_all("div", {'class': 'languages'}):
            div.decompose()

        # find overview and remove it from soup
        for div in soup.find_all("div", {"class": "toc"}):
            div.decompose()

        item["related_terms"] = []
        # find related_terms and remove it from soup
        for div in soup.find_all("div", {"id": "related-terms-list"}):
            terms = (div.text.replace("related terms:", "").replace("‹", "").replace("›", "").split())
            for term in terms:
                item["related_terms"].append(term)
            div.decompose()

        # and remove it from soup
        for div in soup.find_all("div", {"class": "catlinks"}):
            div.decompose()

        item["tables"] = []
        for table in content.find_all("table")[1:]:
            nextTable = table
            while True:
                nextTable = nextTable.nextSibling
                if nextTable is None:
                    break
                if isinstance(nextTable, NavigableString):
                    continue
                if isinstance(nextTable, Tag):
                    if nextTable.name == "table":
                        break

            # non wiki tables need to be ignored (tables in tables, ...)
            if "class" not in table or "wikitable" not in table["class"]:
                continue
            keys = [filter(i.text) for i in table.find('tr').find_all('th')]
            result_table = []
            for row in table.find_all('tr')[1:]:
                vals = []
                for data in row.find_all('td'):
                    vals.append(filter(data.text))
                result_table.append(dict(zip(keys, vals)))
            table.decompose()
            item["tables"].append(result_table)

        # first description
        ps = content.find_all("p")
        if len(ps) > 1:
            current = content.find_all("p")[1]
            main_description = current.get_text()
            while True:
                current = current.nextSibling
                if current is None:
                    break
                if isinstance(current, NavigableString):
                    continue
                if isinstance(current, Tag):
                    if current.name == "h2":
                        break
                    if current.name != "p":
                        continue
                main_description += " " + current.get_text()
            item["main_description"] = filter(main_description)

        item["content"] = {}
        for heading in content.find_all("h2"):
            nextNode = heading
            result = ""
            while True:
                nextNode = nextNode.nextSibling
                if nextNode is None:
                    break
                if isinstance(nextNode, NavigableString):
                    continue
                if isinstance(nextNode, Tag):
                    if nextNode.name == "h2":
                        break
                    result += " " + nextNode.get_text()

            new_heading = heading.text.lower().strip().replace(":", "")
            if result.strip() is "":
                item["content"][new_heading] = None
            else:
                item["content"][new_heading] = filter(result)

        item["side"] = {}
        # logger.warn(middle_description.get_text())
        table = soup.find("table", {"class": "description"})
        if table is not None:
            side_description = table.findAll(
                'tr', {"class": "d_description content"})
            if side_description:
                item["side"]["description"] = side_description[0].text.strip()
            group = table.find('tr', {"class": "d_group content"})
            if group:
                item["side"]["group"] = group.text.replace("Group:", "").strip()
            usefull_combinations = table.find('tr', {"class": "d_combination content"})
            if usefull_combinations:
                usefull_combinations_l = []
                items = usefull_combinations.findAll("li")
                for i in items:
                    usefull_combinations_l.append(i.text.strip())
                item["side"]["usefull_combinations"] = usefull_combinations_l
            taginfo = table.find('tr', {"class": "d_taginfo content"})
            if taginfo:
                frame = taginfo.findAll('iframe')
                if frame:
                    frame_response = urlopen("https:" + frame[0].attrs['src'])
                    iframe_soup = BeautifulSoup(frame_response, 'lxml')
                    taginfo_table = iframe_soup.findAll('tr')
                    item["side"]["tag_info"] = {}
                    for tag_i in taginfo_table:
                        img = tag_i.find('img', alt=True)
                        save_string = img["alt"].lower()
                        amount = tag_i.findAll("td")
                        tag_i_list = []
                        tag_i_list.append(int(filter(amount[1].text).replace(" ", "")))
                        if len(amount) == 3:
                            tag_i_list.append(float(filter(amount[2].text).replace(" ", "").replace("%", "")))
                        item["side"]["tag_info"][save_string] = tag_i_list

            # print(taginfo)
        # content.prettify()
        return item
