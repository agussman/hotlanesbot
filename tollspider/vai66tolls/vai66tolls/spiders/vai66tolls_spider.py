# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request, FormRequest
from itertools import izip_longest # used by grouper
import json
import datetime

OUTDIR="./log/"

class Vai66tollsSpiderSpider(scrapy.Spider):
    name = 'vai66tolls-spider'
    allowed_domains = ['vai66tolls.com']
    start_urls = ['http://vai66tolls.com/']
    #stepinc = datetime.timedelta(minutes=5)

    def __init__(self, fullDay=None,  Dir=None, *args, **kwargs):
        super(Vai66tollsSpiderSpider, self).__init__(*args, **kwargs)

        if (fullDay is not None and Dir is not None):
            self.log("fullDay={}".format(fullDay))
            self.log("Dir={}".format(Dir))

            # Validate inputs
            if (Dir != "rbEast" and Dir != "rbWest"):
                self.log("Invalid value for Dir ({}), it must be rbEast or rbWest".format(Dir))
                raise ValueError

            # Save
            self.Dir = Dir

            try:
                self.day = datetime.datetime.strptime(fullDay, "%Y-%m-%d")
                # 5:30 to 9:30 am Weekdays EastBound
                # 3:00 to 7:00 pm Weekdays Westbound
                if (Dir == "rbEast"):
                    self.timestamp = self.day + datetime.timedelta(hours=5, minutes=30)
                    self.stoptime = self.day + datetime.timedelta(hours=9, minutes=30)
                else: # rbWest
                    self.timestamp = self.day + datetime.timedelta(hours=3, minutes=00)
                    self.stoptime = self.day + datetime.timedelta(hours=7, minutes=00)
            except ValueError:
                self.log("Unable to parse day {} as form %Y-%m-%d".format(fullDay))
                raise

        else:
            now = datetime.datetime.now()
            self.day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.timestamp = now
            self.stoptime = now
            if (now >= self.day + datetime.timedelta(hours=5, minutes=30) and now <= self.day + datetime.timedelta(hours=9, minutes=30)):
                self.Dir = 'rbEast'
            else:
                self.Dir = 'rbWest'


    def parse(self, response):
        # Read the initial page
        # This function doesn't really do anything other than submit the form the first time
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

        # Set direction "Dir", rbEast (morning) or rbWest (afternoon)

        Dir = self.Dir
        #for dir in ['rbEast', 'rbWest'];
        #for Dir in ['rbWest', 'rbEast']:

        # Capture Dir in meta for downstream conditionals
        meta = {
            "Dir": Dir
        }

        # POST Dir Selection
        r = scrapy.FormRequest.from_response(
            response,
            formdata={
                'sm1': 'sm1|btnDirUpdate',
                'Dir': Dir,
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
            meta=meta
        )

        yield r

        # self.log('DOES THIS SHOW UP?')
        #
        # # POST Westbound Selection
        # r = scrapy.FormRequest.from_response(
        #     response,
        #     #formid="form1",
        #     formdata={
        #         'sm1': 'sm1|btnDirUpdate',
        #         'Dir': 'rbWest',
        #         'txtRunRefresh': '',
        #         "__ASYNCPOST": "true",  # I think this is important?
        #         'btnDirUpdate': '',
        #         },
        #     callback=self.parse_last2,
        # )
        #
        # yield r




    def parse_eb(self, response):
        self.log('calling parse_eb')
        self.log_response(response, "eb")

        # Retrieve passed variables
        meta = response.meta

        # Iterate over the Entry Interchange options
        #entry_points = response.xpath("//*[@id='ddlEntryInterch']/option/@value").extract()
        #entry_points = response.xpath("//*[@id='ddlEntryInterch']/option/text()").extract()
        entry_points = response.xpath("//*[@id='ddlEntryInterch']/option")
        for ep in entry_points[0:5]:
            value = ep.xpath('@value').extract()[0]
            text = ep.xpath('text()').extract()[0]
            if text == 'Select Location':
                continue
            self.log("Entry point: {} {}".format(value, text))

        #for ddlEntryInterch in ['5', '9']:
            ddlEntryInterch = value

            # Add in the variables we're setting
            meta.update(
                {
                    'ddlEntryInterch': ddlEntryInterch
                }
            )

            # Build the post body
            post_body = {
                'sm1': 'sm1|btnUpdateBeginSel',
                'Dir': meta["Dir"],
                'txtRunRefresh': '',
                "__ASYNCPOST": "true",  # I think this is important?
                'ddlEntryInterch': meta["ddlEntryInterch"],
                'btnUpdateBeginSel': "Select this Entry"
            }

            post_body = self.update_post_body_with_asp_vars(response, post_body)

            self.log("Let's build a FormRequest")

            # Yield a Request
            r = FormRequest(
                url="https://vai66tolls.com/",
                #method="POST",
                formdata=post_body,
                callback=self.parse_eb_entry,
                meta=meta
            )

            yield r


    def parse_eb_entry(self, response):
        self.log('calling parse_eb_entry')
        self.log_response(response, "eb_entry")

        meta = response.meta

        ddlEntryInterch = meta["ddlEntryInterch"]

        exit_points = response.xpath("//*[@id='ddlExitInterch']/option")
        for ep in exit_points[0:5]:
            value = ep.xpath('@value').extract()[0]
            text = ep.xpath('text()').extract()[0]
            if text == 'Select Location':
                continue
            self.log("Exit point: {} {}".format(value, text))

            ddlExitInterch = value
            ddlExitAfterSel = "16"

            # 5:30 to 9:30 am Weekdays EastBound
            # 3:00 to 7:00 pm Weekdays Westbound
            #day = datetime.datetime(2017, 12, 4)
            stepinc = datetime.timedelta(minutes=30)
            #timestamp = day + datetime.timedelta(hours=7, minutes=30)
            #stoptime = day + datetime.timedelta(hours=8, minutes=00)
            day = self.day
            timestamp = self.timestamp
            stoptime = self.stoptime
            if meta["Dir"] == "rbWest":
                ddlExitAfterSel = '4'
                #timestamp = day + datetime.timedelta(hours=16, minutes=30)
                #stoptime = day + datetime.timedelta(hours=17, minutes=00)

            while (timestamp <= stoptime):

                datepicker = self.timestamp.strftime("%m/%d/%Y")
                timepicker = self.timestamp.strftime("%-I : %M %p")

                # Build the post body
                post_body = {
                    'sm1': 'sm1|btnUpdateEndSel',
                    'Dir': meta["Dir"],
                    'txtRunRefresh': '',
                    "__ASYNCPOST": "true", # I think this is important?
                    'ddlEntryInterch': ddlEntryInterch,
                    'ddlExitInterch': ddlExitInterch,
                    "ddlExitAfterSel": ddlExitAfterSel,
                    "datepicker": datepicker,
                    "timepicker": timepicker,
                    'btnUpdateBeginSel': "Select this Entry"
                }

                # Things to pass along
                meta.update({
                    'ddlExitInterch': ddlExitInterch,
                    "ddlExitAfterSel": ddlExitAfterSel,
                    "ddlEntryInterch": ddlEntryInterch,
                    "timestamp": "{} + {}".format(datepicker, timepicker)
                })

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

                timestamp += self.stepinc


    def parse_last(self, response):
        self.log('calling last')
        self.log_response(response, "last")

        toll_object = response.xpath("//*[@id='spanTollAmt']/text()").extract()
        # Return 0 if we didn't get a result (note: this shouldn't happen!)
        toll_amount = toll_object[0] if len(toll_object) > 0 else "0"

        self.log("TOLL AMOUNT: {}".format(toll_amount))

        meta = response.meta

        retval = {
            "timestamp": meta["timestamp"],
            "ddlEntryInterch": meta["ddlEntryInterch"],
            "ddlExitInterch": meta["ddlExitInterch"],
            "ddlExitAfterSel": meta["ddlExitAfterSel"],
            "toll": toll_amount.replace("$", ""),
            "Dir": meta["Dir"]
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