# Background

# Research
Current Toll data is available from https://www.expresslanes.com/on-the-road

Looking at the Networking activity we submit the form and see a call to:
https://www.expresslanes.com/on-the-road-api?ods%5B%5D=1021

```
{
ods: [
1021
],
rates: [
{
od: "1021",
rate: "1.95",
road: "495",
direction: "N",
duration: "8"
}
]
}
```

Further digging reveals the call:
https://www.expresslanes.com/cache/roadway/entry_exit.js?1457483614

This data files contains all viable exit points for an entry point (e.g., all paths through the network).
It's a little wonky because it's broken up into Northbound and Southbound, it's almost like there's two roads.

Most importantly, it contains the `ods` codes that uniquely identify an Entrance/Exit pair.

Awesome, we can query multiple `ods` prices at a time:
https://www.expresslanes.com/on-the-road-api?ods[]=1038&ods[]=1044&ods[]=1195

Let's grab all the `ods` values with `jq` for style points:
`$ cat data/entry_exit.json | jq '.[] | .[] | .[] | .exits | .[] | .ods | .[]'`

I have some suspicions if that's actually working, because the count doesn't really match this grep:
```
$ cat data/entry_exit.json | jq '.[] | .[] | .[] | .exits | .[] | .ods | .[]' | wc -l
jq: error (at <stdin>:3383): Cannot iterate over null (null)
     264
$ cat data/entry_exit.json | grep ods | wc -l
     348
```

Time for a quick ~python script~ grep hack:
```
$ cat data/entry_exit.json | grep -A 3 ods | grep -o -E '\d{4}' | sort -n | uniq > data/ods.txt
$ wc -l data/ods.txt
     174 data/ods.txt
```
     
Kickstart that into a python scrip to perform the query:
`$ for i in `cat data/ods.txt`; do echo \"$i\",; done > util/query_ods.py`

Script to test it:

Output looks like:
```
{u'direction': u'N',
 u'dt': '2017-10-09 02:45:05',
 u'duration': u'7',
 u'od': u'1011',
 u'rate': u'1.40',
 u'road': u'495'}
 ```


Want it to run as a lambda function.

Store in?
- DynamoDB

DynamoDB
* Fully managed NoSQL (MongoDB): HA, scaling
* Sync'd across AZ within Region
* Dev specifies table throughput
* Document and Key/Value
* Can use SSL
* Use case: User session data

Also, has a pretty sweet free usage tier

Mostly following this:
https://aws.amazon.com/blogs/big-data/analyze-a-time-series-in-real-time-with-aws-lambda-amazon-kinesis-and-amazon-dynamodb-streams/

Anti-Pattern section here is good:
https://aws.amazon.com/blogs/database/choosing-the-right-dynamodb-partition-key/

A little unintuitive, but we need to use Strings for timestamps:
http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html#HowItWorks.DataTypes

DynamoDB does NOT allow searching across just the Range key???
https://stackoverflow.com/a/14838088/3175343


# Logged into AWS Console and created the DynamoDB Table:
Name: Rates
partition key: od
sort key: dt

Unchecked default box
Added a Global Secondary Index on dt (aka dt-index), including all

It's creating for me: New role: DynamoDBAutoscaleRole

# Create an IAM Role for the Lambda function to use to write to the DynamoDB table

Using the existing AmazonDynamoDBFullAccess policy (TODO: restrict to just the Table)

Role name: LambdaToDynamo
Write data to DynamoDb

# Configure AWS CLI locally

If you've never done this before, it should be pretty straight forward (link to docs).

For me this was a little wonky because I have different AWS credentials for work and personal use. In switching,
I ran both `$ aws configure` and edited `~/.aws/credentials`, but the changes didn't seem to take right away.

To confirm your environment is setup correctly, run:

```
$ aws iam get-user
```

and (from the 'util' dir):

```
$ ipython
In [1]: import boto3

In [2]: ddb = boto3.resource("dynamodb")

In [3]: table = ddb.Table("Rates")

In [4]: table.item_count
Out[4]: 0
```


# Create the Lambda function

Create from canary
Name: PollODS
Existing Role > LambdaToDynamo

lambda_function.lambda_handler

Useful reference on the DynamoDB `put_item` call:
http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html#DynamoDB.Client.put_item

Upload to an S3 bucket:
Way more of a PITA than it should be.

You have to create a .zip and the .py needs to be in the base of the zip:

```
util $ zip -r ../app.zip *
```

The lambda handler needs to be set to `<filebasename>.<function>`. In our case that's `lambda_function.lambda_handler`.


If it doesn't show you the Python content then it can't find the function. There could be a typo in the lambda handler, 
a structural issue in the zip, or really anything. It is finicky and incomprehensible.
You'll also get this  message if one of your imports is missing:

 ```
 {
  "errorMessage": "Unable to import module 'lambda_function'"
}
```

So, after some trial an error, it's clear our dumb thing is failing because it's missing the `requests` library.

Instructions on creating a deploymnent package:
http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html

Which even include `requests` in the example (telling).

Because I'm on a Mac and not using a virtualenv, I need to create a `setup.cfg` in the deployment directory:
```
[install]
prefix= 
```
 
And then installed it with:
`$ pip install requests -t $PWD`

# Testing
Configure test events
Create new test event
Event template: Scheduled Event
Give it a name: TestScheduledEvent
Click Test

A couple of notes to be aware of:
 * This test is actually going to run the code, which means it will insert data into the database (or do anything else which might cost you $$$)
 * Timezones are a thing! Running the code locally (EST) will give you a different time than on lambda (UTC)

# Scheduling

Next to "Configuration" above where it's (not) showing your code, click on "Triggers".
Add trigger > Cloudwatch Events
Rule description: Run every 5 minutes
Schedule expression `rate(5 minutes)`

To view the rule, go to CloudWatch > Events > Rules

After doing this, if you're wondering why it looks like your Lambda function isn't running, it might be because it's Disabled.
This can be confusing, because the Trigger will list Rule state: Enabled, but the button will say "Disabled".
<insert image>


Notes on scheduling the timing of the Lambda function:
http://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-create-function.html
http://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-schedule-expressions.html

NOTE: Rate cannot be < 1 minute. (Don't worry, you can always add a `while DDOS == True` and you'll be set)

Lambda Best Practices:
http://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
"To have full control of the dependencies your function uses, we recommend packaging all your dependencies with your deployment package."


https://aws.amazon.com/dynamodb/iot/


# Querying the data

Going to use Amazon API Gateway to get it back out
Helpful tutorial here: https://aws.amazon.com/blogs/compute/using-amazon-api-gateway-as-a-proxy-for-dynamodb/

API Gateway > Create API > 
API name
Description

Create Resource

BEFORE THE API GATEWAY
probably need an IAM read user?
Also, what's my query? Figure that out first. I think Querying everything within the last 5 minutes would do it? SHould only be one run
There doesn't seem to be an easy way to say "WHERE TIMESTAMP=MAX(TIMESTAMP)"




# Creating another Lambda function

As of 2017/12/04 there are new dynamic tolls on I-66 inside the beltway. Tolling information is available from https://vai66tolls.com/. 

The format on this is slightly different, as tolls are only active from 5:30 AM to 9:30 AM Weekdays Eastbound and 3:00 PM to 7:00 PM Weekdays Westbound.

Important seeming variables:
```
Dir:rbEast
txtRunRefresh:
txtCurrentDate:01/02/2018
txtCurrentTime:11:08 PM
txtCurrentDateUnix:1514952543802
ddlExitAfterSel:4
datepicker:01/02/2018
timepicker:5 : 30 am
ddlEntryInterch:1
ddlExitInterch:16
```


