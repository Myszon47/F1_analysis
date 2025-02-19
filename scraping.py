import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

def scrape_f1_data():
    URL = 'https://www.formula1.com/en/results/2024/races/1229/bahrain/race-result'
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    race_titles_search = soup.find_all(attrs={"class": "block", "href": re.compile("^/en/results/2024/races/12[0-9]*/[a-z]*[-]*[a-z]*/race-result")})
    race_URLs = [x['href'] for x in race_titles_search][0:-1]
    race_titles = [x.get_text() for x in race_titles_search]
    race_titles.pop(len(race_titles)-1)

    qualifying_URLs = [url.replace("race-result", "qualifying") for url in race_URLs]

    race_df = pd.DataFrame()
    qualifying_df = pd.DataFrame()

    def get_results(url, race_number, race_titles):
        page = requests.get('https://www.formula1.com' + url)
        soup = BeautifulSoup(page.content, "html.parser")
        race_title = race_titles[race_number]

        try:
            race_results_table = soup.find(class_="f1-table")
            race_headers_search = race_results_table.find_all('th')
            race_headers = [x.get_text() for x in race_headers_search]
            race_headers.append('Circuit')

            race_results_search = race_results_table.find_all(class_='f1-text')
            race_results = [x.get_text() for x in race_results_search]
            race_results = race_results[len(race_headers)-1:len(race_results)]

            race_results_row = []
            for x in range(0, len(race_results)-5, len(race_headers)-1):
                race_results_row += [race_results[x:x+len(race_headers)-1]]

            df = pd.DataFrame(columns=race_headers)
            for row in race_results_row:
                df.loc[len(df)] = row + [race_title]

            df.drop(columns=['No', 'Laps'], axis=0, inplace=True)
            df['Driver'] = df['Driver'].str[:-3]
            return df

        except AttributeError:
            print(f"Race '{race_title}' has not yet taken place.")
            return pd.DataFrame()

    race_dfs = []
    qualifying_dfs = []

    for race_number in range(len(race_URLs)):
        race_dfs.append(get_results(race_URLs[race_number], race_number, race_titles))
        qualifying_dfs.append(get_results(qualifying_URLs[race_number], race_number, race_titles))

    if race_dfs:
        race_df = pd.concat(race_dfs, ignore_index=True)
    if qualifying_dfs:
        qualifying_df = pd.concat(qualifying_dfs, ignore_index=True)

    return race_df, qualifying_df


race_df, qualifying_df = scrape_f1_data()
# save to excel file
with pd.ExcelWriter('f12024_results.xlsx') as writer:
    race_df.to_excel(writer, sheet_name='race_results', index=False)
    qualifying_df.to_excel(writer, sheet_name='qualifying_results', index=False)