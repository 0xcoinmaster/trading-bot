import logging
import os
import inspect
import sys
import time
from enum import Enum

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from .AVInterface import AVInterval

class Interval(Enum):
        """
        Time intervals for price and technical indicators requests
        """
        MINUTE_1 = 'MINUTE_1'
        MINUTE_2 = 'MINUTE_2'
        MINUTE_3 = 'MINUTE_3'
        MINUTE_5 = 'MINUTE_5'
        MINUTE_10 = 'MINUTE_10'
        MINUTE_15 = 'MINUTE_15'
        MINUTE_30 = 'MINUTE_30'
        HOUR = 'HOUR'
        HOUR_2 = 'HOUR_2'
        HOUR_3 = 'HOUR_3'
        HOUR_4 = 'HOUR_4'
        DAY = 'DAY'
        WEEK = 'WEEK'
        MONTH = 'MONTH'

class Broker():
    """
    This class provides a template interface for all those broker related
    actions/tasks wrapping the actual implementation class internally
    """

    def __init__(self, config, services):
        self.read_configuration(config)
        self.ig_index = services['ig_index']
        self.alpha_vantage = services['alpha_vantage']


    def read_configuration(self, config):
        self.use_av_api = config['general']['use_av_api']
        # AlphaVantage limits to 5 calls per minute
        self.trade_timeout = 12 if self.use_av_api else 2


    def wait_after_trade(self):
        """
        Wait for the required amount of time after a trade call. Depends on
        broker API calls restrictions
        """
        time.sleep(self.trade_timeout)


    def get_open_positions(self):
        """
        **IG INDEX API ONLY**
        Returns the current open positions
        """
        return self.ig_index.get_open_positions()


    def get_market_from_watchlist(self, watchlist_name):
        """
        **IG INDEX API ONLY**
        Return a name list of the markets in the required watchlist
        """
        return self.ig_index.get_market_from_watchlist(watchlist_name)


    def navigate_market_node(self, node_id):
        """
        **IG INDEX API ONLY**
        Return the children nodes of the requested node
        """
        return self.ig_index.navigate_market_node(node_id)


    def get_account_used_perc(self):
        """
        **IG INDEX API ONLY**
        Returns the account used value in percentage
        """
        return self.ig_index.get_account_used_perc()


    def close_all_positions(self):
        """
        **IG INDEX API ONLY**
        Attempt to close all the current open positions
        """
        return self.ig_index.close_all_positions()


    def close_position(self, position):
        """
        **IG INDEX API ONLY**
        Attempt to close the requested open position
        """
        return self.ig_index.close_position(position)


    def trade(self, epic, trade_direction, limit, stop):
        """
        **IG INDEX API ONLY**
        Request a trade of the given market
        """
        return self.ig_index.trade(epic, trade_direction, limit, stop)


    def get_market_info(self, epic):
        """
        Return the last available snapshot of the requested market including
        prices and volume info
        """
        # TODO use AlphaVantage Quote Endpoint call if av enabled
        return self.ig_index.get_market_info(epic)


    def macd_dataframe(self, epic, market_id, interval):
        """
        Return a pandas dataframe containing MACD technical indicator
        for the requested market with requested interval
        """
        if self.use_av_api:
            av_interval = self.to_av_interval(interval)
            if av_interval is None:
                return None
            return self.alpha_vantage.macdext(market_id, interval)
        else:
            return self.ig_index.macd_dataframe(epic, None)
        return None


    def get_prices(self, epic, market_id, interval, data_range):
        """
        Return historic price of the requested market as a dictionary:
            - data = {'high': [], 'low': [], 'close': [], 'volume': []}
        """
        data = {'high': [], 'low': [], 'close': [], 'volume': []}
        if self.use_av_api:
            av_interval = self.to_av_interval(interval)
            if av_interval is None:
                return None

            dataframe = self.alpha_vantage.get_prices(market_id, av_interval)
            if dataframe is None:
                return None

            #dataframe.index = range(len(dataframe)
            data['high'] = dataframe['2. high'].values
            data['low'] = dataframe['3. low'].values
            data['close'] = dataframe['4. close'].values
            data['volume'] = dataframe['5. volume'].values
        else:
            prices = self.ig_index.get_prices(epic, interval.value, data_range)
            if prices is None:
                return None

            for i in prices['prices']:
                if i['highPrice']['bid'] is not None:
                    data['high'].append(i['highPrice']['bid'])
                if i['lowPrice']['bid'] is not None:
                    data['low'].append(i['lowPrice']['bid'])
                if i['closePrice']['bid'] is not None:
                    data['close'].append(i['closePrice']['bid'])
                if isinstance(i['lastTradedVolume'], int):
                    data['volume'].append(int(i['lastTradedVolume']))
        return data


    def to_av_interval(self, interval):
        """
        Convert the Broker Interval to AlphaVantage compatible intervals.
        Return the converted interval or None if a conversion is not available
        """
        if interval == Interval.MINUTE_1:
            return AVInterval.MIN_1
        elif interval == Interval.MINUTE_5:
            return AVInterval.MIN_5
        elif interval == Interval.MINUTE_15:
            return AVInterval.MIN_15
        elif interval == Interval.MINUTE_30:
            return AVInterval.MIN_30
        elif interval == Interval.HOUR:
            return AVInterval.MIN_60
        elif interval == Interval.DAY:
            return AVInterval.DAILY
        elif interval == Interval.WEEK:
            return AVInterval.WEEKLY
        elif interval == Interval.MONTH:
            return AVInterval.MONTHLY
        else:
            logging.error('Unable to convert interval {} to AlphaVantage equivalent'.format(
                interval.value))
            return None