In the response, the relevant portion is:
```html
<span id="spanTollAmt" class="data-txt">$7.75</span>
```

This is an ASP.net page and maintaining VIEWSTATE, cookies, etc is beyond the ken of requests. We're going to switch to `scrapy`.
Good reference: https://blog.scrapinghub.com/2016/04/20/scrapy-tips-from-the-pros-april-2016-edition/

`$ pip install scrapy`

Using 1.5.0 for this.

`$ scrapy startproject vai66tolls`

Need to enable Cookies in settings.py:

```
# see https://stackoverflow.com/questions/41942879/scrapy-missing-cookies-in-response
# https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
COOKIES_ENABLED = True
COOKIES_DEBUG = True

DOWNLOADER_MIDDLEWARES = {
  'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700
}
```


Going to do what I should have done initially and create a virualenv
`$ mkvirtualenv hotlanesbot`

Installing scrapy (note this, failed the first time I ran it on an error w/ `cryptography` having to do with `python < 3`, but it was fun on a re-run):
`$ pip install --target=$PWD scrapy`
`$ pip install service_identity`
`$ pip install --target=$PWD service_identity`
`$ pip install --upgrade google-auth-oauthlib`
`$ pip install Scrapy` <-- this is what mattered to get rid of the opentype error
then:
`(hotlanesbot)tollspider $ scrapy startproject vai66tolls`

`(hotlanesbot)tollspider $ cd vai66tolls/`
`(hotlanesbot)vai66tolls $ scrapy genspider vai66tolls-spider vai66tolls.com`






ElasticCache - in-memory data store
* Redis
* Memcached
- ElasticCache/Redis
https://aws.amazon.com/elasticache/redis/

- ??

Redshift
* petabyte-scale data warehouse for BI
    * hRedshift columns = 1024kb
* Supports SQL tools w/ ODBC/JDBC connections (Postgres-based)
* Columnar data store
* Monitors and backups data, can enable encryption

Kinesis
* Collect data from multiple Producers, maintains order
* "Stream" 
    * Preserves for 24hrs default, 7 days max
    * Data blob can be 1 MB
* Run SQL queries on streaming data
* Emit from Kensis Streams to S3, Redshift, EMR, Lambda (Consumers)
* Scale across multiple shards
* Aggregation refers to the storage of multiple records in a Streams record







