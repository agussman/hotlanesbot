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

        self.log('Initial request headers: (%s)' % response.headers)

        proto_cookies = response.headers.getlist('Cookie')
        self.log('Cookies?: (%s)' % proto_cookies)

        cookieJar = response.meta.setdefault('cookie_jar', CookieJar())
        cookieJar.extract_cookies(response, response.request)
        for cookie in cookieJar:
            self.log('cookies %s' % cookie)

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
        self.log('request headers: %s' % response.request.headers)
        self.log('request cookies: %s' % response.request.cookies)
