import requests
from bs4 import BeautifulSoup
import json

url_head = "https://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod="
url_tail = "&lng=sk"
url_index = 2000
url = url_head + str(url_index) + url_tail
r = requests.get(url)
print(r.apparent_encoding)
soup = BeautifulSoup(r.text, 'html.parser')
charset = soup.head.meta.attrs['content'][soup.head.meta.attrs['content'].index('charset=') + 8:]
r.encoding = charset
soup = BeautifulSoup(r.text, 'html.parser')
subj = {}
grade_dict = {0: "X", 1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}
td = soup.table.find_all("td")
subj["id"] = url_index
subj["code"] = td[2].text[14:]
subj["name"] = td[3].text[16:]
subj["url"] = url
subj["credits"] = float(td[5].text[td[5].text.rfind(" ") + 1:])
subj["students_evaluated"] = int(td[15].text[td[15].text.rfind(" ") + 1:])
subj["average_grade"] = grade_dict[round(sum([(n + 1) * float(item.text[:-1].strip()) for n, item in enumerate(td[22:28])]) / 100)]
subj["desc_length"] = len(td[9].text) + len(td[10].text) + len(td[11].text) + len(td[12].text)
subj["date"] = "{2}-{1}-{0} {3}:{4}:{5}".format(*td[29].text[23:].replace(".", " ").replace(":", " ").split(" "))
print(subj["id"], subj["name"])