curl 'https://vai66tolls.com/' -H 'cookie: ASP.NET_SessionId=up5ygvcjzjalnw2z1r1e0qeg' -H 'origin: https://vai66tolls.com' -H 'accept-encoding: gzip, deflate, br' -H 'accept-language: en-US,en;q=0.9' -H 'x-requested-with: XMLHttpRequest' -H 'x-microsoftajax: Delta=true' -H 'pragma: no-cache' -H 'cache-control: no-cache' -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36' -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' -H 'accept: */*' -H 'referer: https://vai66tolls.com/' -H 'authority: vai66tolls.com' --data 'sm1=sm1%7CbtnUpdateEndSel&txtProjectionsEast=%7B%22data%22%3A%7B%221%22%3A%7B%22x%22%3A72.59275022218935%2C%22y%22%3A507.1073907732498%2C%22hash%22%3A-924004836%7D%2C%222%22%3A%7B%22x%22%3A151.12526720005553%2C%22y%22%3A472.97412396094296%2C%22hash%22%3A1753858769%7D%2C%223%22%3A%7B%22x%22%3A130.62560640019365%2C%22y%22%3A484.4094988727011%2C%22hash%22%3A172829413%7D%2C%224%22%3A%7B%22x%22%3A319.9401777777821%2C%22y%22%3A371.0102966551203%2C%22hash%22%3A750498074%7D%2C%225%22%3A%7B%22x%22%3A196.9247367110802%2C%22y%22%3A144.3040254295338%2C%22hash%22%3A1022995839%7D%2C%226%22%3A%7B%22x%22%3A348.2517297777813%2C%22y%22%3A376.95367120276205%2C%22hash%22%3A-754168337%7D%2C%227%22%3A%7B%22x%22%3A233.83461191132665%2C%22y%22%3A159.02639861032367%2C%22hash%22%3A82753581%7D%2C%228%22%3A%7B%22x%22%3A532.1603093333542%2C%22y%22%3A493.26276484993286%2C%22hash%22%3A228155854%7D%2C%229%22%3A%7B%22x%22%3A745.5746524446877%2C%22y%22%3A466.82226947823074%2C%22hash%22%3A1006370368%7D%7D%7D&txtProjectionsWest=%7B%22data%22%3A%7B%224%22%3A%7B%22x%22%3A273.6397219556384%2C%22y%22%3A378.9821881093085%2C%22hash%22%3A-223921119%7D%2C%2211%22%3A%7B%22x%22%3A450.3364287998993%2C%22y%22%3A435.350902762264%2C%22hash%22%3A-138389322%7D%2C%2212%22%3A%7B%22x%22%3A694.0138403554447%2C%22y%22%3A517.4868819864932%2C%22hash%22%3A1112146227%7D%2C%2213%22%3A%7B%22x%22%3A831.2607879112475%2C%22y%22%3A422.5148401792394%2C%22hash%22%3A-2074711502%7D%2C%2215%22%3A%7B%22x%22%3A1020.6685660445364%2C%22y%22%3A404.6635906677693%2C%22hash%22%3A-414990012%7D%2C%2216%22%3A%7B%22x%22%3A1094.7562858667225%2C%22y%22%3A426.1448951404309%2C%22hash%22%3A-337587764%7D%2C%2217%22%3A%7B%22x%22%3A924.8112433778588%2C%22y%22%3A393.69806051591877%2C%22hash%22%3A-1568430654%7D%7D%7D&txtProjectionsExits=%7B%22data%22%3A%7B%221%22%3A%7B%22x%22%3A71.70728604472242%2C%22y%22%3A505.2439999540802%2C%22hash%22%3A-1582594562%7D%2C%224%22%3A%7B%22x%22%3A257.101348266704%2C%22y%22%3A395.53938718442805%2C%22hash%22%3A-709005436%7D%2C%225%22%3A%7B%22x%22%3A177.8930823111441%2C%22y%22%3A450.0577305065235%2C%22hash%22%3A-31229911%7D%2C%226%22%3A%7B%22x%22%3A354.1645333333872%2C%22y%22%3A375%2C%22hash%22%3A-612407673%7D%2C%228%22%3A%7B%22x%22%3A535.5215779556893%2C%22y%22%3A490.9877215634333%2C%22hash%22%3A916792536%7D%2C%229%22%3A%7B%22x%22%3A752.6700167113449%2C%22y%22%3A462.11478044162504%2C%22hash%22%3A959379390%7D%2C%2210%22%3A%7B%22x%22%3A442.1633614222519%2C%22y%22%3A432.25231311819516%2C%22hash%22%3A-82483650%7D%2C%2211%22%3A%7B%22x%22%3A460.13478897779714%2C%22y%22%3A451.01571840327233%2C%22hash%22%3A2123083794%7D%2C%2212%22%3A%7B%22x%22%3A698.6858289778465%2C%22y%22%3A517.3521818842273%2C%22hash%22%3A1165055615%7D%2C%2213%22%3A%7B%22x%22%3A831.6685674667824%2C%22y%22%3A426.79605701658875%2C%22hash%22%3A1830473341%7D%2C%2214%22%3A%7B%22x%22%3A922.7257422222756%2C%22y%22%3A394.40165763814%2C%22hash%22%3A718080043%7D%2C%2215%22%3A%7B%22x%22%3A1023.7152618666878%2C%22y%22%3A421.27986737631727%2C%22hash%22%3A-668718683%7D%2C%2216%22%3A%7B%22x%22%3A1095.4203840000555%2C%22y%22%3A427.67175621306524%2C%22hash%22%3A-872142550%7D%7D%7D&Dir=rbEast&txtRunRefresh=&txtCurrentDate=01%2F02%2F2018&txtCurrentTime=11%3A18%20PM&txtCurrentDateUnix=1514953180846&ddlExitAfterSel=10&datepicker=01%2F02%2F2018&timepicker=5%20%3A%2030%20am&ddlEntryInterch=4&ddlExitInterch=16&__EVENTTARGET=&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=rc9NXGggkJTID%2B%2BnzWGy3gydwOtuVFIwvIneOjLEHkzWPjWBcQO3AnzgcNFS9rElcbMouoB%2FtKxzM6YUPU19yZol5mlmy1adjMqNLDt2%2BOe%2Bno%2Fsk%2BQndevnaKLdsQlG%2FNYtl4ZcqSAH5iVxWGR0RREAsqD6sn2Z1FSbTDAuMEVUwAx5eUT36cbvZUWVyN567CMNzKrJ5KKY6kGlrK2aZgONB9Mb%2BojiRZN7gccASaBkqBJMpo9a%2FAcW8opHnw5OMbZ7h%2F7Ikro%2FcF%2B9zEOfy%2Flk7FhHF%2Bm1cTkxWZYJQxKLi9qVLtB2fdzHM%2F%2FfzP%2F61ad%2Bi3LW8EWs1g%2FEYyokG44B%2FgPr8E5tP1%2FqFOOESdPsplAFf0OS64baTsIozf6Eqw5i8FJgeIUYukBlsUpKDwjf2DoTt6Fr6Jd9fSY%2Fcrsde6wd5Wmss%2Fo70mgHcAILToQYffVeSQ0LP401dAKIUVekf9yWeaeGL0hfkaRjtdiTILFZsXA7GRXTTucMPkcplCOYZ4Gg9g8a9R5fUdqJ7oIfGBH6QJvOsH1V5XLQvGbGV1smJ%2BEgMeeAuomY%2FCNhlygWFkuWuHIWR1%2FoLn%2FBqNd3CEb4G4uiRkwI32FoKD80oFKjGR7o91yJFvRpG1cD0JsCAO2iBDiXjxJbTY54QHZmG2BzmaPJDYxu1NJQaCRX8fKorggmk3uv3upW6KZi%2Fgy2TFVharTNbX7hE0jxltuCl%2BWK92U2jyvzhpsYUkHRTMkH44gUO1OdzbAp1s7UUzBTVfEpTagDrjGSDFbQENHuRoOn47xwfRQCFaqHGTtZ0XtLxBJXvD%2FflaRWL9pF6ldvVEVFLNcIPEoz72J2vrkPsNnEGnqryIph7M53U8DSH8zQbXdKOLfAPyNShW%2B3vv565%2FAhlmrOd9KY9ORj24ze3%2BBpsPN9F4614jvGz8RcD%2F6emlLgEHZ8Z5DpABJRZ2UMQUo9N8X0O%2FND6QYCfMJg7sYerrioeKMrQFHYG%2FQB6%2FzTBsRq6N2pYwJxLbvwLqMoIvxXi3KUGQN7PbwfhSRnOW%2BBZz9buupf9F44JnVbMUccTuhEx8JjThBsEI%2FTVRfgupifltvQuqmsvR1shp%2FkpzPIub8MFmCMe5XYILAEaBO245Fa%2B2fait0HSyfFsT79ALcDYu5NzUjto4ocGd0hG%2BHzdd7gLcv45%2BhDsK7h97IU%2BaEtFpFhM%2Bg7F1ooPfswML%2BD0eMVtKhfJnE3rfBTJFJuB2OIktRxKAx7e2VbGY%2FQqRLWIo34aoW5Hb%2FQ9MGEPwEXnKU%2BjIYIxNXwz7C124IUsGX%2Bcgj1zVMU%2F%2BU%3D&__VIEWSTATEGENERATOR=CA0B0334&__EVENTVALIDATION=jO00uzCpIbOvWI6%2FdAy977GQMP%2BJFkDAZ%2FpkcGqoswAoWpHqI7dK9oV1VD2kwcGfyIxw2GBEFefXEysOgBcJ3DDxMqgpWGIvFL8nWXaWWQptgX3nJhAwFi1dLm4yLGj2ZxF22P7017dSyv3F9SUSrek%2Bz1Xymu88hdEAbkJG5IN3j9p4hmGjXQrgxEMaxfWm6rtvob6yOCKnsanXrIFQVHclHEzMLeqBjKnW3wNRG0ciKn2PBkq8nNje6TMLFwBFh3UZgA%2BO8thwkIIAH1j4fc94WGOe%2BCh0OOzs%2FZiwuAxbOmmqIhERH6ZBIofrayL2qQr23VOvABHz3UkSJjCt0FfO9WJuzSRFtBfVGw7RAoG8nDgn0ZtADtsLW76yC5Ipx3gfTQlM%2FyoCbZbMrvP%2F1IUlcbDZP4M1JdKLnIAXanr2jZAJRegInKMzPGf2FSB0GtH1mnN784h6LFNmWnW4XLVPF3yEkfVzrFU9Xc2eWVF2wh0jy49jE0S6iQVAgxSCvIV2%2B1M7BJi7WGqhyAnuZxA5DQMRqwcHvOdJr5l1EBfdH06INu6P1GVhBl%2BWqMl11JALvcCcQNVMnCtpWMmmacWyDFeGJ9mEF92LgyG31vCbNsFDL1bHG61fMMLEY1fEx6iY1kfQ11pM5HIlwmIakfPuVSaLZnGA5J0B%2B4b9wMxZsz4a0NZzPvGBEpufn69Z95wyUS3EECGXAX7o%2Bm9L78MwCfnY8Q4QapZleyEoFYmtQY9Txf57L1hhxxA28pxehrD6b3KrQfPDhUJk91JB0fP5w43ZF9hojx9SKWGyBqxNh85a5UvuqzrFzw2iM434AabREDWoCQgdZIkeLqnUcGdotxbeheghqy6QOUgTrZTbpaJDoNaYCliALPjdTHPyWzglNWl4oeW5XZLvSUYBVvyTMAbg7HPcA1gHd2QP5ZVBKWon0r8ErGoQVOLrEjYe&__ASYNCPOST=true&btnUpdateEndSel=Select%20this%20Exit' --compressed

