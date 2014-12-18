__author__ = 'ronghua'

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item
from Depression.items import DepressionItem
from Depression.items import TopicItem
import re

class DepressionSpider(BaseSpider):
    name = "depression"
    allowed_domains = ["douban.com"]
    start_urls = ["http://www.douban.com/group/151898"]

    def parse(self,response):
        # hxs = HtmlXPathSelector(response)
        itemD = DepressionItem() # !!! take care of the parentheses
        itemD['groupName'] = response.xpath('//h1/text()').re("^\s+(.*)\s+$")
        itemD['groupIntro'] = response.xpath('//div[contains(@class,"group-intro")]/text()').re("^\s+(.*)\s+$")

        itemT = TopicItem()
        itemT['title'] = []
        itemT['link'] = []

        td = response.xpath('//td[contains(@class,"title")]')
        for index in td:
            itemT['title'].append(index.xpath('.//a/@title | .//a/@href').extract()) # extract the text of all topics in one page, how to get more papges


            #itemT['link'].append(index.xpath('.//a/@href').extract())

        #itemT['title'] = response.xpath('//td[contains(@class,"title")]/a/text()').extract()

        itemD['essenceTopic'] = response.xpath('//a[contains(@href,"essence#topic")]/@href').extract() # get the link of essence topics


        return itemD, itemT
