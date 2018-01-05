import scrapy

class VAI66TollsViewStateSpider(scrapy.Spider):
    name = 'vai66tolls'
    start_urls = ['https://vai66tolls.com/']
    download_delay = 1

    def parse(self, response):
        filename = "/tmp/body.html"
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)


        self.log('Other thing?')
        # Parse Eastbound
        r = scrapy.FormRequest.from_response(
            response,
            headers={
                "Host": "vai66tolls.com",
                #User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:52.0) Gecko/20100101 Firefox/52.0
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "X-Requested-With": "XMLHttpRequest",
                "X-MicrosoftAjax": "Delta=true",
                "Cache-Control": "no-cache",
                #Content-Type: application/x-www-form-urlencoded; charset=utf-8
                "Referer": "https://vai66tolls.com/",
                "Content-Length": "5945",
                #Cookie: _ga=GA1.2.54030347.1515124135; _gid=GA1.2.1927582929.1515124135; ASP.NET_SessionId=0lxzfbuje3m04qyiw1qrw5dp
                "Connection": "keep-alive",
                "Pragma": "no-cache"
            },
            formid="form1",
            formdata={
                'sm1': 'sm1|btnDirUpdate',
                'Dir': 'rbEast',
                "__ASYNCPOST": "true",
                'datepicker': '01/02/2018',
                'timepicker': '11:04pm',

                },
            callback=self.parse_eb,
        )

        print "HEADERS"
        print r.headers
        print "BODY"
        print "\n\n".join(r.body.split('&'))

        yield r

        self.log('Done?')

    def parse_eb(self, response):
        filename = "/tmp/eb.txt"
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)