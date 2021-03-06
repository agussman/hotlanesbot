import requests
import json
import datetime

import boto3

import pprint

ODS = [
    "1009",
    "1010",
    "1011",
    "1012",
    "1013",
    "1014",
    "1015",
    "1016",
    "1017",
    "1018",
    "1019",
    "1020",
    "1021",
    "1022",
    "1023",
    "1024",
    "1025",
    "1026",
    "1027",
    "1028",
    "1029",
    "1030",
    "1031",
    "1032",
    "1033",
    "1034",
    "1035",
    "1036",
    "1037",
    "1038",
    "1040",
    "1041",
    "1042",
    "1043",
    "1044",
    "1045",
    "1046",
    "1048",
    "1049",
    "1050",
    "1051",
    "1052",
    "1053",
    "1055",
    "1056",
    "1057",
    "1058",
    "1059",
    "1060",
    "1062",
    "1063",
    "1064",
    "1065",
    "1066",
    "1068",
    "1069",
    "1070",
    "1071",
    "1072",
    "1074",
    "1075",
    "1076",
    "1077",
    "1079",
    "1080",
    "1081",
    "1082",
    "1085",
    "1086",
    "1087",
    "1088",
    "1089",
    "1090",
    "1091",
    "1092",
    "1094",
    "1095",
    "1096",
    "1097",
    "1098",
    "1099",
    "1100",
    "1101",
    "1102",
    "1103",
    "1104",
    "1105",
    "1106",
    "1107",
    "1108",
    "1109",
    "1110",
    "1111",
    "1112",
    "1113",
    "1114",
    "1115",
    "1116",
    "1117",
    "1118",
    "1119",
    "1120",
    "1121",
    "1122",
    "1123",
    "1124",
    "1125",
    "1126",
    "1127",
    "1128",
    "1129",
    "1130",
    "1131",
    "1132",
    "1133",
    "1134",
    "1135",
    "1136",
    "1140",
    "1141",
    "1144",
    "1145",
    "1146",
    "1147",
    "1148",
    "1149",
    "1150",
    "1151",
    "1152",
    "1153",
    "1154",
    "1155",
    "1156",
    "1157",
    "1158",
    "1159",
    "1160",
    "1161",
    "1162",
    "1163",
    "1164",
    "1165",
    "1166",
    "1167",
    "1168",
    "1169",
    "1170",
    "1171",
    "1172",
    "1173",
    "1174",
    "1175",
    "1176",
    "1177",
    "1178",
    "1179",
    "1180",
    "1181",
    "1182",
    "1183",
    "1184",
    "1185",
    "1186",
    "1187",
    "1188",
    "1189",
    "1190",
    "1191",
    "1192",
    "1193",
    "1194",
    "1195",
    "1196",
    "1197",
    ]

URL = "https://www.expresslanes.com/on-the-road-api"

def lambda_handler(event, context):

    #s3 = boto3.resource('s3')
    #for bucket in s3.buckets.all():
    #    print(bucket.name)

    ddb = boto3.resource(service_name='dynamodb')
    table = ddb.Table("Rates")

    #print table.item_count

    # DynamoDB wants timestamps as Strings (we're dropping the milliseconds)
    dt = datetime.datetime.now().isoformat(' ').split(".")[0]

    #print dt

    payload = {"ods[]": ODS}

    resp = requests.get(url=URL, params=payload)
    print "%s %s %s" % (dt, resp.status_code, resp.url)
    data = json.loads(resp.content)

    print "Got response:"
    #pprint.pprint(data)

    for rate in data['rates']:
        rate[u'dt'] = dt
        pprint.pprint(rate)

        send_to_dynamo(rate, table)

def send_to_dynamo(rate, table):
    #print "..."
    response = table.put_item(Item=rate)
    print(response)


if __name__ == "__main__":
    lambda_handler({}, {})