import datetime

import backtrader as bt
import backtrader.analyzers as btanalyzers


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
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.ema10 = bt.indicators.WeightedMovingAverage(
            self.datas[0], period=50)

        self.ema15 = bt.indicators.WeightedMovingAverage(
            self.datas[0], period=150)

        self.ema30 = bt.indicators.WeightedMovingAverage(
            self.datas[0], period=200)

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

        # 上升趋势
        # \
        # and self.ema15[0] <= self.dataclose and self.ema30[0] <= self.dataclose and self.ema10[0] <= self.dataclose
        if self.ema15[-1] < self.ema30[-1] and self.ema15[0] > self.ema30[0]:
            self.order = self.buy()
            # if not self.position:
            #     self.order = self.buy()
            # else:
            #     self.order = self.close()
            #     self.order = self.buy()

        # 下降趋势
        if (self.ema15[-1] > self.ema30[-1] and self.ema15[0] < self.ema30[0]):
            self.order = self.close()

            # if not self.position:
            #     self.order = self.sell()
            # else:
            #     self.order = self.close()
            #     self.order = self.sell()


    def stop(self):
        self.log(u'(金叉死叉有用吗) Ending Value %.2f' %
                 (self.broker.getvalue()))


if __name__ == '__main__':
    # 初始化模型
    cerebro = bt.Cerebro()

    # 构建策略
    strats = cerebro.addstrategy(TestStrategy)
    # Date, Open, High, Low, Close, Adj
    # Close, Volume
    data = bt.feeds.GenericCSVData(
        dataname='NASDAQ.csv',
        fromdate=datetime.datetime(1987, 1, 1),
        todate=datetime.datetime(2023, 7, 21),
        dtformat='%Y-%m-%d',
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=5,
        volume=5,
        openinterest=5
    )
    cerebro.adddata(data)

    # 设定初始资金和佣金
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(0.0005)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=75)

    # 策略执行前的资金
    print('启动资金: %.2f' % cerebro.broker.getvalue())

    # Analyzer
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='SharpeRatio')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='DrawDown')

    # 策略执行
    thestrats = cerebro.run()
    thestrat = thestrats[0]

    print('夏普比率:', thestrat.analyzers.SharpeRatio.get_analysis())
    # print('回撤分析:', thestrat.analyzers.DrawDown.get_analysis())
    print('最大回撤:', thestrat.analyzers.DrawDown.get_analysis()['max']['drawdown'])

    # print('夏普比率:', thestrat.analyzers.SharpRation.get_analysis()['SharpeRatio'])
    # print('最大回撤:', thestrat.analyzers.DrawDown.get_analysis['max']['DrawDown'])

    cerebro.plot()
