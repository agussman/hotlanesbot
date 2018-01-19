# -*- coding: utf-8 -*-
import scrapy

class Vai66tollsSpiderSpider(scrapy.Spider):
    name = 'vai66tolls-spider'
    allowed_domains = ['vai66tolls.com']
    start_urls = ['http://vai66tolls.com/']

    def parse(self, response):
        # Doesn't do anything other than make the form request so we can get a cookie
        filename = "/tmp/parse.html"
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
            callback=self.parse_form,
            #callback=self.parse_eb,
            )

        yield r

    def parse_form(self, response):
        filename = "/tmp/parse_form.html"
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
        self.log('2 Request headers: %s' % response.request.headers)
        self.log('2 Request cookies: %s' % response.request.cookies)
        self.log('2 Response headers: %s' % response.headers)

        # Parse Eastbound
        r = scrapy.FormRequest.from_response(
            response,
            #formid="form1",
            formdata={
                'sm1': 'sm1|btnDirUpdate',
                'Dir': 'rbEast',
                'txtRunRefresh': '',
                "__ASYNCPOST": "true", # I think this is important?
                'btnDirUpdate': '',
                #'datepicker': '12/04/2017',
                #'timepicker': '7:30am',
                #'ddlExitAfterSel': '16',
                #'ddlEntryInterch': '5',
                #'ddlExitInterch': '16',
                },
            callback=self.parse_eb,
        )

        yield r




    def parse_eb(self, response):
        self.log('calling parse_eb')
        self.log_response(response, "eb")

        r = scrapy.FormRequest.from_response(
            response,
            #formid="form1",
            formdata={
                'sm1': 'sm1|btnUpdateBeginSel',
                'Dir': 'rbEast',
                'txtRunRefresh': '',
                "__ASYNCPOST": "true", # I think this is important?
                #'datepicker': '12/04/2017',
                #'timepicker': '7:30am',
                #'ddlExitAfterSel': 16,
                'ddlEntryInterch': 5,
                #'ddlExitInterch': 16,
                'btnUpdateBeginSel': "Select this Entry"
                },
            callback=self.parse_eb_entry,
        )

        yield r


    def parse_eb_entry(self, response):
        self.log('calling parse_eb_entry')
        self.log_response(response, "eb_entry")






    def log_response(self, response, prefix):
        filename = "/tmp/{}.html".format(prefix)
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('%s Saved file %s' % (prefix, filename))
        self.log('%s Request headers: %s' % (prefix, response.request.headers))
        self.log('%s Request cookies: %s' % (prefix, response.request.cookies))
        self.log('%s Response headers: %s' % (prefix, response.headers))
        self.log("\n".join(response.request.body.split('&')))