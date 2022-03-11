import pymongo

connstr = "[REDACTED]"
srv = subjapi_google_belgium = pymongo.MongoClient(connstr)
db = subjapidb = subjapi_google_belgium["subjapidb"]
col = subjects = subjapidb["subjects"]
res = subjects.find().sort("id", pymongo.ASCENDING).limit(5)

l = []
for row in res:
    l.append(row)
