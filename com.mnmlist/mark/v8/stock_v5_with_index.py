import datetime
import os

import backtrader as bt
import backtrader.analyzers as btanalyzers
import numpy as np

index_data = bt.feeds.GenericCSVData(
    dataname='data/yahoo/' + "NASDAQ.csv",
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

class TestStrategy(bt.Strategy):
    """
    继承并构建自己的bt策略
    """

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        # 初始化相关数据
        self.dataclose = self.datas[0].close
        self.index_close = self.datas[1].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.year_highest = bt.ind.Highest(self.datas[0].high, period=260)
        self.year_lowest = bt.ind.Lowest(self.datas[0].low, period=260)


        self.ema10 = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=50)

        self.ema15 = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=150)

        self.ema30 = bt.indicators.ExponentialMovingAverage(
            self.datas[0], period=200)

        self.index_ema10 = bt.indicators.ExponentialMovingAverage(
            self.datas[1], period=50)

        self.index_ema15 = bt.indicators.ExponentialMovingAverage(
            self.datas[1], period=150)

        self.index_ema30 = bt.indicators.ExponentialMovingAverage(
            self.datas[1], period=200)

        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=150)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=150,
        #                                     subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=150)

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
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f, cash %.2f, value %.2f, close %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm, cerebro.broker.getcash(), cerebro.broker.getvalue(), self.dataclose[0]))
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

        # year_data_close = self.dataclose.get(-1, 260)
        # low_of_52week = 0
        # high_of_52week = 0
        # if len(year_data_close) > 0:
        #     low_of_52week = np.min(year_data_close)
        #     high_of_52week = np.max(year_data_close)
        # 上升趋势    and self.dataclose > low_of_52week * 1.3 and self.dataclose > high_of_52week * 0.75
        index_10 = self.index_ema10[0]
        index_15 = self.index_ema15[0]
        index_30 = self.index_ema30[0]
        index_close = self.index_close[0]
        year_highest_close =  self.year_highest[0]
        year_lowest_close = self.year_lowest[0]
        cur_close = self.dataclose[0]
        if self.position:
            if (self.ema10[-1] > self.ema30[-1] and self.ema10[0] < self.ema30[0]):
                self.order = self.close()
            elif self.dataclose < self.ema15[0]:
                self.order = self.close()
            elif index_10 <= index_30 and index_close <= index_30:
                self.order = self.close()
        else:
            if index_10 < index_30 or index_close < index_30:
                return
            if cur_close < year_highest_close * 0.75 or cur_close < year_lowest_close * 1.3:
                return
            if self.ema10[-1] < self.ema30[-1] and self.ema10[0] > self.ema30[0]:
                self.order = self.buy()
            elif self.dataclose > self.ema30[0] and self.dataclose > self.ema15[0] and self.dataclose > self.ema10[0] \
                    and self.ema10[0] > self.ema30[0] and self.ema10[0] > self.ema15[0] and self.ema15[0] > self.ema30[0]:
                self.order = self.buy()

    def stop(self):
        self.log(u'(金叉死叉有用吗) Ending Value %.2f' %
                 (self.broker.getvalue()))


if __name__ == '__main__':
    result_file_name = "../result.csv"
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
                   "CRM", "TXN", "UNH", "V"]
    good_stock_set = set(good_stocks)
    result_lines = []
    result_lines.append("ticker,cash,value,夏普比率,最大回撤\n")
    file_names = os.listdir("../data/yahoo")
    # for file_name in file_names:
    for file_name in ["AAPL.csv", "NVDA.csv", "GOOGL.csv", "MSFT.csv", "TSLA.csv"]:
        ticker = file_name.strip(".csv")
        if ticker not in good_stock_set:
            print(ticker + "*******not in good stock *******")
            continue
        print("******IN GOOD STOCK********" + file_name)

        # 初始化模型
        cerebro = bt.Cerebro()

        # 构建策略
        strats = cerebro.addstrategy(TestStrategy)
        # Date, Open, High, Low, Close, Volume, Dividends, Stock
        # Splits
        data = bt.feeds.GenericCSVData(
            dataname='data/yahoo/' + file_name,
            fromdate=datetime.datetime(2015, 1, 1),
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
        cerebro.adddata(index_data)

        # 设定初始资金和佣金
        cerebro.broker.setcash(1000000.0)
        cerebro.broker.setcommission(0.0005)
        cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

        # 策略执行前的资金
        print('启动资金: %.2f' % cerebro.broker.getvalue())

        # Analyzer
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='SharpeRatio')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name='DrawDown')

        # 策略执行
        try:
            thestrats = cerebro.run(maxcpus=4)
        except IndexError:
            continue
        else:
            thestrat = thestrats[0]
        sharp_radio = round(thestrat.analyzers.SharpeRatio.get_analysis()['sharperatio'], 2)
        max_retreat = round(thestrat.analyzers.DrawDown.get_analysis()['max']['drawdown'], 2)
        print('ticker:{}, 夏普比率:{},最大回撤:{}%'.format(ticker, sharp_radio, max_retreat))

        execute_result = "{},{},{},{},{}%\n".format(ticker, round(cerebro.broker.getcash()),
                                                    round(cerebro.broker.getvalue()), sharp_radio, max_retreat)
        result_lines.append(execute_result)

    # cerebro.plot()
    file.writelines(result_lines)
    file.flush()