curl 'https://vai66tolls.com/'  -H 'origin: https://vai66tolls.com' -H 'accept-encoding: gzip, deflate, br' -H 'accept-language: en-US,en;q=0.9' -H 'x-requested-with: XMLHttpRequest' -H 'x-microsoftajax: Delta=true' -H 'pragma: no-cache' -H 'cache-control: no-cache' -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36' -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' -H 'accept: */*' -H 'referer: https://vai66tolls.com/' -H 'authority: vai66tolls.com' --data 'sm1=sm1%7CbtnUpdateEndSel&txtProjectionsEast=%7B%22data%22%3A%7B%221%22%3A%7B%22x%22%3A72.59275022218935%2C%22y%22%3A507.1073907732498%2C%22hash%22%3A-924004836%7D%2C%222%22%3A%7B%22x%22%3A151.12526720005553%2C%22y%22%3A472.97412396094296%2C%22hash%22%3A1753858769%7D%2C%223%22%3A%7B%22x%22%3A130.62560640019365%2C%22y%22%3A484.4094988727011%2C%22hash%22%3A172829413%7D%2C%224%22%3A%7B%22x%22%3A319.9401777777821%2C%22y%22%3A371.0102966551203%2C%22hash%22%3A750498074%7D%2C%225%22%3A%7B%22x%22%3A196.9247367110802%2C%22y%22%3A144.3040254295338%2C%22hash%22%3A1022995839%7D%2C%226%22%3A%7B%22x%22%3A348.2517297777813%2C%22y%22%3A376.95367120276205%2C%22hash%22%3A-754168337%7D%2C%227%22%3A%7B%22x%22%3A233.83461191132665%2C%22y%22%3A159.02639861032367%2C%22hash%22%3A82753581%7D%2C%228%22%3A%7B%22x%22%3A532.1603093333542%2C%22y%22%3A493.26276484993286%2C%22hash%22%3A228155854%7D%2C%229%22%3A%7B%22x%22%3A745.5746524446877%2C%22y%22%3A466.82226947823074%2C%22hash%22%3A1006370368%7D%7D%7D&txtProjectionsWest=%7B%22data%22%3A%7B%224%22%3A%7B%22x%22%3A273.6397219556384%2C%22y%22%3A378.9821881093085%2C%22hash%22%3A-223921119%7D%2C%2211%22%3A%7B%22x%22%3A450.3364287998993%2C%22y%22%3A435.350902762264%2C%22hash%22%3A-138389322%7D%2C%2212%22%3A%7B%22x%22%3A694.0138403554447%2C%22y%22%3A517.4868819864932%2C%22hash%22%3A1112146227%7D%2C%2213%22%3A%7B%22x%22%3A831.2607879112475%2C%22y%22%3A422.5148401792394%2C%22hash%22%3A-2074711502%7D%2C%2215%22%3A%7B%22x%22%3A1020.6685660445364%2C%22y%22%3A404.6635906677693%2C%22hash%22%3A-414990012%7D%2C%2216%22%3A%7B%22x%22%3A1094.7562858667225%2C%22y%22%3A426.1448951404309%2C%22hash%22%3A-337587764%7D%2C%2217%22%3A%7B%22x%22%3A924.8112433778588%2C%22y%22%3A393.69806051591877%2C%22hash%22%3A-1568430654%7D%7D%7D&txtProjectionsExits=%7B%22data%22%3A%7B%221%22%3A%7B%22x%22%3A71.70728604472242%2C%22y%22%3A505.2439999540802%2C%22hash%22%3A-1582594562%7D%2C%224%22%3A%7B%22x%22%3A257.101348266704%2C%22y%22%3A395.53938718442805%2C%22hash%22%3A-709005436%7D%2C%225%22%3A%7B%22x%22%3A177.8930823111441%2C%22y%22%3A450.0577305065235%2C%22hash%22%3A-31229911%7D%2C%226%22%3A%7B%22x%22%3A354.1645333333872%2C%22y%22%3A375%2C%22hash%22%3A-612407673%7D%2C%228%22%3A%7B%22x%22%3A535.5215779556893%2C%22y%22%3A490.9877215634333%2C%22hash%22%3A916792536%7D%2C%229%22%3A%7B%22x%22%3A752.6700167113449%2C%22y%22%3A462.11478044162504%2C%22hash%22%3A959379390%7D%2C%2210%22%3A%7B%22x%22%3A442.1633614222519%2C%22y%22%3A432.25231311819516%2C%22hash%22%3A-82483650%7D%2C%2211%22%3A%7B%22x%22%3A460.13478897779714%2C%22y%22%3A451.01571840327233%2C%22hash%22%3A2123083794%7D%2C%2212%22%3A%7B%22x%22%3A698.6858289778465%2C%22y%22%3A517.3521818842273%2C%22hash%22%3A1165055615%7D%2C%2213%22%3A%7B%22x%22%3A831.6685674667824%2C%22y%22%3A426.79605701658875%2C%22hash%22%3A1830473341%7D%2C%2214%22%3A%7B%22x%22%3A922.7257422222756%2C%22y%22%3A394.40165763814%2C%22hash%22%3A718080043%7D%2C%2215%22%3A%7B%22x%22%3A1023.7152618666878%2C%22y%22%3A421.27986737631727%2C%22hash%22%3A-668718683%7D%2C%2216%22%3A%7B%22x%22%3A1095.4203840000555%2C%22y%22%3A427.67175621306524%2C%22hash%22%3A-872142550%7D%7D%7D&Dir=rbEast&txtRunRefresh=&txtCurrentDate=01%2F02%2F2018&txtCurrentTime=11%3A18%20PM&txtCurrentDateUnix=1514953180846&ddlExitAfterSel=10&datepicker=01%2F02%2F2018&timepicker=5%20%3A%2030%20am&ddlEntryInterch=4&ddlExitInterch=16&__EVENTTARGET=&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=rc9NXGggkJTID%2B%2BnzWGy3gydwOtuVFIwvIneOjLEHkzWPjWBcQO3AnzgcNFS9rElcbMouoB%2FtKxzM6YUPU19yZol5mlmy1adjMqNLDt2%2BOe%2Bno%2Fsk%2BQndevnaKLdsQlG%2FNYtl4ZcqSAH5iVxWGR0RREAsqD6sn2Z1FSbTDAuMEVUwAx5eUT36cbvZUWVyN567CMNzKrJ5KKY6kGlrK2aZgONB9Mb%2BojiRZN7gccASaBkqBJMpo9a%2FAcW8opHnw5OMbZ7h%2F7Ikro%2FcF%2B9zEOfy%2Flk7FhHF%2Bm1cTkxWZYJQxKLi9qVLtB2fdzHM%2F%2FfzP%2F61ad%2Bi3LW8EWs1g%2FEYyokG44B%2FgPr8E5tP1%2FqFOOESdPsplAFf0OS64baTsIozf6Eqw5i8FJgeIUYukBlsUpKDwjf2DoTt6Fr6Jd9fSY%2Fcrsde6wd5Wmss%2Fo70mgHcAILToQYffVeSQ0LP401dAKIUVekf9yWeaeGL0hfkaRjtdiTILFZsXA7GRXTTucMPkcplCOYZ4Gg9g8a9R5fUdqJ7oIfGBH6QJvOsH1V5XLQvGbGV1smJ%2BEgMeeAuomY%2FCNhlygWFkuWuHIWR1%2FoLn%2FBqNd3CEb4G4uiRkwI32FoKD80oFKjGR7o91yJFvRpG1cD0JsCAO2iBDiXjxJbTY54QHZmG2BzmaPJDYxu1NJQaCRX8fKorggmk3uv3upW6KZi%2Fgy2TFVharTNbX7hE0jxltuCl%2BWK92U2jyvzhpsYUkHRTMkH44gUO1OdzbAp1s7UUzBTVfEpTagDrjGSDFbQENHuRoOn47xwfRQCFaqHGTtZ0XtLxBJXvD%2FflaRWL9pF6ldvVEVFLNcIPEoz72J2vrkPsNnEGnqryIph7M53U8DSH8zQbXdKOLfAPyNShW%2B3vv565%2FAhlmrOd9KY9ORj24ze3%2BBpsPN9F4614jvGz8RcD%2F6emlLgEHZ8Z5DpABJRZ2UMQUo9N8X0O%2FND6QYCfMJg7sYerrioeKMrQFHYG%2FQB6%2FzTBsRq6N2pYwJxLbvwLqMoIvxXi3KUGQN7PbwfhSRnOW%2BBZz9buupf9F44JnVbMUccTuhEx8JjThBsEI%2FTVRfgupifltvQuqmsvR1shp%2FkpzPIub8MFmCMe5XYILAEaBO245Fa%2B2fait0HSyfFsT79ALcDYu5NzUjto4ocGd0hG%2BHzdd7gLcv45%2BhDsK7h97IU%2BaEtFpFhM%2Bg7F1ooPfswML%2BD0eMVtKhfJnE3rfBTJFJuB2OIktRxKAx7e2VbGY%2FQqRLWIo34aoW5Hb%2FQ9MGEPwEXnKU%2BjIYIxNXwz7C124IUsGX%2Bcgj1zVMU%2F%2BU%3D&__VIEWSTATEGENERATOR=CA0B0334&__EVENTVALIDATION=jO00uzCpIbOvWI6%2FdAy977GQMP%2BJFkDAZ%2FpkcGqoswAoWpHqI7dK9oV1VD2kwcGfyIxw2GBEFefXEysOgBcJ3DDxMqgpWGIvFL8nWXaWWQptgX3nJhAwFi1dLm4yLGj2ZxF22P7017dSyv3F9SUSrek%2Bz1Xymu88hdEAbkJG5IN3j9p4hmGjXQrgxEMaxfWm6rtvob6yOCKnsanXrIFQVHclHEzMLeqBjKnW3wNRG0ciKn2PBkq8nNje6TMLFwBFh3UZgA%2BO8thwkIIAH1j4fc94WGOe%2BCh0OOzs%2FZiwuAxbOmmqIhERH6ZBIofrayL2qQr23VOvABHz3UkSJjCt0FfO9WJuzSRFtBfVGw7RAoG8nDgn0ZtADtsLW76yC5Ipx3gfTQlM%2FyoCbZbMrvP%2F1IUlcbDZP4M1JdKLnIAXanr2jZAJRegInKMzPGf2FSB0GtH1mnN784h6LFNmWnW4XLVPF3yEkfVzrFU9Xc2eWVF2wh0jy49jE0S6iQVAgxSCvIV2%2B1M7BJi7WGqhyAnuZxA5DQMRqwcHvOdJr5l1EBfdH06INu6P1GVhBl%2BWqMl11JALvcCcQNVMnCtpWMmmacWyDFeGJ9mEF92LgyG31vCbNsFDL1bHG61fMMLEY1fEx6iY1kfQ11pM5HIlwmIakfPuVSaLZnGA5J0B%2B4b9wMxZsz4a0NZzPvGBEpufn69Z95wyUS3EECGXAX7o%2Bm9L78MwCfnY8Q4QapZleyEoFYmtQY9Txf57L1hhxxA28pxehrD6b3KrQfPDhUJk91JB0fP5w43ZF9hojx9SKWGyBqxNh85a5UvuqzrFzw2iM434AabREDWoCQgdZIkeLqnUcGdotxbeheghqy6QOUgTrZTbpaJDoNaYCliALPjdTHPyWzglNWl4oeW5XZLvSUYBVvyTMAbg7HPcA1gHd2QP5ZVBKWon0r8ErGoQVOLrEjYe&__ASYNCPOST=true&btnUpdateEndSel=Select%20this%20Exit' --compressed


