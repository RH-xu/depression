__author__ = 'RHX'
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.http import Request

from Depression.items import DepressionItem
from Depression.items import TopicItem
from Depression.items import RecentTopicItem
from Depression.items import ResponseItem
import re


class DepressionSpider(CrawlSpider):
    name = "post"
    allowed_domains = ["douban.com"]
    start_urls = [
                  #"http://www.douban.com/group/search?cat=1019&q=%E6%8A%91%E9%83%81%E7%97%87"
                  #"http://www.douban.com/group/151898"
                  # "http://www.douban.com/group/151898/discussion?start=3450"
                   "http://www.douban.com/group/16530/discussion?start=0" # younth loneliness depression
                 ]
    rules = [
            Rule(SgmlLinkExtractor(allow=(r'/group/16530/discussion\?start=\d'),restrict_xpaths=('//span[@class="next"]') ),
                 follow=True),

            Rule(SgmlLinkExtractor(allow=('/group/topic/[^/]+/$'), restrict_xpaths=('//td[@class="title"]')),
                 callback='parse_post', follow=True),

            #Rule(SgmlLinkExtractor(allow=('/group/topic/[^/]+/\?start'),restrict_xpaths=('//span[@class="next"]')),
            #     callback="parse_reply", follow=True), # this rule to extract the reply of next page
            ]

    def _get_ID_from_topic_URL(self, url):
        m = re.search("^http://www.douban.com/group/topic/([^/]+)/", url)
        if (m):
            return m.group(1)
        else:
            return 0

    def _get_ID_from_member_URL(self, url):
        m = re.search("^http://www.douban.com/group/people/([^/]+)/$", url)
        if (m):
            return m.group(1)
        else:
            return 0

    def parse_post(self, response):
        self.log("Fetch post: Post, Post, Post: %s" % response.url) #need to be the post ID
        itemP = TopicItem()

        itemP['title_P'] = response.xpath('.//h1/text()').extract()
        itemP['topicID_P'] = self._get_ID_from_topic_URL(response.url) # need to understand

        itemP['link_P'] = response.url
        itemP['author_P'] = response.xpath('//span[@class="from"]/a/@href').re(r'people/([^/]+)/$') # another way to do so
        itemP['createTime_P'] = response.xpath('//h3/span[@class="color-green"]/text()').extract()

        itemP['content_P'] = response.xpath('//div[@class="topic-content"]/p/text()').re("^[^\r](.*)$") # filter out the space .extract()
        num = response.xpath('//span[@class="fav-num"]/a/text()').re("\d+")
        if (num):
            itemP['numberLikes_P'] = str(num[0]) # change the type to 'str'
        else:
            itemP['numberLikes_P'] = '0'

        yield itemP
        resTos=[]

        ul = response.xpath('//ul[@class="topic-reply" and @id = "comments"]/li')

        if (len(ul)>0):
            self.log("we are going to extract one reply if any with length %d :" % len(ul))
            # extract reply from this page
            for li in ul:
                replys = li.xpath('.//div[@class="reply-quote"]') # need to correspond to one ul in topic-reply
                if (replys):
                    resTo = replys.xpath('.//span[@class="pubdate"]/a/@href').re(r'people/([^/]+)/$')
                else:
                    resTo = ['0000000'] # 0 denotes respond to nobody
                resTos.append(resTo)

            # IDs = ul.xpath('.//@id').extract()
            authors = ul.xpath('.//h4/a/@href').re(r'people/([^/]+)/$')
            times = ul.xpath('.//h4/span/text()').extract()
            contents = ul.xpath('.//div[@class="reply-doc content"]/p') # .extract() to  # to keep the same length with others

            self.log("Lengths compare, ID: 0, authors: %d, times: %d, contents: %d; "%(len(authors), len(times), len(contents)) )

            for author, time, content, resT in zip( authors, times, contents, resTos):
                itemR = ResponseItem()
                itemR['topicID_R'] = self._get_ID_from_topic_URL(response.url)
                #itemR['responseID_R'] = ID.strip()  #.append(ID)
                itemR['author_R'] = author.strip() #.append(author)
                itemR['time_R'] = time.strip() #.append(time)
                itemR['content_R'] = "".join(content.xpath('.//text()').re("^[^\r](.*)$")).encode('utf-8').strip() #.append("".join(content).encode('utf-8'))
                itemR['responseTo_R'] = resT
                self.log("We have print out one reply")
                yield itemR
                #itemRs.append(itemR)

            #itemRs.append(self.parse_reply(response))
            #itemR=self.parse_reply(response)

            nextReply = response.xpath('//span[@class="next"]/link/@href').extract()
            if (len(nextReply)>0):
                self.log("There is more pages of reply, go ahead, with next %d " % len(nextReply))
                yield Request(nextReply[0], callback=self.parse_post) # Request() function, the first parameter should be a string
        #return itemP, itemRs


    def parse_reply(self, response):
        self.log("Extract reply: Reply, Reply, Reply %s" % response.url)

        """
        itemR = ResponseItem()
        itemR['topicID_R'] = self._get_ID_from_topic_URL(response.url) # PRoblem, url, response.xpath('').re(r'topic/([^/]+)/$') #
        itemR['responseID_R'] = []
        itemR['author_R'] = []
        itemR['time_R'] =[]
        itemR['content_R'] = []
        itemR['responseTo_R'] =[]
        """
        itemRs=[]
        resTos=[]

        ul = response.xpath('//ul[@class="topic-reply"]/li')
        for li in ul:
            replys = li.xpath('.//div[@class="reply-quote"]') # need to correspond to one ul in topic-reply
            if (replys):
                resTo = replys.xpath('.//span[@class="pubdate"]/a/@href').re(r'people/([^/]+)/$')
            else:
                resTo = ['0000000'] # 0 denotes respond to nobody
            resTos.append(resTo)

        # IDs = ul.xpath('.//@id').extract()
        authors = ul.xpath('.//h4/a/@href').re(r'people/([^/]+)/$')
        times = ul.xpath('.//h4/span/text()').extract()
        contents = ul.xpath('.//div[@class="reply-doc content"]/p').extract() # to keep the same length with others

        self.log("Lengths compare, ID: 0, authors: %d, times: %d, contents: %d; "%(len(authors), len(times), len(contents)) )

        for author, time, content, resT in zip( authors, times, contents, resTos):
            itemR = ResponseItem()
            itemR['topicID_R'] = self._get_ID_from_topic_URL(response.url)
            #itemR['responseID_R'] = ID.strip()  #.append(ID)
            itemR['author_R'] = author.strip() #.append(author)
            itemR['time_R'] = time.strip() #.append(time)
            itemR['content_R'] = "".join(content).encode('utf-8').strip() #.append("".join(content).encode('utf-8'))
            itemR['responseTo_R'] = resT
            self.log("We have print out one reply")
            yield itemR
            itemRs.append(itemR)

        # return itemRs # to handel the return, the methods could be

            #JsonLinesItemExporter.export_item(itemR)

        #return itemR # I want to set that, each item with a line


