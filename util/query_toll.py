#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
import csv
from optparse import OptionParser
import json
import requests

#from creoleparser import text2html

print __file__
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pprint

# Output CSV fields used by ISEBOX
FIELDS=['timestamp','start','end','toll','duration']

def main():
    
    (options, args) =  get_options()
    
    # Query the API
    apiurl="https://www.495expresslanes.com/map/route"
    params = {'SB': { 'start':'Georgetown Pike', 'end':'S Van Dorn St'},
              'NB': { 'start':'S Van Dorn St', 'end':'Georgetown Pike'},
    }
    resp = requests.get(url=apiurl, params=params['SB'])
    data = json.loads(resp.content)
    
    pprint.pprint(data)
    
    # Write output file
    #fout = open(options.output_file, "wb")
    with open(options.output_file, "a") as fout:
        
        # Unicode compatability required for Excel, but this breaks ISEBOX
        #fout.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
        
        #csv_fout = csv.DictWriter(fout, fieldnames=FIELDS, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE)
        csv_fout = csv.DictWriter(fout, fieldnames=FIELDS, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        csv_fout.writeheader()
        
        
        # Get Soutbound Traffic
        
        
        # Get Northbound Traffic
        
        
        
        
        for point in data['query']['geosearch']:
            
            print "%s (%s)" % (point['title'], point['pageid'])
            
            # Query for info about this particular article
            params2 = {'action':'query',
                      'pageids':point['pageid'],
                      #'prop':'info|revisions',
                      'prop':'info|extracts',
                      'inprop':'url',
                      #'rvprop':'content',
                      #'rvsection':0,
                      #'rvparse':'',
                      #'exintro':'',
                      'exchars':525,
                      'format':'json'
            }
            
            resp2 = requests.get(url=apiurl, params=params2)

            print resp2.url
            
            #print "************\n%s\n*****************" % resp2.content

            article = json.loads(resp2.content)

            #pprint.pprint(article)
            #pprint.pprint(article['query']['pages']['40593053'])
            
            point['url'] = "<a href='%s' target='_blank'>Source</a>" % article['query']['pages'][str(point['pageid'])]['fullurl']
            #content = article['query']['pages'][str(point['pageid'])]['revisions'][0]['*']
            content = article['query']['pages'][str(point['pageid'])]['extract']
            
            # Shrink some of the headers
            content = content.replace("<h2>", "<b>")
            content = content.replace("</h2>", "</b>")
            
            #pprint.pprint(content)
            
            #point['description'] = text2html(content)
            point['description'] = content
            #point['description'] = url
            point['date'] = article['query']['pages'][str(point['pageid'])]['touched']
            
            point['icon'] = icon
            
            #csv_fout.writerow(point)
            csv_fout.writerow( {k:unicode(v).encode('utf8') for k,v in point.items()} )
            #exit()


def get_options():
    parser = OptionParser()
    parser.add_option("-o", "--output", dest="output_file", action="store", 
                      help="required output file")
    
    (options, args) = parser.parse_args()

    if not options.output_file:
        parser.print_help()
        sys.exit(1)
        
    return (options, args)

if __name__ == "__main__":
    main()