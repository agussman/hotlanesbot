# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request, FormRequest
from itertools import izip_longest # used by grouper
import json

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
        entry_points = response.xpath("//*[@id='ddlEntryInterch']/option")
        for ep in entry_points:
            value = ep.xpath('@value').extract()[0]
            text = ep.xpath('text()').extract()[0]
            if text == 'Select Location':
                continue
            self.log("Entry point: {} {}".format(value, text))


        # Build the post body
        post_body = {
            'sm1': 'sm1|btnUpdateBeginSel',
            'Dir': 'rbEast',
            'txtRunRefresh': '',
            "__ASYNCPOST": "true", # I think this is important?
            'ddlEntryInterch': '5',
            'btnUpdateBeginSel': "Select this Entry"
        }

        post_body = self.update_post_body_with_asp_vars(response, post_body)

        self.log("Let's build a FormRequest")

        # Yield a Request
        r = FormRequest(
            url="https://vai66tolls.com/",
            #method="POST",
            formdata=post_body,
            callback=self.parse_eb_entry
        )

        yield r


    def parse_eb_entry(self, response):
        self.log('calling parse_eb_entry')
        self.log_response(response, "eb_entry")

        exit_points = response.xpath("//*[@id='ddlExitInterch']/option")
        for ep in exit_points:
            value = ep.xpath('@value').extract()[0]
            text = ep.xpath('text()').extract()[0]
            if text == 'Select Location':
                continue
            self.log("Exit point: {} {}".format(value, text))

            # Build the post body
            post_body = {
                'sm1': 'sm1|btnUpdateEndSel',
                'Dir': 'rbEast',
                'txtRunRefresh': '',
                "__ASYNCPOST": "true", # I think this is important?
                'ddlEntryInterch': '5',
                'ddlExitInterch': value,
                "ddlExitAfterSel": value,
                "datepicker": "12/04/2017",
                "timepicker": "8 : 30 am",
                'btnUpdateBeginSel': "Select this Entry"
            }

            # Things to pass along
            meta = {
                'ddlExitInterch': value,
                "ddlExitAfterSel": value,
            }

            post_body = self.update_post_body_with_asp_vars(response, post_body)

            self.log("Let's build another FormRequest")

            # Yield a Request
            r = FormRequest(
                url="https://vai66tolls.com/",
                #method="POST",
                formdata=post_body,
                callback=self.parse_last,
                meta=meta
            )

            yield r


    def parse_last(self, response):
        self.log('calling last')
        self.log_response(response, "last")

        toll_amount = response.xpath("//*[@id='spanTollAmt']/text()").extract()[0]

        self.log("TOLL AMOUNT: {}".format(toll_amount))

        meta = response.meta

        retval = {
            "timestamp": "20170104",
            "ddlEntryInterch": "5",
            "ddlExitInterch": meta["ddlExitInterch"],
            "toll": toll_amount.replace("$", "")
        }

        yield retval



    def update_post_body_with_asp_vars(self, response, post_body):
        asp_vars = self.extract_asp_vars(response)

        # prepopulate with stuff we parsed from asp_vars or empty string if its not there
        for key in ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']:
            post_body[key] = asp_vars[key]
        for key in ['__EVENTTARGET', '__EVENTARGUMENT', '__LASTFOCUS']:
            post_body[key] = ''

        return post_body


    def extract_asp_vars(self, response):
        # Parse the funky pipedelimited asp response data, grab the ASP.net variables
        asp_vars = {}
        for (length, type, id, content) in grouper(response.body.split("|"), 4):
            self.log("pipedem: {}".format(id))
            if id and id.startswith("__"):  # e.g. __VIEWSTATE
                asp_vars[id] = content

        return asp_vars






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


#
# END CLASS
# UTILITY STUFF HERE, MOVE TO OWN FILE
#


# itertools example, move to utils file
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # from itertools import zip_longest
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)