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

# Create the Lambda function

Create from canary
Name: PollODS
Existing Role > LambdaToDynamo

lambda_function.lambda_handler



Upload to an S3 bucket:
Way more of a PITA than it should be.
You have to create a .zip and the .py needs to be in the base of the zip
The lambda handler needs to be set to <filebasename>.<function>
If it doesn't show you the content then it can't find the function.
You'll also get this  message if one of your imports is missing:
 ```
 {
  "errorMessage": "Unable to import module 'lambda_function'"
}
```
 
 


Notes on scheduling the timing of the Lambda function:
http://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-create-function.html




https://aws.amazon.com/dynamodb/iot/

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