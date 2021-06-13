from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import pandas as pd

url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo"
ATR = 7
MULTIPLIER = 3


class APIError(Exception):
    '''An API Error Exception'''

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)


def superTrendCalculator(df):
    '''Initialising the Required Fields'''
    df['TR0'] = abs(df["High"] - df["Low"])
    df['TR1'] = abs(df["High"] - df["Close"].shift(1))
    df['TR2'] = abs(df["Low"] - df["Close"].shift(1))
    df["TR"] = round(df[['TR0', 'TR1', 'TR2']].max(axis=1), 2)
    df["ATR"] = 0.00
    df['Upper_Bound'] = 0.00
    df["Lower_Bound"] = 0.00
    df["Final_Upper_Bound"] = 0.00
    df["Final_Lower_Bound"] = 0.00
    df["Super_Trend"] = 0.00
    df["Buy_Sell"] = ""

    '''Calculating ATR using Previous ATR and Current TR'''
    for i, row in df.iterrows():
        if i == 0:
            df.loc[i, 'ATR'] = 0.00
        else:
            df.loc[i, 'ATR'] = ((df.loc[i-1, 'ATR'] * 13)+df.loc[i, 'TR'])/14

    '''Calculating Upper and Lower Bound'''
    df['Upper_Bound'] = round((((df["High"]) + df["Low"]) / 2) +
                              (MULTIPLIER * df["ATR"]), 2)
    df['Lower_Bound'] = round(((df["High"] + df["Low"]) / 2) -
                              (MULTIPLIER * df["ATR"]), 2)

    '''Calculating Fianl Upper Bound'''
    for i, row in df.iterrows():
        if i == 0:
            df.loc[i, "Final_Upper_Bound"] = 0.00
        else:
            if (df.loc[i, "Upper_Bound"] < df.loc[i-1, "Final_Upper_Bound"]) | (df.loc[i-1, "Close"] > df.loc[i-1, "Final_Upper_Bound"]):
                df.loc[i, "Final_Upper_Bound"] = df.loc[i, "Upper_Bound"]
            else:
                df.loc[i, "Final_Upper_Bound"] = df.loc[i-1, "Final_Upper_Bound"]

    '''Calculating Final Lower Bound'''
    for i, row in df.iterrows():
        if i == 0:
            df.loc[i, "Final_Lower_Bound"] = 0.00
        else:
            if (df.loc[i, "Lower_Bound"] > df.loc[i-1, "Final_Lower_Bound"]) | (df.loc[i-1, "Close"] < df.loc[i-1, "Final_Lower_Bound"]):
                df.loc[i, "Final_Lower_Bound"] = df.loc[i, "Lower_Bound"]
            else:
                df.loc[i, "Final_Lower_Bound"] = df.loc[i-1, "Final_Lower_Bound"]

    '''Calculating Super Trend'''
    for i, row in df.iterrows():
        if i == 0:
            df.loc[i, "Super_Trend"] = 0.00
        elif (df.loc[i-1, "Super_Trend"] == df.loc[i-1, "Final_Upper_Bound"]) & (df.loc[i, "Close"] <= df.loc[i, "Final_Upper_Bound"]):
            df.loc[i, "Super_Trend"] = df.loc[i, "Final_Upper_Bound"]
        elif (df.loc[i-1, "Super_Trend"] == df.loc[i-1, "Final_Upper_Bound"]) & (df.loc[i, "Close"] > df.loc[i, "Final_Upper_Bound"]):
            df.loc[i, "Super_Trend"] = df.loc[i, "Final_Lower_Bound"]
        elif (df.loc[i-1, "Super_Trend"] == df.loc[i-1, "Final_Lower_Bound"]) & (df.loc[i, "Close"] >= df.loc[i, "Final_Lower_Bound"]):
            df.loc[i, "Super_Trend"] = df.loc[i, "Final_Lower_Bound"]
        elif (df.loc[i-1, "Super_Trend"] == df.loc[i-1, "Final_Lower_Bound"]) & (df.loc[i, "Close"] < df.loc[i, "Final_Lower_Bound"]):
            df.loc[i, "Super_Trend"] = df.loc[i, "Final_Upper_Bound"]

    '''Buy Sell Indicator'''
    for i, row in df.iterrows():
        if i == 0:
            df["Buy_Sell"] = "NA"
        elif (df.loc[i, "Super_Trend"] < df.loc[i, "Close"]):
            df.loc[i, "Buy_Sell"] = "BUY"
        else:
            df.loc[i, "Buy_Sell"] = "SELL"


if __name__ == "__main__":
    req = Request(url)

    try:
        urlFile = urlopen(url)
    except HTTPError as e:
        print('The server couldn\'t fulfill the request.')
        raise APIError(e.reason)
    except URLError as e:
        print('Failed to reach a server.')
        raise APIError(e.reason)
    else:
        jsonList = json.load(urlFile)
        dataSet = jsonList.get("Time Series (5min)")
        df = pd.DataFrame.from_dict(dataSet, orient='index')
        df.reset_index(level=0, inplace=True)
        df.rename(columns={'index': 'Time_Stamp', '3. low': 'Low', '2. high': 'High',
                  '4. close': 'Close', '5. volume': 'Volume', "1. open": 'Open'}, inplace=True)
        df[["Low", "High", 'Close', 'Open', 'Volume']] = df[[
            "Low", "High", 'Close', 'Open', 'Volume']].apply(pd.to_numeric)
        superTrendCalculator(df)
        df.to_csv('Super_Trend.csv', header=True, index=False)