{
  "log": {
    "version": "1.2",
    "creator": {
      "name": "WebInspector",
      "version": "537.36"
    },
    "pages": [
      {
        "startedDateTime": "2018-01-03T04:35:15.936Z",
        "id": "page_19",
        "title": "https://vai66tolls.com/",
        "pageTimings": {
          "onContentLoad": 886.2739999894984,
          "onLoad": 1387.3769999772776
        }
      }
    ],
    "entries": [
      {
        "startedDateTime": "2018-01-03T04:40:01.395Z",
        "time": 103.3325559987861,
        "request": {
          "method": "POST",
          "url": "https://vai66tolls.com/",
          "httpVersion": "http/2.0",
          "headers": [
            {
              "name": "cookie",
              "value": "ASP.NET_SessionId=up5ygvcjzjalnw2z1r1e0qeg"
            },
            {
              "name": "origin",
              "value": "https://vai66tolls.com"
            },
            {
              "name": "accept-encoding",
              "value": "gzip, deflate, br"
            },
            {
              "name": "accept-language",
              "value": "en-US,en;q=0.9"
            },
            {
              "name": "x-requested-with",
              "value": "XMLHttpRequest"
            },
            {
              "name": "x-microsoftajax",
              "value": "Delta=true"
            },
            {
              "name": "content-length",
              "value": "5739"
            },
            {
              "name": ":path",
              "value": "/"
            },
            {
              "name": "pragma",
              "value": "no-cache"
            },
            {
              "name": "cache-control",
              "value": "no-cache"
            },
            {
              "name": "user-agent",
              "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
            },
            {
              "name": "content-type",
              "value": "application/x-www-form-urlencoded; charset=UTF-8"
            },
            {
              "name": "accept",
              "value": "*/*"
            },
            {
              "name": "referer",
              "value": "https://vai66tolls.com/"
            },
            {
              "name": ":authority",
              "value": "vai66tolls.com"
            },
            {
              "name": ":scheme",
              "value": "https"
            },
            {
              "name": ":method",
              "value": "POST"
            }
          ],
          "queryString": [],
          "cookies": [
            {
              "name": "ASP.NET_SessionId",
              "value": "up5ygvcjzjalnw2z1r1e0qeg",
              "expires": null,
              "httpOnly": false,
              "secure": false
            }
          ],
          "headersSize": -1,
          "bodySize": 5739,
          "postData": {
            "mimeType": "application/x-www-form-urlencoded; charset=UTF-8",
            "text": "sm1=sm1%7CbtnUpdateEndSel&txtProjectionsEast=%7B%22data%22%3A%7B%221%22%3A%7B%22x%22%3A72.59275022218935%2C%22y%22%3A507.1073907732498%2C%22hash%22%3A-924004836%7D%2C%222%22%3A%7B%22x%22%3A151.12526720005553%2C%22y%22%3A472.97412396094296%2C%22hash%22%3A1753858769%7D%2C%223%22%3A%7B%22x%22%3A130.62560640019365%2C%22y%22%3A484.4094988727011%2C%22hash%22%3A172829413%7D%2C%224%22%3A%7B%22x%22%3A319.9401777777821%2C%22y%22%3A371.0102966551203%2C%22hash%22%3A750498074%7D%2C%225%22%3A%7B%22x%22%3A196.9247367110802%2C%22y%22%3A144.3040254295338%2C%22hash%22%3A1022995839%7D%2C%226%22%3A%7B%22x%22%3A348.2517297777813%2C%22y%22%3A376.95367120276205%2C%22hash%22%3A-754168337%7D%2C%227%22%3A%7B%22x%22%3A233.83461191132665%2C%22y%22%3A159.02639861032367%2C%22hash%22%3A82753581%7D%2C%228%22%3A%7B%22x%22%3A532.1603093333542%2C%22y%22%3A493.26276484993286%2C%22hash%22%3A228155854%7D%2C%229%22%3A%7B%22x%22%3A745.5746524446877%2C%22y%22%3A466.82226947823074%2C%22hash%22%3A1006370368%7D%7D%7D&txtProjectionsWest=%7B%22data%22%3A%7B%224%22%3A%7B%22x%22%3A273.6397219556384%2C%22y%22%3A378.9821881093085%2C%22hash%22%3A-223921119%7D%2C%2211%22%3A%7B%22x%22%3A450.3364287998993%2C%22y%22%3A435.350902762264%2C%22hash%22%3A-138389322%7D%2C%2212%22%3A%7B%22x%22%3A694.0138403554447%2C%22y%22%3A517.4868819864932%2C%22hash%22%3A1112146227%7D%2C%2213%22%3A%7B%22x%22%3A831.2607879112475%2C%22y%22%3A422.5148401792394%2C%22hash%22%3A-2074711502%7D%2C%2215%22%3A%7B%22x%22%3A1020.6685660445364%2C%22y%22%3A404.6635906677693%2C%22hash%22%3A-414990012%7D%2C%2216%22%3A%7B%22x%22%3A1094.7562858667225%2C%22y%22%3A426.1448951404309%2C%22hash%22%3A-337587764%7D%2C%2217%22%3A%7B%22x%22%3A924.8112433778588%2C%22y%22%3A393.69806051591877%2C%22hash%22%3A-1568430654%7D%7D%7D&txtProjectionsExits=%7B%22data%22%3A%7B%221%22%3A%7B%22x%22%3A71.70728604472242%2C%22y%22%3A505.2439999540802%2C%22hash%22%3A-1582594562%7D%2C%224%22%3A%7B%22x%22%3A290.25965155567974%2C%22y%22%3A368.442798177246%2C%22hash%22%3A2116900292%7D%2C%225%22%3A%7B%22x%22%3A177.8930823111441%2C%22y%22%3A450.0577305065235%2C%22hash%22%3A-31229911%7D%2C%226%22%3A%7B%22x%22%3A354.1645333333872%2C%22y%22%3A375%2C%22hash%22%3A-612407673%7D%2C%228%22%3A%7B%22x%22%3A535.5215779556893%2C%22y%22%3A490.9877215634333%2C%22hash%22%3A916792536%7D%2C%229%22%3A%7B%22x%22%3A752.6700167113449%2C%22y%22%3A462.11478044162504%2C%22hash%22%3A959379390%7D%2C%2210%22%3A%7B%22x%22%3A442.1633614222519%2C%22y%22%3A432.25231311819516%2C%22hash%22%3A-82483650%7D%2C%2211%22%3A%7B%22x%22%3A460.13478897779714%2C%22y%22%3A451.01571840327233%2C%22hash%22%3A2123083794%7D%2C%2212%22%3A%7B%22x%22%3A698.6858289778465%2C%22y%22%3A517.3521818842273%2C%22hash%22%3A1165055615%7D%2C%2213%22%3A%7B%22x%22%3A831.6685674667824%2C%22y%22%3A426.79605701658875%2C%22hash%22%3A1830473341%7D%2C%2214%22%3A%7B%22x%22%3A922.7257422222756%2C%22y%22%3A394.40165763814%2C%22hash%22%3A718080043%7D%2C%2215%22%3A%7B%22x%22%3A1023.7152618666878%2C%22y%22%3A421.27986737631727%2C%22hash%22%3A-668718683%7D%2C%2216%22%3A%7B%22x%22%3A1095.4203840000555%2C%22y%22%3A427.67175621306524%2C%22hash%22%3A-872142550%7D%7D%7D&txtRunRefresh=&txtCurrentDate=01%2F02%2F2018&txtCurrentTime=11%3A34%20PM&txtCurrentDateUnix=1514954115942&ddlExitAfterSel=1&datepicker=01%2F02%2F2018&timepicker=6%20%3A%2055%20pm&ddlEntryInterch=16&ddlExitInterch=5&__EVENTTARGET=&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=89uQ6Y%2B4cqsuLwf0Z5%2B95ubuYpXE%2BSRlpmTqbDrx8EqBCWdwo9trYPtSOBCcuX06RpyRt%2BSgA%2Bmzkf7Ch%2BUyagN%2BkJzMccGsDdRiED9AHsk3bLnkRvSOPDzgEC2aYksteGg6LkLdpQyhMS9VgbwAOJarDL9lQPxlQ3bFu1kCkQFaafX1gF8Ze7LHdvV%2F4aj5xbPbHOWSTvbitPvfVVrX1HTDAWJ2Iqt5bmTroA34lkmbFUGuaWhz0QsrERyeDUXG2zHrMUXhLng0eTwQWiEFaV9eUWIaeews0o1TB1K6VkqrfIK3FlbS2OaA3zewb3DtZShYoWAdBgqZ9Xto9m8Zej6rPzGBRBkRXdRUFmTzQMGSpsYye%2F2RgotRFeTS0pUDY1G%2B8NuW2uH0ksH3aoUebxPXlQEtnumzOr3Pcmh5AxLeYEaT6CB1j6zE8kJn25euDGPvWliHsmYm%2FbLrU%2Fvj6dzeel95l%2BVSsjrynSZqivRrrvBBebBeuL8Q3CpVbyiYuRsFnwm2NThmWxf5HKQy%2F%2FHTUxP3lIsjG8yDAbrL7IM6YGrydHmNV1keWv1Yd6tEESIDBCISLVB%2BtGOCQTkCJ23IATkwYKgB5HWopRKAn2dLhckpjaCXCYbtBOC0ZiEJFFzR2brHfid5naWvCdL%2FEv1KapS5CIigtilpP79HxpDem2%2BrmTd6b8UlnFZLtK4ZK0jwDujwZdEMHKw4TSk71koDuJ16%2BGk2mV1kv21Gv4ByPrCQhPYvPnBmOKhNU1xqrX4Fupm74RBCG%2F4d0I0WBXhBLQ3l3hv9T4CIVKokJwBs4pZBbdCkzU67AewQ1QesG6t3NDli5nQfCSmJnj3i06Nur4ReuFZ0tsDpJ44xiqfBvPOfZtkAcYxG0YeEJNG6yoUNoxYtZA66TjVssqzMtCBmLmS7C%2BDPK9iisoY7aut30DRgrSKp7u6eOszCefl2HbixLNpK7%2B%2BbhWTgXNbSNdDR%2BYKHIfD8vMwNjVqxRct3ILg%2Bpa6i8zlqQg8XhoB%2BEApOnA1aChd593HEJ5FGXAejk6rrSB%2FLaYUdl1ckgwTMx9h3IK40ioki1ADN64S3i3TbYrkoZkjjGBXSoItR7oFUStn5mxqfkEIRvYkYMkPx5CRVztI%2BUWXpLowQbzA5dO7sBk6UgQKLyzwNerfKjX2hfDdedQDNn2Kwf%2FktpEoAC9Idni2Xp9mLIPrAB24SykBew%2Fh5j6KvbTxH7GUO0Q%3D%3D&__VIEWSTATEGENERATOR=CA0B0334&__EVENTVALIDATION=MM5%2BmPXtrzOptCKKnqpP8qkg3XYKJDBqcpQay9Rmp5T83v%2FKkrEpAb%2BeNwTZQk28ObogxFbdVGjSM4GH9lwnag9uTvwReObWdTs%2FUuMpaktN0B3ssYExN8LgK%2B%2BV%2BAni3LDd%2BnLflC%2Bv444QHIBO3MjztfPaWB9nCQRa3%2FAJtyV7Jh1PbETtPoNHdo7VDfjJ%2Ft38qT7dKaZ1vcYk88QFmWDHrA4gzF%2FTQjahh2epFlEGYP96xYkPXmdha%2FQBSA4t6MNWgfbBBGPnzbWY9WHhYAKmZVvBQn7StSaiYVvISUldAt8wxuVyPitCPHL0G%2BuK7LcUQ91tMVtmN89e7O03ZPwR4WHJ4UXCjFLmrm56IfmW2ymMvr%2B7niFUWc%2BeRWgiaDmix7BIu1J%2BqaUzboZxq9%2BRwaY%2BsPs9xfoWELMYV%2BqZFLdY%2Bvgp55Dcxpv8Zsyy%2BWvJVMLCJsOqv6gXctzKEzTI61WGNLnfOPP9oETb5jBN8GpMPJ8x9XtBWe6XNd%2FidYUZ0%2F9%2Fhxf0Ca4vG2e1SDwalVbpn7uQFRh11gICx%2Fu3Vk0DRGt5NVcdVCGWf1CkDNTZzBdqLXfafZRciyY7KQCLTpQNyECbMnsqhhA8dk409tNF8GivuxFvzqr0ibvemb18rnxyyl6rMCmTmeCGwVFUM17SbUFJCHxVTYmgdrquxNBECXbLJOAnZxQpQUZyLJ5enCpZ%2B3ltLfROr9lUS9bTCsUkGCBxQSTjOR2MXNV%2Ftz%2FFPMra%2BLTgEUrd99n0a7woVDbO6UMG312GKDuihkeq3qeldCNphPkJYAT0qNWGlahSS6QfI5JN2eptkDwOjsw%2FCY0uCz4hGkRYCKbe2cLqSREf8xBl6VsminGYFLQ%3D&__ASYNCPOST=true&btnUpdateEndSel=Select%20this%20Exit",
            "params": [
              {
                "name": "sm1",
                "value": "sm1%7CbtnUpdateEndSel"
              },
              {
                "name": "txtProjectionsEast",
                "value": "%7B%22data%22%3A%7B%221%22%3A%7B%22x%22%3A72.59275022218935%2C%22y%22%3A507.1073907732498%2C%22hash%22%3A-924004836%7D%2C%222%22%3A%7B%22x%22%3A151.12526720005553%2C%22y%22%3A472.97412396094296%2C%22hash%22%3A1753858769%7D%2C%223%22%3A%7B%22x%22%3A130.62560640019365%2C%22y%22%3A484.4094988727011%2C%22hash%22%3A172829413%7D%2C%224%22%3A%7B%22x%22%3A319.9401777777821%2C%22y%22%3A371.0102966551203%2C%22hash%22%3A750498074%7D%2C%225%22%3A%7B%22x%22%3A196.9247367110802%2C%22y%22%3A144.3040254295338%2C%22hash%22%3A1022995839%7D%2C%226%22%3A%7B%22x%22%3A348.2517297777813%2C%22y%22%3A376.95367120276205%2C%22hash%22%3A-754168337%7D%2C%227%22%3A%7B%22x%22%3A233.83461191132665%2C%22y%22%3A159.02639861032367%2C%22hash%22%3A82753581%7D%2C%228%22%3A%7B%22x%22%3A532.1603093333542%2C%22y%22%3A493.26276484993286%2C%22hash%22%3A228155854%7D%2C%229%22%3A%7B%22x%22%3A745.5746524446877%2C%22y%22%3A466.82226947823074%2C%22hash%22%3A1006370368%7D%7D%7D"
              },
              {
                "name": "txtProjectionsWest",
                "value": "%7B%22data%22%3A%7B%224%22%3A%7B%22x%22%3A273.6397219556384%2C%22y%22%3A378.9821881093085%2C%22hash%22%3A-223921119%7D%2C%2211%22%3A%7B%22x%22%3A450.3364287998993%2C%22y%22%3A435.350902762264%2C%22hash%22%3A-138389322%7D%2C%2212%22%3A%7B%22x%22%3A694.0138403554447%2C%22y%22%3A517.4868819864932%2C%22hash%22%3A1112146227%7D%2C%2213%22%3A%7B%22x%22%3A831.2607879112475%2C%22y%22%3A422.5148401792394%2C%22hash%22%3A-2074711502%7D%2C%2215%22%3A%7B%22x%22%3A1020.6685660445364%2C%22y%22%3A404.6635906677693%2C%22hash%22%3A-414990012%7D%2C%2216%22%3A%7B%22x%22%3A1094.7562858667225%2C%22y%22%3A426.1448951404309%2C%22hash%22%3A-337587764%7D%2C%2217%22%3A%7B%22x%22%3A924.8112433778588%2C%22y%22%3A393.69806051591877%2C%22hash%22%3A-1568430654%7D%7D%7D"
              },
              {
                "name": "txtProjectionsExits",
                "value": "%7B%22data%22%3A%7B%221%22%3A%7B%22x%22%3A71.70728604472242%2C%22y%22%3A505.2439999540802%2C%22hash%22%3A-1582594562%7D%2C%224%22%3A%7B%22x%22%3A290.25965155567974%2C%22y%22%3A368.442798177246%2C%22hash%22%3A2116900292%7D%2C%225%22%3A%7B%22x%22%3A177.8930823111441%2C%22y%22%3A450.0577305065235%2C%22hash%22%3A-31229911%7D%2C%226%22%3A%7B%22x%22%3A354.1645333333872%2C%22y%22%3A375%2C%22hash%22%3A-612407673%7D%2C%228%22%3A%7B%22x%22%3A535.5215779556893%2C%22y%22%3A490.9877215634333%2C%22hash%22%3A916792536%7D%2C%229%22%3A%7B%22x%22%3A752.6700167113449%2C%22y%22%3A462.11478044162504%2C%22hash%22%3A959379390%7D%2C%2210%22%3A%7B%22x%22%3A442.1633614222519%2C%22y%22%3A432.25231311819516%2C%22hash%22%3A-82483650%7D%2C%2211%22%3A%7B%22x%22%3A460.13478897779714%2C%22y%22%3A451.01571840327233%2C%22hash%22%3A2123083794%7D%2C%2212%22%3A%7B%22x%22%3A698.6858289778465%2C%22y%22%3A517.3521818842273%2C%22hash%22%3A1165055615%7D%2C%2213%22%3A%7B%22x%22%3A831.6685674667824%2C%22y%22%3A426.79605701658875%2C%22hash%22%3A1830473341%7D%2C%2214%22%3A%7B%22x%22%3A922.7257422222756%2C%22y%22%3A394.40165763814%2C%22hash%22%3A718080043%7D%2C%2215%22%3A%7B%22x%22%3A1023.7152618666878%2C%22y%22%3A421.27986737631727%2C%22hash%22%3A-668718683%7D%2C%2216%22%3A%7B%22x%22%3A1095.4203840000555%2C%22y%22%3A427.67175621306524%2C%22hash%22%3A-872142550%7D%7D%7D"
              },
              {
                "name": "txtRunRefresh",
                "value": ""
              },
              {
                "name": "txtCurrentDate",
                "value": "01%2F02%2F2018"
              },
              {
                "name": "txtCurrentTime",
                "value": "11%3A34%20PM"
              },
              {
                "name": "txtCurrentDateUnix",
                "value": "1514954115942"
              },
              {
                "name": "ddlExitAfterSel",
                "value": "1"
              },
              {
                "name": "datepicker",
                "value": "01%2F02%2F2018"
              },
              {
                "name": "timepicker",
                "value": "6%20%3A%2055%20pm"
              },
              {
                "name": "ddlEntryInterch",
                "value": "16"
              },
              {
                "name": "ddlExitInterch",
                "value": "5"
              },
              {
                "name": "__EVENTTARGET",
                "value": ""
              },
              {
                "name": "__EVENTARGUMENT",
                "value": ""
              },
              {
                "name": "__LASTFOCUS",
                "value": ""
              },
              {
                "name": "__VIEWSTATE",
                "value": "89uQ6Y%2B4cqsuLwf0Z5%2B95ubuYpXE%2BSRlpmTqbDrx8EqBCWdwo9trYPtSOBCcuX06RpyRt%2BSgA%2Bmzkf7Ch%2BUyagN%2BkJzMccGsDdRiED9AHsk3bLnkRvSOPDzgEC2aYksteGg6LkLdpQyhMS9VgbwAOJarDL9lQPxlQ3bFu1kCkQFaafX1gF8Ze7LHdvV%2F4aj5xbPbHOWSTvbitPvfVVrX1HTDAWJ2Iqt5bmTroA34lkmbFUGuaWhz0QsrERyeDUXG2zHrMUXhLng0eTwQWiEFaV9eUWIaeews0o1TB1K6VkqrfIK3FlbS2OaA3zewb3DtZShYoWAdBgqZ9Xto9m8Zej6rPzGBRBkRXdRUFmTzQMGSpsYye%2F2RgotRFeTS0pUDY1G%2B8NuW2uH0ksH3aoUebxPXlQEtnumzOr3Pcmh5AxLeYEaT6CB1j6zE8kJn25euDGPvWliHsmYm%2FbLrU%2Fvj6dzeel95l%2BVSsjrynSZqivRrrvBBebBeuL8Q3CpVbyiYuRsFnwm2NThmWxf5HKQy%2F%2FHTUxP3lIsjG8yDAbrL7IM6YGrydHmNV1keWv1Yd6tEESIDBCISLVB%2BtGOCQTkCJ23IATkwYKgB5HWopRKAn2dLhckpjaCXCYbtBOC0ZiEJFFzR2brHfid5naWvCdL%2FEv1KapS5CIigtilpP79HxpDem2%2BrmTd6b8UlnFZLtK4ZK0jwDujwZdEMHKw4TSk71koDuJ16%2BGk2mV1kv21Gv4ByPrCQhPYvPnBmOKhNU1xqrX4Fupm74RBCG%2F4d0I0WBXhBLQ3l3hv9T4CIVKokJwBs4pZBbdCkzU67AewQ1QesG6t3NDli5nQfCSmJnj3i06Nur4ReuFZ0tsDpJ44xiqfBvPOfZtkAcYxG0YeEJNG6yoUNoxYtZA66TjVssqzMtCBmLmS7C%2BDPK9iisoY7aut30DRgrSKp7u6eOszCefl2HbixLNpK7%2B%2BbhWTgXNbSNdDR%2BYKHIfD8vMwNjVqxRct3ILg%2Bpa6i8zlqQg8XhoB%2BEApOnA1aChd593HEJ5FGXAejk6rrSB%2FLaYUdl1ckgwTMx9h3IK40ioki1ADN64S3i3TbYrkoZkjjGBXSoItR7oFUStn5mxqfkEIRvYkYMkPx5CRVztI%2BUWXpLowQbzA5dO7sBk6UgQKLyzwNerfKjX2hfDdedQDNn2Kwf%2FktpEoAC9Idni2Xp9mLIPrAB24SykBew%2Fh5j6KvbTxH7GUO0Q%3D%3D"
              },
              {
                "name": "__VIEWSTATEGENERATOR",
                "value": "CA0B0334"
              },
              {
                "name": "__EVENTVALIDATION",
                "value": "MM5%2BmPXtrzOptCKKnqpP8qkg3XYKJDBqcpQay9Rmp5T83v%2FKkrEpAb%2BeNwTZQk28ObogxFbdVGjSM4GH9lwnag9uTvwReObWdTs%2FUuMpaktN0B3ssYExN8LgK%2B%2BV%2BAni3LDd%2BnLflC%2Bv444QHIBO3MjztfPaWB9nCQRa3%2FAJtyV7Jh1PbETtPoNHdo7VDfjJ%2Ft38qT7dKaZ1vcYk88QFmWDHrA4gzF%2FTQjahh2epFlEGYP96xYkPXmdha%2FQBSA4t6MNWgfbBBGPnzbWY9WHhYAKmZVvBQn7StSaiYVvISUldAt8wxuVyPitCPHL0G%2BuK7LcUQ91tMVtmN89e7O03ZPwR4WHJ4UXCjFLmrm56IfmW2ymMvr%2B7niFUWc%2BeRWgiaDmix7BIu1J%2BqaUzboZxq9%2BRwaY%2BsPs9xfoWELMYV%2BqZFLdY%2Bvgp55Dcxpv8Zsyy%2BWvJVMLCJsOqv6gXctzKEzTI61WGNLnfOPP9oETb5jBN8GpMPJ8x9XtBWe6XNd%2FidYUZ0%2F9%2Fhxf0Ca4vG2e1SDwalVbpn7uQFRh11gICx%2Fu3Vk0DRGt5NVcdVCGWf1CkDNTZzBdqLXfafZRciyY7KQCLTpQNyECbMnsqhhA8dk409tNF8GivuxFvzqr0ibvemb18rnxyyl6rMCmTmeCGwVFUM17SbUFJCHxVTYmgdrquxNBECXbLJOAnZxQpQUZyLJ5enCpZ%2B3ltLfROr9lUS9bTCsUkGCBxQSTjOR2MXNV%2Ftz%2FFPMra%2BLTgEUrd99n0a7woVDbO6UMG312GKDuihkeq3qeldCNphPkJYAT0qNWGlahSS6QfI5JN2eptkDwOjsw%2FCY0uCz4hGkRYCKbe2cLqSREf8xBl6VsminGYFLQ%3D"
              },
              {
                "name": "__ASYNCPOST",
                "value": "true"
              },
              {
                "name": "btnUpdateEndSel",
                "value": "Select%20this%20Exit"
              }
            ]
          }
        },
        "response": {
          "status": 200,
          "statusText": "",
          "httpVersion": "http/2.0",
          "headers": [
            {
              "name": "date",
              "value": "Wed, 03 Jan 2018 04:40:01 GMT"
            },
            {
              "name": "server",
              "value": "Microsoft-IIS/10.0"
            },
            {
              "name": "x-aspnet-version",
              "value": "4.0.30319"
            },
            {
              "name": "x-powered-by",
              "value": "ASP.NET"
            },
            {
              "name": "content-type",
              "value": "text/plain; charset=utf-8"
            },
            {
              "name": "status",
              "value": "200"
            },
            {
              "name": "cache-control",
              "value": "private"
            },
            {
              "name": "content-length",
              "value": "7594"
            }
          ],
          "cookies": [],
          "content": {
            "size": 7594,
            "mimeType": "text/plain"
          },
          "redirectURL": "",
          "headersSize": -1,
          "bodySize": -1,
          "_transferSize": 7736
        },
        "cache": {},
        "timings": {
          "blocked": 1.561556011874923,
          "dns": 12.76199999847448,
          "ssl": 14.753000024938899,
          "connect": 39.51799997594208,
          "send": 0.6600000197067999,
          "wait": 46.17099999450146,
          "receive": 2.6599999982863665,
          "_blocked_queueing": 0.5560000136028975
        },
        "serverIPAddress": "54.225.195.58",
        "connection": "2156233",
        "pageref": "page_19"
      }
    ]
  }
}