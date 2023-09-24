import glob
import os
import pickle
import re
from datetime import datetime

import pandas as pd
from pick import pick

pd.options.mode.chained_assignment = None

################################################################
# Configuration

ask_owner = True
owner_options = ["Tim", "Corina", "Beide"]
################################################################

base_path = os.path.join(os.path.dirname(
    __file__))

migros_files = glob.glob(os.path.join(base_path, "downloads/migros/*.csv"))
coop_files = glob.glob(os.path.join(base_path, "downloads/coop/*.csv"))

data_per_month = {}

owner_data = None


def get_owner_of_article(article_name):
    cache_file = os.path.join(base_path, "owner_data.pickle")
    if (owner_data is None):
        if (os.path.exists(cache_file)):
            with open(cache_file, 'rb') as f:
                owner_data = pickle.load(f)
        else:
            owner_data = {}
    if (article_name not in owner_data):
        if (not ask_owner):
            return None
        owner, index = pick(
            owner_options, "Please choose the owner of the article '{}': ".format(article_name))
        owner_data[article_name] = owner
        with open(cache_file, 'wb') as f:
            pickle.dump(owner_data, f)
    return owner_data[article_name]


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
        for idx, row in smaller_df.iterrows():
            smaller_df.at[idx, "Besitzend"] = get_owner_of_article(row["Artikel"])
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
    for idx, row in df.iterrows():
            df.at[idx, "Besitzend"] = get_owner_of_article(row["Artikel"])
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
