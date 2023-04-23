import glob
import os
import re
from datetime import datetime

import pandas as pd

pd.options.mode.chained_assignment = None

base_path = os.path.join(os.path.dirname(
    __file__))

migros_files = glob.glob(os.path.join(base_path, "downloads/migros/*.csv"))
coop_files = glob.glob(os.path.join(base_path, "downloads/coop/*.csv"))

data_per_month = {}

for file in migros_files:
    df = pd.read_csv(file, sep=";")
    dates = df["Datum"].unique()
    df["Type"] = "Migros"
    for date in dates:
        search = re.search(r"(\d{2})\.(\d{2}).(\d{2,4})", date)
        assert(search is not None)
        date_object = datetime.strptime(date, "%d.%m.%Y")
        date_full = date_object.strftime("%B %Y")
        smaller_df = df.loc[df["Datum"] == date]
        smaller_df["Total"] = smaller_df["Umsatz"].sum()
        if (date_full not in data_per_month.keys()):
            data_per_month[date_full] = smaller_df
        else:
            data_per_month[date_full] = pd.concat(
                [data_per_month[date_full], smaller_df], ignore_index=True)


for file in coop_files:
    df = pd.read_csv(file)
    if ("Datum" in df.columns):
        date = df["Datum"].unique()[0]
    else:
        search = re.search(r"(\d{2})\.(\d{2}).(\d{2,4})", file)
        assert(search is not None)
        date = search.group(0)
    try:
        date_object = datetime.strptime(date, "%d.%m.%y")
    except:
        date_object = datetime.strptime(date, "%d.%m.%Y")
    date_full = date_object.strftime("%B %Y")
    df["Datum"] = date
    df["Type"] = "Coop"
    if (date_full not in data_per_month.keys()):
        data_per_month[date_full] = df
    else:
        data_per_month[date_full] = pd.concat([
            data_per_month[date_full], df], ignore_index=True)


# prepare to write outputs
overall_writer = pd.ExcelWriter(os.path.join(
    base_path, 'belege.xlsx'), engine='xlsxwriter')

for key, value in data_per_month.items():
    value.to_excel(overall_writer, sheet_name=key)

# Close the Pandas Excel writer and output the Excel file.
overall_writer.close()
