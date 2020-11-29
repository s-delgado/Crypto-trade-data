import requests
import time
import pandas as pd
import calendar
from datetime import datetime, timedelta


def get_unix_ms_from_date(date):
    # Expects a datetime object
    return int(calendar.timegm(date.timetuple()) * 1000 + date.microsecond / 1000)


def get_first_trade_id_from_start_date(api_url, symbol, from_date):
    new_end_date = from_date + timedelta(seconds=60)
    r = requests.get(api_url,
                     params={
                         "symbol": symbol,
                         "startTime": get_unix_ms_from_date(from_date),
                         "endTime": get_unix_ms_from_date(new_end_date)
                     })

    if r.status_code != 200:
        print('somethings wrong!', r.status_code)
        print('sleeping for 10s... will retry')
        time.sleep(10)
        get_first_trade_id_from_start_date(api_url, symbol, from_date)

    response = r.json()
    if len(response) > 0:
        return response[0]['a']
    else:
        raise Exception('no trades found')


def get_trades(api_url, symbol, from_id):
    r = requests.get(api_url,
                     params={
                         "symbol": symbol,
                         "limit": 1000,
                         "fromId": from_id
                     })

    if r.status_code != 200:
        print('somethings wrong!', r.status_code)
        print('sleeping for 10s... will retry')
        time.sleep(10)
        get_trades(api_url, symbol, from_id)

    return r.json()


def trim(df, to_date):
    return df[df['T'] <= get_unix_ms_from_date(to_date)]


def fetch_binance_trades(api_url, symbol, from_date, to_date):
    from_id = get_first_trade_id_from_start_date(api_url, symbol, from_date)
    current_time = 0
    df = pd.DataFrame()

    while current_time < get_unix_ms_from_date(to_date):
        try:
            trades = get_trades(api_url, symbol, from_id)

            from_id = trades[-1]['a']
            current_time = trades[-1]['T']

            print(
                f'fetched {len(trades)} trades from id {from_id} @ {datetime.utcfromtimestamp(current_time / 1000.0)}')

            df = pd.concat([df, pd.DataFrame(trades)])

            # dont exceed request limits
            time.sleep(0.5)
        except Exception:
            print('somethings wrong....... sleeping for 15s')
            time.sleep(15)

    df.drop_duplicates(subset='a', inplace=True)
    df = trim(df, to_date)
    print(f'binance__{symbol}__trades__from__{from_date.strftime("%d/%m/%Y %H:%M:%S")}__to__{to_date.strftime("%d/%m/%Y %H:%M:%S")}')
    return df


def trade_verifier(df):
    values = df.to_numpy()

    last_id = values[0][0]

    for row in values[1:]:
        trade_id = row[0]
        if last_id + 1 != trade_id:
            print('last_id', last_id)
            print('trade_id', trade_id)
            print('inconsistent data')
            return False
        last_id = trade_id

    print('data is OK!')
    return True

