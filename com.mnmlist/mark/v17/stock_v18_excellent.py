import datetime
import os

import backtrader as bt
import backtrader.analyzers as btanalyzers
import talib


# index_data = bt.feeds.GenericCSVData(
#     dataname='data/yahoo/' + "NASDAQ.csv",
#     fromdate=datetime.datetime(2010, 1, 1),
#     todate=datetime.datetime(2023, 7, 21),
#     dtformat='%Y-%m-%d',
#     datetime=0,
#     open=1,
#     high=2,
#     low=3,
#     close=4,
#     volume=5,
#     openinterest=5
# )


def get_delta_day(d1, d2):
    d1 = datetime.datetime.strptime(d1, '%Y-%m-%d')
    d2 = datetime.datetime.strptime(d2, '%Y-%m-%d')
    delta = d1 - d2
    return delta.days

def up_trend(self):
    count = 0
    pre = self.ema2[0]
    for i in range(1, 10):
        cur = self.ema2[-i]
        if pre >= cur:
            count = count + 1
        pre = cur
    return count >= 6

def down_trend(self):
    count = 0
    pre = self.ema2[0]
    for i in range(1, 13):
        cur = self.ema2[-i]
        if pre <= cur:
            count = count + 1
        pre = cur
    return count >= 10


class TestStrategy(bt.Strategy):
    """
    继承并构建自己的bt策略
    """

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self, params=None):
        # 初始化相关数据
        self.dataclose = self.datas[0].close
        # self.index_close = self.datas[1].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.global_sell_date = ''
        self.latest_sell_date = ''
        self.global_buy_price = self.dataclose
        self.ema2 = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=10)

        self.ema4 = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=20)

        self.ema10 = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=50)

        self.ema15 = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=150)

        self.ema30 = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=200)

        # self.index_ema10 = bt.indicators.ExponentialMovingAverage(
        #     self.datas[1], period=50)
        #
        # self.index_ema15 = bt.indicators.ExponentialMovingAverage(
        #     self.datas[1], period=150)
        #
        # self.index_ema30 = bt.indicators.ExponentialMovingAverage(
        #     self.datas[1], period=200)
        self.ao = bt.indicators.AwesomeOscillator()
        # self.ao_year_high = bt.ind.Highest(self.ao, period=130)
        self.close_10day_high = bt.ind.Highest(self.dataclose, period=2)
        self.close_10day_low = bt.ind.Lowest(self.dataclose, period=2)
        self.cut_price = -1

        # self.mo = bt.indicators.MomentumOscillator()
        self.rmi = bt.indicators.RSI_EMA()
        # self.MACDHisto = bt.indicators.MACDHisto()
        # self.MACD = bt.indicators.MACD()
        self.close_month_high = bt.ind.Highest(self.dataclose, period=20)
        # self.ao_month_high = bt.ind.Highest(self.ao, period=260)


        # real = MFI(df.high, df.low, df.close, df.volume, timeperiod=14)
        # self.mfi = bt.talib.MFI(self.datas[0].high, self.datas[0].low, self.datas[0].close, self.datas[0].volume)
        # self.ULTOSC = bt.talib.ULTOSC(self.datas[0].high, self.datas[0].low, self.datas[0].close)
        # self.ADOSC = bt.talib.ADOSC(self.datas[0].high, self.datas[0].low, self.datas[0].close, self.datas[0].volume, fastperiod=5, slowperiod=10)
        # self.OBV = bt.talib.OBV(self.datas[0].close, self.datas[0].volume)
        # self.willr = bt.talib.WILLR(self.datas[0].high, self.datas[0].low, self.datas[0].close, timeperiod=20)


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f, cash %.2f, value %.2f, close %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm, cerebro.broker.getcash(), cerebro.broker.getvalue(), self.dataclose[0]))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.bar_executed_close = self.dataclose[0]
                self.global_buy_price = order.executed.price
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f, cash %.2f, value %.2f, close %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm, cerebro.broker.getcash(), cerebro.broker.getvalue(), self.dataclose[0]))

                print("sell_date:{}".format(self.global_sell_date))
                self.latest_sell_date = str(self.datas[0].datetime.date(0))
                self.cut_price = -1
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f, cash %.2f, value %.2f, close %.2f' %
                 (trade.pnl, trade.pnlcomm, cerebro.broker.getcash(), cerebro.broker.getvalue(), self.dataclose[0]))

    def next(self):
        # 记录收盘价
        # self.log('现金{}, 总金额{}, Close{}'.format(cerebro.broker.getcash(), cerebro.broker.getvalue(), self.dataclose[0]))

        # 是否正在下单，如果是的话不能提交第二次订单
        if self.order:
            return

        # index_10 = self.index_ema10[0]
        # index_15 = self.index_ema15[0]
        # index_30 = self.index_ema30[0]
        # index_close = self.index_close[0]
        self.cut_price = max(self.cut_price, self.dataclose * 0.80)

        if self.position:
            on_down_trend = down_trend(self)
            if on_down_trend:
                self.order = self.close()
            if self.close_10day_high / self.dataclose > 1.15:
                self.order = self.close()
            if self.dataclose < self.cut_price:
                # self.global_sell_date = str(self.datas[0].datetime.date(0))
                self.order = self.close()
            elif (self.ema10[-1] > self.ema30[-1] and self.ema10[0] < self.ema30[0]):
                self.order = self.close()
            elif self.dataclose < self.ema15[0]:
                # self.global_sell_date = str(self.datas[0].datetime.date(0))
                self.order = self.close()
            elif self.dataclose > self.ema30 and (self.dataclose - self.ema30)/self.dataclose > 0.6:
                self.order = self.close()
            # elif self.close_10day_high > self.dataclose and (self.close_10day_high - self.dataclose) / self.dataclose > 0.20:
            #     self.order = self.close()
        else:
            cur_date = str(self.datas[0].datetime.date(0))
            latest_sell_date = self.latest_sell_date
            if latest_sell_date == "":
                self.latest_sell_date = cur_date
            latest_delta_day = get_delta_day(cur_date, self.latest_sell_date)
            if latest_delta_day != '' and latest_delta_day < 10:
                return
            # 价格小于长期均线，观望
            if self.dataclose < self.ema30 or self.dataclose < self.ema15:
                return
            if self.rmi <= 30 or self.rmi >= 75:
                return
            if self.dataclose > self.ema30 and (self.dataclose - self.ema30)/self.dataclose > 0.5:
                return

            if self.dataclose < self.close_month_high and (self.close_month_high - self.dataclose) / self.dataclose > 0.20:
                return
            # in_up_trend = bool(up_trend(self))
            # if not in_up_trend:
            #     return

            if self.dataclose / self.close_10day_low > 1.15:
                return

            # MACD穿越
            if self.ema10[-1] < self.ema30[-1] and self.ema10[0] > self.ema30[0]\
                    and self.dataclose > self.ema30[0] and self.dataclose > self.ema15[0] and self.dataclose > self.ema10[0]:
                print("Cross Over match, ema10[-1]:{}, self.ema30[-1]:{}, self.ema10[0]:{}, self.ema30[0]:{}".format(
                    self.ema10[-1], self.ema30[-1], self.ema10[0], self.ema30[0]))
                self.order = self.buy()
            elif self.dataclose > self.ema30[0] and self.dataclose > self.ema15[0] and self.dataclose > self.ema10[0]\
                    and self.ema10[0] > self.ema30[0] and self.ema10[0] > self.ema15[0]:
                self.order = self.buy()
            elif self.ao[-1] < 0 and self.ao[0] > 0:
                if self.ao[-5] * self.ao[-20] > 0:
                    print("AO match, date:{}, self.ao[-1]:{}, self.ao[0]:{}, self.ao[-5]:{},self.ao[-20]:{}".format(
                        self.datas[0].datetime.date(0), self.ao[-1], self.ao[0], self.ao[-5], self.ao[-20]))
                    self.order = self.buy()

    def stop(self):
        self.log(u'(金叉死叉有用吗) Ending Value %.2f' %
                 (self.broker.getvalue()))


