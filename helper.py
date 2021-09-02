from collections import OrderedDict
from datetime import datetime

def calculate_total(data):

    fields = ["delta", "gamma", "vega", "theta"]

    result = data["result"]
    
    response = {}
    # total = {
    #     "delta": 0,
    #     "gamma": 0,
    #     "vega": 0,
    #     "theta": 0
    # }
    for doc in result:
        try:
            instrument_name = doc["instrument_name"]
            currency, date = instrument_name.split('-')[0:2]

            if date in response:
                for field in fields:
                    response[date][field] += doc[field]
                    
            
            else:
                response[date] = {field : doc[field] for field in fields}
                    
                    

        except Exception as ex:
            print(str(ex))

        # total["delta"] += doc["delta"]
        # total["gamma"] += doc["gamma"]
        # total["vega"] += doc["vega"]
        # total["theta"] += doc["theta"]
    response = dict(OrderedDict(sorted(response.items(), key=lambda t: datetime.strptime(t[0], "%d%b%y"))))
    # response["Sum"] = total
    return response

def get_exp_strikes(instrument_names):

    exp_date_strike = {}
    
    for instrument_name in instrument_names:
        date, strike = instrument_name.split('-')[1:3]

        if date in exp_date_strike:
            exp_date_strike[date].add(int(strike))
            
        else:
            exp_date_strike[date] = {int(strike)}
    
    return exp_date_strike

def update_mark_iv1(implied_dict, order_book):
    
    try:

        greeks_delta = order_book["greeks"]["delta"]
        mark_iv = order_book["mark_iv"]

        exp_date = order_book["underlying_index"].split('-')[1]

        if exp_date in implied_dict:
            # if greeks_delta is more close to 0.5 than previous recorder than update its value
            if implied_dict[exp_date]["greeks_delta"] > abs(-0.5 - greeks_delta):
                implied_dict[exp_date] = {
                    "greeks_delta": abs(-0.5 - greeks_delta),
                    "mark_iv": mark_iv
                }
        else:
            implied_dict[exp_date] = {
                "greeks_delta": abs(-0.5 - greeks_delta),
                "mark_iv": mark_iv
            }
    except Exception as ex:
        print(str(ex))
    return implied_dict


def get_future_position(data):
    response = {}
    result = data["result"]

    for doc in result:
        instrument_name = doc["instrument_name"]
        currency, date = instrument_name.split('-')[0:2]
        size_currency = doc["size_currency"]
        mark_price = doc["mark_price"]


        response[date] = {
            "future_pos": size_currency,
            "future_price": mark_price
        }

    return response
        

def get_acc_information(request):

    request = request["result"]

    return {
        "Balance": request["balance"],
        "Equity": request["equity"],
        "Available Funds": request["available_funds"]
    }