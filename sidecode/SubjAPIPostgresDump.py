import sqlalchemy
from datetime import datetime
import json


def extract_parenthesis(s: str):
    y = s.rfind(")")
    x = s[:y].rfind("(")
    if x != -1 and y != -1 and x + 1 < y:
        return s[x + 1:y].strip()


cs = 'postgresql://ubu9vdzrkxv50xapdjek:KHNbsxVVQ2XTz0H62oWv@bahxcbs7p3r7rdfuqxrl-postgresql.services.clever-cloud.com:5432/bahxcbs7p3r7rdfuqxrl'
eng = sqlalchemy.create_engine(cs, echo=False)
md = sqlalchemy.MetaData(eng)
md.reflect()
all_rows = [dict(item) for item in md.tables["subjects"].select().execute().fetchall()]
for row in all_rows:
    row["date_indexed"] = row["date_indexed"].isoformat()
    if isinstance(row["date_modified"], datetime):
        row["date_modified"] = row["date_modified"].isoformat()
    if row["credits"] is not None and row["credits"][:1] == '$':
        row["credits"] = row["credits"][1:]
    idle_is_trash = row.pop("url")
    if row["short"] is None and row["name"] is not None:
        row["short"] = extract_parenthesis(row["name"])

with open("subjapi.json", "w+t", encoding="utf-8") as file:
    json.dump(all_rows, file, ensure_ascii=False)
print("done")