if __name__ == '__main__':
    result_file_name = "/Users/sting/PycharmProjects/trade/com.mnmlist/mark/v17/result-v18-all-sp500.csv"
    file = open(result_file_name, "w")

    good_stocks = ["NVDA", "ENPH", "IDXX", "MSFT", "GNRC", "CZR", "AAPL", "CPRT", "LRCX", "ALGN", "EPAM", "SEDG",
                   "CDNS", "TSLA", "AMD", "MSCI", "ETSY", "ANET", "WST", "DXCM", "MRNA", "SNPS", "AMAT", "CTAS", "BIO",
                   "STLD", "ADBE", "POOL", "PWR", "ANSS", "MU", "MPC", "LYV", "SPGI", "FTNT", "MCO", "TTWO", "URI",
                   "MTCH", "PYPL", "LLY", "INTU", "PAYC", "MSI", "DHI", "ODFL", "AJG", "BX", "CSGP", "ISRG", "CDW",
                   "DVN", "ON", "BRO", "PGR", "ROK", "CMA", "KEYS", "TER", "MS", "FDX", "TT", "META", "NFLX", "ACN",
                   "PTC", "ACGL", "NTAP", "GRMN", "VLO", "ZTS", "LW", "NASDAQ", "ETN", "CMG", "CHTR", "ZBRA", "TDG",
                   "AXON", "AMZN", "PNC", "BLK", "GOOG", "JPM", "NOW", "TGT", "TEL", "CRL", "MPWR", "SCHW", "AME",
                   "FICO", "NSC", "TXT", "SHW", "EL", "COST", "AVGO", "MTD", "AMP", "GOOGL", "BBWI", "TRMB", "COP",
                   "TECH", "CTLT", "LEN", "ABBV", "TYL", "FSLR", "NOC", "ALB", "ITW", "ORLY", "BR", "TRGP", "MMC",
                   "RJF", "DE", "CAT", "CBRE", "PODD", "DXC", "KLAC", "NVR", "BAC", "ZION", "HD", "NXPI", "DHR", "OXY",
                   "FITB", "ADSK", "GWW", "ROL", "MRO", "DRI", "RSG", "VRSK", "CF", "CSX", "APH", "ADM", "DOV", "STX",
                   "CRM", "TXN", "UNH", "V", "BABA", "PDD"]
    good_stock_set = set(good_stocks)
    result_lines = []
    result_lines.append("ticker,cash,value,sharpeRatio,drawDown,bonusRatio\n")
    file_names = os.listdir("../data/yahoo")
    for file_name in file_names:
    # for file_name in ["AAPL.csv", "NVDA.csv", "GOOGL.csv", "MSFT.csv", "TSLA.csv", "NFLX.csv","ENPH.csv","ADBE.csv", "BABA.csv", "PDD.csv"]:
    # for file_name in ["BABA.csv"]:
        ticker = file_name.strip(".csv")
        # if ticker not in good_stock_set:
        #     print(ticker + "*******not in good stock *******")
        #     continue
        # print("******IN GOOD STOCK********" + file_name)

        # 初始化模型
        cerebro = bt.Cerebro()

        # 构建策略
        strats = cerebro.addstrategy(TestStrategy)
        # Date, Open, High, Low, Close, Volume, Dividends, Stock
        # Splits
        data = bt.feeds.GenericCSVData(
            dataname='../data/yahoo/' + file_name,
            fromdate=datetime.datetime(2010, 1, 1),
            todate=datetime.datetime(2023, 7, 21),
            dtformat='%Y-%m-%d',
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=5,
            openinterest=5
        )
        cerebro.adddata(data)
        # cerebro.adddata(index_data)

        # 设定初始资金和佣金
        cerebro.broker.setcash(1000000.0)
        cerebro.broker.setcommission(0.0005)
        cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

        # 策略执行前的资金
        print('启动资金: %.2f' % cerebro.broker.getvalue())

        # Analyzer
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='SharpeRatio')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name='DrawDown')

        try:
            thestrats = cerebro.run(maxcpus=4)
            thestrat = thestrats[0]
            sharp_radio = round(thestrat.analyzers.SharpeRatio.get_analysis()['sharperatio'], 2)
            max_retreat = round(thestrat.analyzers.DrawDown.get_analysis()['max']['drawdown'], 2)
            bonus_rate = round((cerebro.broker.getvalue() / 1000000 - 1) * 100, 2)
            print('ticker:{}, 夏普比率:{},最大回撤:{}%,收益:{}%'.format(ticker, sharp_radio, max_retreat, bonus_rate))

            execute_result = "{},{},{},{},{},{}%\n".format(ticker, round(cerebro.broker.getcash()),
                                                           round(cerebro.broker.getvalue()), sharp_radio, max_retreat,
                                                           bonus_rate)
            result_lines.append(execute_result)
        except IndexError as error:
            print(error)
        except Exception as ex:
            print(ex)

    file.writelines(result_lines)
    file.flush()
    for ticker_result in result_lines:
        print(ticker_result)
    cerebro.plot()