from google.cloud import datastore
import json
from time import perf_counter

datastore_client = datastore.Client.from_service_account_json("cretentials.json")
jsons = [{"id": 200000, "code": "40B103", "name": "stavebn\u00e9 materi\u00e1ly (SMat)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200000&lng=sk", "credits": 5.0,
          "students_evaluated": 799, "average_grade": "D", "desc_length": 1098, "date": "2013-9-30 16:12:48"},
         {"id": 200001, "code": "40B101", "name": "matematika 1 (Mat1)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200001&lng=sk", "credits": "7.0",
          "students_evaluated": "904", "average_grade": "D", "desc_length": 1221, "date": "2013-10-23 18:09:33"},
         {"id": 200002, "code": "40B109", "name": "dejiny architekt\u00fary a stavite\u013estva 1 (DAaS1)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200002&lng=sk",
          "credits": "3.0", "students_evaluated": "452", "average_grade": "C", "desc_length": 866, "date": "2014-9-26 09:29:30"},
         {"id": 200003, "code": "40B102", "name": "deskript\u00edvna geometria (DG)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200003&lng=sk", "credits": "5.0",
          "students_evaluated": "940", "average_grade": "C", "desc_length": 1808, "date": "2014-2-14 12:58:13"},
         {"id": 200004, "code": "40B104", "name": "geol\u00f3gia (Gl)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200004&lng=sk", "credits": "5.0", "students_evaluated": "829",
          "average_grade": "D", "desc_length": 1969, "date": "2014-2-18 12:45:56"},
         {"id": 200005, "code": "40B119", "name": "urbanizmus a \u00fazemn\u00e9 pl\u00e1novanie 1 (UUP)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200005&lng=sk",
          "credits": "3.0", "students_evaluated": "146", "average_grade": "C", "desc_length": 1544, "date": "2014-9-26 09:51:10"},
         {"id": 200006, "code": "40B107", "name": "matematick\u00fd semin\u00e1r 1 (MS1)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200006&lng=sk", "credits": "2.0",
          "students_evaluated": "797", "average_grade": "C", "desc_length": 1042, "date": "2011-4-2 18:23:56"},
         {"id": 200007, "code": "40B108", "name": "stavebn\u00e1 ch\u00e9mia (SCh)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200007&lng=sk", "credits": "3.0",
          "students_evaluated": "155", "average_grade": "C", "desc_length": 1175, "date": "2013-9-30 16:14:20"},
         {"id": 200008, "code": "80000 ", "name": "telesn\u00e1 v\u00fdchova (TV)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200008&lng=sk", "credits": "1.0",
          "students_evaluated": "1610", "average_grade": "A", "desc_length": 1003, "date": "2014-4-15 10:41:14"},
         {"id": 200009, "code": "40B221", "name": "statika stavebn\u00fdch kon\u0161trukci\u00ed 1B (SSK1B)", "url": "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod=200009&lng=sk",
          "credits": "7.0", "students_evaluated": "373", "average_grade": "E", "desc_length": 1598, "date": "2014-2-4 13:32:41"}]
ents = []
partkey = datastore_client.key("subject")
for item in jsons:
    ent = datastore.entity.Entity(partkey.completed_key(item.pop("id")))
    ent.update(item)
    ents.append(ent)

datastore_client.put_multi(ents)
t1 = perf_counter()
q = datastore_client.query(kind="subject")
q.keys_only()
y = [e.id for e in q.fetch()]
t2 = perf_counter()
x = [e.id for e in datastore_client.query(kind="subject").fetch()]
t3 = perf_counter()
print("query shortype: ", t2 - t1)
print("query longtype: ", t3 - t2)

# ** BACKUP **
with open("backup.json", "w+t", encoding="utf-8") as file:
    json.dump(list(datastore_client.query(kind="subject").fetch()), file, default=str, ensure_ascii=False)
