# -*- coding: utf-8 -*-
import scrapy

OUTDIR="./log/"

class Vai66tollsSpiderSpider(scrapy.Spider):
    name = 'vai66tolls-spider'
    allowed_domains = ['vai66tolls.com']
    start_urls = ['http://vai66tolls.com/']

    def parse(self, response):
        # Call the initial page
        self.log('calling parse')
        self.log_response(response, "parse")

        # Parse Eastbound
        r = scrapy.FormRequest.from_response(
            response,
            callback=self.parse_form,
            )

        yield r

    def parse_form(self, response):
        self.log('calling parse_form')
        self.log_response(response, "parse_form")

        # POST Eastbound Selection
        r = scrapy.FormRequest.from_response(
            response,
            #formid="form1",
            formdata={
                'sm1': 'sm1|btnDirUpdate',
                'Dir': 'rbEast',
                'txtRunRefresh': '',
                "__ASYNCPOST": "true",  # I think this is important?
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

        self.log('DOES THIS SHOW UP?')

        # POST Westbound Selection
        r = scrapy.FormRequest.from_response(
            response,
            #formid="form1",
            formdata={
                'sm1': 'sm1|btnDirUpdate',
                'Dir': 'rbWest',
                'txtRunRefresh': '',
                "__ASYNCPOST": "true",  # I think this is important?
                'btnDirUpdate': '',
                },
            callback=self.parse_last2,
        )

        yield r


    def parse_pre_toll(self, response):
        self.log('calling pre_toll')
        self.log_response(response, "pre_toll")

        r = scrapy.FormRequest.from_response(
            response,
            formid="form1",
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









    def parse_eb(self, response):
        self.log('calling parse_eb')
        self.log_response(response, "eb")

        # Iterate over the Entry Interchange options
        #entry_points = response.xpath("//*[@id='ddlEntryInterch']/option/@value").extract()
        #entry_points = response.xpath("//*[@id='ddlEntryInterch']/option/text()").extract()
        entry_points = response.select("//*[@id='ddlEntryInterch']/option")
        for ep in entry_points:
            value = ep.select('@value').extract()
            text = ep.select('text()').extract()
            self.log("Entry point: {}".format(value))


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


    def parse_last(self, response):
        self.log('calling last')
        self.log_response(response, "last")

    def parse_last2(self, response):
        self.log('calling last2')
        self.log_response(response, "last2")



    def log_response(self, response, prefix):
        filename = OUTDIR+"/{}.html".format(prefix)
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('%s Saved file %s' % (prefix, filename))
        self.log('%s Request headers: %s' % (prefix, response.request.headers))
        self.log('%s Request cookies: %s' % (prefix, response.request.cookies))
        self.log('%s Request body split:')
        self.log("\n\t".join(response.request.body.split('&')))
        self.log('%s Response headers: %s' % (prefix, response.headers))
