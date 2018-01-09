# -*- coding: utf-8 -*-
import scrapy


class Vai66tollsSpiderSpider(scrapy.Spider):
    name = 'vai66tolls-spider'
    allowed_domains = ['vai66tolls.com']
    start_urls = ['http://vai66tolls.com/']

    def parse(self, response):
        filename = "/tmp/body.html"
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)

        # Parse Eastbound
        r = scrapy.FormRequest.from_response(
            response,
            callback=self.parse_eb,
            )

        yield r

    def parse_eb(self, response):
        filename = "/tmp/eb.txt"
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)

        self.log('request cookies: %s' % response.request.cookies)
