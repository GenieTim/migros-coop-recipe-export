import re
import sys

import numpy as np
import pandas as pd
from tika import parser

file = sys.argv[1] #if len(sys.argv) > 2 else "/Users/timbernhard/Privat/Programming/OpenSource-Contributions/export-all-belege/tmp-downloads/receipt_9900150890603042300002101409.pdf"
assert(file is not None)
# file = r"/Users/timbernhard/Downloads/receipt_9900170316008102200035951979.pdf"

rawText = parser.from_file(file)
data = rawText['content'].splitlines()

lineIdx = 0
while (lineIdx < len(data) and not data[lineIdx].startswith("Artikel")):
    lineIdx += 1


def split_line(line):
    split = line.split(" ")
    return list(filter(lambda x: x != "", split))


def is_number(value):
    return np.all([c.isdigit() or c == "." for c in value])


header = data[lineIdx]
split_header = split_line(header)
header_len = len(split_header)
assert(split_header == ["Artikel", "Menge",
       "Preis", "Aktion", "Total", "Zusatz"])
processed_data = {}
for col in split_header:
    processed_data[col] = []

# one empty line
lineIdx += 2
processed_data_idx = 0
while (lineIdx < len(data) and data[lineIdx] != "" and not (data[lineIdx].startswith("Rabatt") or data[lineIdx].startswith("Bon ") or data[lineIdx].startswith("Total CHF"))):
    for col in split_header:
        processed_data[col].append("")
    # parse this line
    line = split_line(data[lineIdx])
    # start at the back
    in_line_idx = len(line)-1
    while (np.all([c.isalpha() and not c.isdigit() for c in line[in_line_idx]]) and in_line_idx > 0):
        processed_data["Zusatz"][processed_data_idx] += " " + line[in_line_idx]
        in_line_idx -= 1

    if (is_number(line[in_line_idx]) and is_number(line[in_line_idx-1]) and is_number(line[in_line_idx-2]) and is_number(line[in_line_idx-3])):
        processed_data["Zusatz"][processed_data_idx] = line[in_line_idx] + \
            processed_data["Zusatz"][processed_data_idx]
        in_line_idx -= 1

    processed_data["Total"][processed_data_idx] += line[in_line_idx]
    in_line_idx -= 1

    # now it gets more complicated:
    assert(is_number(line[in_line_idx]) and is_number(line[in_line_idx-1]))
    if (is_number(line[in_line_idx]) and is_number(line[in_line_idx-1]) and is_number(line[in_line_idx-2])):
        processed_data["Aktion"][processed_data_idx] += line[in_line_idx]
        in_line_idx -= 1

    processed_data["Preis"][processed_data_idx] += line[in_line_idx]
    in_line_idx -= 1

    processed_data["Menge"][processed_data_idx] += line[in_line_idx]
    in_line_idx -= 1

    processed_data["Artikel"][processed_data_idx] = " ".join(
        line[0:in_line_idx+1])

    processed_data_idx += 1
    lineIdx += 1

# then, we can also process the bons and other vouchers
while (lineIdx < len(data) and (data[lineIdx].startswith("Rabatt") or data[lineIdx].startswith("Bon ") or data[lineIdx] == "")):
    if (data[lineIdx] != ""):
        for col in split_header:
            processed_data[col].append("")
        # parse this line
        line = split_line(data[lineIdx])
        processed_data["Preis"][processed_data_idx] += line[len(line)-1]
        processed_data["Artikel"][processed_data_idx] += " ".join(
            line[0:-1])
        processed_data_idx += 1
    lineIdx += 1

date = ""
while (lineIdx < len(data)):
    line = split_line(data[lineIdx])
    if (len(line) > 0):
      search = re.search(r"(\d{2})\.(\d{2}).(\d{2,4})", line[0])
      if (search is not None):
          date = "-" + search.group(0)
          break
    lineIdx += 1

df = pd.DataFrame(processed_data)
target_file = file.replace(".pdf", "{}.csv".format(date))
df.to_csv(target_file)

print(target_file)
