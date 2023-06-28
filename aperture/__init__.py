import asyncio
import hashlib
import hmac

import aiohttp
import pandas as pd
import requests


class OptionMarkPriceClient:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://eapi.binance.com"

    def generate_signature(self, params):
        # Concatenate parameters
        ordered_data = ''.join([str(k) + str(v) for k, v in sorted(params.items())])
        message = bytearray(ordered_data, 'utf-8')
        secret = bytearray(self.secret_key, 'utf-8')

        # Create HMAC SHA256 signature
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return signature
    
    def get_exchange_info(self):
        path = '/eapi/v1/exchangeInfo'

        response = requests.get(self.base_url + path)
        return response.json()

    async def get_mark_price(self, session, symbol=None):
        path = '/eapi/v1/mark'

        # Construct parameters
        params = {}
        if symbol:
            params["symbol"] = symbol

        # Add headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        # Send GET request asynchronously
        async with session.get(self.base_url + path + f"?symbol={symbol}", headers=headers) as response:
            # Raise error if request failed
            if response.status != 200:
                raise Exception(f'GET {path} failed with status {response.status}: {response.text}')

            # Return response as JSON
            data = await response.json()
            return data

    async def get_option_chain(self, date, coin, option_type):
        x_info = self.get_exchange_info()
        symbols = [symbol['symbol'] for symbol in x_info['optionSymbols'] if self.filter_options_symbols(symbol, date, coin, option_type)]

        async with aiohttp.ClientSession() as session:
            tasks = [self.get_mark_price(session, symbol=symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks)

        return results

    def filter_options_symbols(self, symbol, date, coin, option_type):
        return symbol['expiryDate'] * 1_000_000 == pd.Timestamp(f"{date} 08").value and symbol['underlying'] == f"{coin}USDT" and symbol['side'] == option_type
    
    async def get_option_chain_df(self, date, coin, option_type):
        res = await self.get_option_chain(date, coin, option_type)
        df = pd.DataFrame([mark[0] for mark in res])
        df['markPrice'] = df['markPrice'].astype(float)
        df['bidIV'] = df['bidIV'].astype(float)
        df['askIV'] = df['askIV'].astype(float)
        df['markIV'] = df['markIV'].astype(float)
        df['delta'] = df['delta'].astype(float)
        df['theta'] = df['theta'].astype(float)
        df['gamma'] = df['gamma'].astype(float)
        df['vega'] = df['vega'].astype(float)
        df['highPriceLimit'] = df['highPriceLimit'].astype(float)
        df['lowPriceLimit'] = df['lowPriceLimit'].astype(float)
        
        df['strike'] = df['symbol'].apply(lambda x: x.split('-')[2]).astype(float)

        return df
