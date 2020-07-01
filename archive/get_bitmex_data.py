import requests
from datetime import datetime, timedelta
import os

# Download historical data
start = datetime.strptime("01-01-2017", "%d-%m-%Y")
end = datetime.today()

date_generated = [start + timedelta(days=x) for x in range(0, (end-start).days)]

for d in date_generated:
    print(d)

    date = d.strftime('%Y%m%d')
    file_name = date + ".csv.gz"

    if file_name not in os.listdir("data/trade/"):
        url = "https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/trade/" + file_name

        with requests.get(url) as r:
            with open('data/trade/' + url.split('/')[-1], 'wb') as f:
                f.write(r.content)

    if file_name not in os.listdir("data/quote/"):
        url = "https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/" + file_name

        with requests.get(url) as r:
            with open('data/quote/' + url.split('/')[-1], 'wb') as f:
                f.write(r.content)



