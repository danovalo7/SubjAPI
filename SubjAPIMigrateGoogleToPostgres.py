from SubjAPIGoogleDatabase import SubjAPIGoogleDatabase
from SubjAPIPostgresDatabase import SubjAPIPostgresDatabase

pwd = "[REDACTED]"
gdb = SubjAPIGoogleDatabase(threaded=True, password=pwd)
pdb = SubjAPIPostgresDatabase(threaded=True, password=pwd, cache_size=200)
indd = pdb.get_indexed()


def extract_parenthesis(s: str):
    x = s.rfind("(")
    y = s.rfind(")")
    if x != -1 and y != -1 and x + 1 < y:
        return s[x + 1:y]


cr = 0

google_records = list(gdb._datastore_client.query(kind="subject").fetch())
print("Records fetched: ", len(google_records))
for row in google_records:
    rid = row.id
    if rid in indd:
        print("Skipped row ", rid)
        continue
    row = dict(row)
    row["id"] = rid
    if row.get("name"):
        row["name"] = row["name"].strip()
        row["short"] = extract_parenthesis(row["name"]).strip()
    if row.get("code"):
        row["code"] = row["code"].strip()
    pdb.cache(row)
    cr += 1
    if cr % 500 == 0:
        print("Cached ", cr, " records so far")
print("Done, cached records: ", cr)
