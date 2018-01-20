# -*- coding: utf-8 -*-
import scrapy

class Vai66tollsSpiderSpider(scrapy.Spider):
    name = 'vai66tolls-spider'
    allowed_domains = ['vai66tolls.com']
    start_urls = ['http://vai66tolls.com/']

    def parse(self, response):
        self.log('calling parse')
        self.log_response(response, "parse")

        # Parse Eastbound
        r = scrapy.FormRequest.from_response(
            response,
            callback=self.parse_form,
            #callback=self.parse_pre_toll,
            )

        yield r


    def parse_pre_toll(self, response):
        self.log('calling pre_toll')
        self.log_response(response, "pre_toll")

        r = scrapy.FormRequest.from_response(
            response,
            #formid="form1",
            formdata={
                'sm1': 'sm1|btnUpdateEndSel',
                'Dir': 'rbEast',
                'txtRunRefresh': '',
                "__ASYNCPOST": "true", # I think this is important?
                'datepicker': '12/04/2017',
                'timepicker': '8:30am',
                'ddlExitAfterSel': 10,
                'ddlEntryInterch': 5,
                'ddlExitInterch': 16,
                'btnUpdateEndSel': 'Select this Exit'
                },
            callback=self.parse_eb_entry,
        )

        yield r




    def parse_form(self, response):
        self.log('calling parse_form')
        self.log_response(response, "parse_form")

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
            callback=self.parse_pre_toll,
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