# -*- coding: utf-8 -*-
import scrapy
from scrapy.http.cookies import CookieJar

class Vai66tollsSpiderSpider(scrapy.Spider):
    name = 'vai66tolls-spider'
    allowed_domains = ['vai66tolls.com']
    start_urls = ['http://vai66tolls.com/']

    def parse(self, response):
        filename = "/tmp/body.html"
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)

        self.log('Initial Response headers: (%s)' % response.headers)

        # look for "cookie" things in response headers
        poss_cookies = response.headers.getlist('Set-Cookie')
        self.log('Set-Cookie?: (%s)' % poss_cookies)

        poss_cookies = response.headers.getlist('Cookie')
        self.log('Cookie?: (%s)' % poss_cookies)

        poss_cookies = response.headers.getlist('cookie')
        self.log('cookie?: (%s)' % poss_cookies)

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
        self.log('Request headers: %s' % response.request.headers)
        self.log('Request cookies: %s' % response.request.cookies)
