import asyncio
import websockets
import json
import pandas as pd
from helper import *
from to_gsheets import write_df_to_sheet, updateAccSummary
import time


client_id = ""
client_secret = ""


class DeribitWS:

    def __init__(self, client_id, client_secret, test=False):
        '''
        Информация об API:
        10001 - максимальное число данных в одном запросе
        '''

        if test:
            self.url = 'wss://test.deribit.com/ws/api/v2'
        elif not test:
            self.url = 'wss://www.deribit.com/ws/api/v2'
        else:
            raise Exception('live must be a bool, True=real, False=paper')


        self.client_id = client_id
        self.client_secret = client_secret

        self.auth_creds = {
              "jsonrpc" : "2.0",
              "id" : 0,
              "method" : "public/auth",
              "params" : {
                "grant_type" : "client_credentials",
                "client_id" : self.client_id,
                "client_secret" : self.client_secret
              }
            }
        # self.test_creds()

        self.msg = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": None,
        }

    async def pub_api(self, msg):
        async with websockets.connect(self.url) as websocket:
            await websocket.send(msg)
            while websocket.open:
                response = await websocket.recv()
                return json.loads(response)

    async def priv_api(self, msg):
        async with websockets.connect(self.url) as websocket:
            await websocket.send(json.dumps(self.auth_creds))
            while websocket.open:
                response = await websocket.recv()
                await websocket.send(msg)
                response = await websocket.recv()
                break
            return json.loads(response)

    @staticmethod
    def async_loop(api, message):
        return asyncio.run(api(message))

    def execute_funcs(self, *funcs):
        return asyncio.run(self.__execute_many_funcs(*funcs))

    async def __execute_many_funcs(self, *funcs):
        res = await asyncio.gather(*funcs)
        return res

    def get_positions(self, currency = 'BTC', kind="future"):

        params = {
            "currency" : currency,
            "kind" : kind
        }

        self.msg["method"] = "private/get_positions"
        self.msg["params"] = params
        positions = self.async_loop(self.priv_api, json.dumps(self.msg))
        return positions

    def get_instrument_names(self, currency):
        params = {
            "currency": currency,
            "kind": "option"
        }
        self.msg["method"] = "public/get_instruments"
        self.msg["params"] = params
        quote = self.async_loop(self.pub_api, json.dumps(self.msg))

        return quote['result']

    def get_order_book(self, instrument):
        params = {
            "instrument_name": instrument,
        }
        self.msg["method"] = "public/get_order_book"
        self.msg["params"] = params
        quote = self.async_loop(self.pub_api, json.dumps(self.msg))

        return quote['result']


    def get_public_index(self, currency):
        params = {
            "currency": currency,
        }
        self.msg["method"] = "public/get_index"
        self.msg["params"] = params
        quote = self.async_loop(self.pub_api, json.dumps(self.msg))

        return quote['result']
    

    def account_summary(self, currency, extended=False):
        params = {
            "currency": currency,
            "extended": extended
        }

        self.msg["method"] = "private/get_account_summary"
        self.msg["params"] = params
        summary = self.async_loop(self.priv_api, json.dumps(self.msg))
        return summary

def custom_sheet(currency='BTC', sheet_name=""):
    # calculate greeks total (delta, gamma etc)
    positions = ws.get_positions(currency=currency, kind = 'option')
    total = calculate_total(positions)
    # print(total)
    greeks_df = pd.DataFrame.from_dict(total).transpose()
    print(greeks_df)


    # calculate implied
    instruments = ws.get_instrument_names(currency)
    instrument_names = []
    for instrument in instruments:
        
        instrument_names.append(instrument["instrument_name"])

    implied_dict = {}

    exp_date_strikes = get_exp_strikes(instrument_names)

    for expDate, strikes in exp_date_strikes.items():
        

        strikes = list(strikes)

        # print("\n", expDate, sorted(strikes))
        underlying_price = ws.get_order_book(currency + '-' + expDate + '-' + str(strikes[0]) + '-' + 'P')["underlying_price"]
        # print(underlying_price)

        closest_strike = min(strikes, key=lambda x:abs(x-underlying_price))
        # print(closest_strike)
        
        mark_iv = ws.get_order_book(currency + '-' + expDate + '-' + str(closest_strike) + '-' + 'P')["mark_iv"]
        implied_dict[expDate] = {
                "mark_iv": mark_iv
            }
    
    # count = 0
    # for i in instrument_names[:100]:
    #     count += 1
    #     if count == 25:
    #         time.sleep(3)
    #         count = 0
    #     # print(i)
    #     if "27AUG21" in i:
    #         time.sleep(1)
    #     order_book = ws.get_order_book(i)
    #     # print("\n", order_book)

    #     implied_dict = update_mark_iv(implied_dict, order_book)
    print("\n\n", implied_dict)
    
    implied_df = pd.DataFrame.from_dict(implied_dict).transpose()
    # del implied_df["greeks_delta"]
    
    # calculate future pos
    positions = ws.get_positions(currency=currency, kind = 'future')
    future_pos_dict = get_future_position(positions)
    future_pos_df = pd.DataFrame.from_dict(future_pos_dict).transpose()
    print(future_pos_df)
    
    final_df = pd.concat([greeks_df, implied_df, future_pos_df], axis=1)

    print(final_df)
    
    # for sorting index 
    final_df.reset_index(inplace=True)
    i = pd.to_datetime(final_df['index'], errors='coerce')
    j = i.sort_values()
    final_df = final_df.loc[j.index]
    final_df.set_index('index',inplace=True)

    final_df.loc["Sum"] = final_df.sum(axis=0)
    
    final_df["delta + future pos"] = final_df.fillna(0)["delta"] + final_df.fillna(0)["future_pos"]
    
    print(final_df)
    write_df_to_sheet(final_df, sheet_name)


    acc_summary = ws.account_summary(currency=currency)
    acc_info = get_acc_information(acc_summary)

    # get public index price
    index_price = ws.get_public_index(currency=currency)
    acc_info["index_price"] = index_price[currency]
    updateAccSummary(sheet_name, **acc_info)

if __name__ == '__main__':

    ws = DeribitWS(client_id, client_secret, test=False)

    while True:
        try:
            custom_sheet(currency="BTC", sheet_name="BTC-Options")
            custom_sheet(currency="ETH", sheet_name="ETH-Options")
        except Exception as ex:
            print(str(ex))
        finally:
            print("\n\n Waiting time: 5 mins\n\n")
            time.sleep(300)
