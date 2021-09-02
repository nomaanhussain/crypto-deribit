import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import (get_as_dataframe,
                               set_with_dataframe)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

SPREADSHEET_KEY = ''




def _get_worksheet(key: str, worksheet_name: str, creds: "json filepath to Google account credentials" = "jsonFileFromGoogle.json",) -> gspread.Worksheet:
    """ return a gspread Worksheet instance for given Google Sheets workbook/worksheet """
    
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        creds, scope)
    gc = gspread.authorize(credentials)
    wb = gc.open_by_key(key)
    sheet = wb.worksheet(worksheet_name)
    return sheet


def write(sheet: gspread.Worksheet, df: pd.DataFrame, **options) -> None:
    sheet.clear()
    set_with_dataframe(sheet, df,
                       include_index=True,
                       resize=False,
                       **options)


def write_df_to_sheet(df, sheet_name):
    SHEET_NAME = sheet_name
    sh: gspread.Worksheet = _get_worksheet(SPREADSHEET_KEY, SHEET_NAME)

    write(sh, df)


def updateAccSummary(sheet_name, **kwargs):
    
    SHEET_NAME = sheet_name
    sh: gspread.Worksheet = _get_worksheet(SPREADSHEET_KEY, SHEET_NAME)

    # sh.add_rows(3)
    # rows = [[]]
    # for k, v in kwargs.items():
    #     rows.append(['','','',str(k), v])
    # sh.append_rows(rows)

    
    sh.update_acell('D18', "Balance")
    sh.update_acell('D19', "Equity")
    sh.update_acell('D20', "Available Funds")
    sh.update_acell('D21', "Index Price")

    sh.update_acell('E18', kwargs["Balance"])
    sh.update_acell('E19', kwargs["Equity"])
    sh.update_acell('E20', kwargs["Available Funds"])
    sh.update_acell('E21', kwargs["index_price"])





