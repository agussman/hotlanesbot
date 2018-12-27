#!/usr/bin/env python3
import sys
import json

'''
Take the output of https://www.expresslanes.com/themes/custom/transurbangroup/js/on-the-road/entry_exit.js?v=1.x

Manually clean it to extract the json

Run this script to convert it into the condensed version for running with the scraper.
'''

# Assume this file is located nearby
# TODO: Convert to pulling and cleaning it directly
JSON_EXITS = "./data/entry_exit.json"

# drop the last two characters of the id
def clean_id(exit_id):
    #return exit_id
    return exit_id[:-2]


def main():

    # A dict
    # Key are exit ids
    # Values are downstream exit ids
    results = {}
    with open(JSON_EXITS) as f:
        exits = json.load(f)

        for direction, content in exits.items():
            #print(direction)
            for key, entry in content["entries"].items():
                entry_id = clean_id(entry["id"])
                if entry_id in results:
                    # UPDATE: You will see this happens because we're "cleaning" the ids
                    # sys.exit("Unexpectedly saw the same entry id ({}) twice. Aborting.".format(entry_id))
                    continue
                else:
                    results[entry_id] = []
                for exit_obj in entry["exits"]:
                    exit_id = clean_id(exit_obj["id"])
                    if exit_id not in results[entry_id]:
                        results[entry_id].append(exit_id)
                    else:
                        # Okay, this really shouldn't happen
                        sys.exit("Should not have seen a duplicate exit_id {}".format(exit_id))
    
    print(json.dumps(results, indent=4))


                





if __name__ == "__main__":
    # execute only if run as a script
    main()