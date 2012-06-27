# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import unittest
import datetime
import random

from pyalgotrade import broker
from pyalgotrade import bar

class Callback:
	def __init__(self):
		self.eventCount = 0

	def onOrderUpdated(self, broker_, order):
		self.eventCount += 1

class BaseTestCase(unittest.TestCase):
	TestInstrument = "orcl"

	def setUp(self):
		self.__currSeconds = 0

	def buildBars(self, openPrice, highPrice, lowPrice, closePrice, sessionClose = False):
		ret = {}
		dateTime = datetime.datetime.now() + datetime.timedelta(seconds=self.__currSeconds)
		self.__currSeconds += 1
		bar_ = bar.Bar(dateTime, openPrice, highPrice, lowPrice, closePrice, closePrice*10, closePrice)
		bar_.setSessionClose(sessionClose)
		ret[BaseTestCase.TestInstrument] = bar_
		return bar.Bars(ret, dateTime)

class MarketOrderTestCase(BaseTestCase):
	def testBuyAndSell(self):
		brk = broker.Broker(11)

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 1)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 1)

		# Sell
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = broker.MarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 11)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

	def testFailToBuy(self):
		brk = broker.Broker(5)

		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)

		# Fail to buy. No money.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getPendingOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 0)

		# Fail to buy. Canceled.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(11, 15, 8, 12, True))
		self.assertTrue(order.isCanceled())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

	def testBuyAndSell_GTC(self):
		brk = broker.Broker(5)

		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1, True)

		# Fail to buy. No money.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)
		# Set sessionClose to true test that the order doesn't get canceled.
		brk.onBars(self.buildBars(10, 15, 8, 12, True))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getPendingOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 0)

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(2, 15, 1, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 2)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 3)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 1)

	def testBuyAndSellInTwoSteps(self):
		brk = broker.Broker(20.4)

		# Buy
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(round(brk.getCash(), 1) == 0.4)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)

		# Sell
		order = broker.MarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(round(brk.getCash(), 1) == 10.4)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)

		# Sell again
		order = broker.MarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(11, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 11)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(round(brk.getCash(), 1) == 21.4)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)

	def testPortfolioValue(self):
		brk = broker.Broker(11)

		# Buy
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 1)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)

		self.assertTrue(brk.getValue(self.buildBars(11, 11, 11, 11)) == 11 + 1)
		self.assertTrue(brk.getValue(self.buildBars(1, 1, 1, 1)) == 1 + 1)

	def testBuyWithCommission(self):
		brk = broker.Broker(1020, broker.FixedCommission(10))

		# Buy
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 100)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 10)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 100)

	def testSellShort_1(self):
		brk = broker.Broker(1000)

		# Short sell
		order = broker.MarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(200, 200, 200, 200))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 1200)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(brk.getValue(self.buildBars(100, 100, 100, 100)) == 1000 + 100)
		self.assertTrue(brk.getValue(self.buildBars(0, 0, 0, 0)) == 1000 + 200)
		self.assertTrue(brk.getValue(self.buildBars(30, 30, 30, 30)) == 1000 + 170)

		# Buy at the same price.
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(200, 200, 200, 200))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 1000)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)

	def testSellShort_2(self):
		brk = broker.Broker(1000)

		# Short sell 1
		order = broker.MarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getCash() == 1100)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(brk.getValue(self.buildBars(100, 100, 100, 100)) == 1000)
		self.assertTrue(brk.getValue(self.buildBars(0, 0, 0, 0)) == 1000 + 100)
		self.assertTrue(brk.getValue(self.buildBars(70, 70, 70, 70)) == 1000 + 30)
		self.assertTrue(brk.getValue(self.buildBars(200, 200, 200, 200)) == 1000 - 100)

		# Buy 2 and earn 50
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(50, 50, 50, 50))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(brk.getCash() == 1000) # +50 from short sell operation, -50 from buy operation.
		self.assertTrue(brk.getValue(self.buildBars(50, 50, 50, 50)) == 1000 + 50)
		self.assertTrue(brk.getValue(self.buildBars(70, 70, 70, 70)) == 1000 + 50 + 20)

		# Sell 1 and earn 50
		order = broker.MarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(brk.getValue(self.buildBars(70, 70, 70, 70)) == 1000 + 50 + 50)

	def testSellShort_3(self):
		brk = broker.Broker(100)

		# Buy 1
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(brk.getCash() == 0)

		# Sell 2
		order = broker.MarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 2)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(brk.getCash() == 200)

		# Buy 1
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(brk.getCash() == 100)

	def testSellShortWithCommission(self):
		sharePrice = 100
		commission = 10
		brk = broker.Broker(1010, broker.FixedCommission(commission))

		# Sell 10 shares
		order = broker.MarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 10)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(sharePrice, sharePrice, sharePrice, sharePrice))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 10)
		self.assertTrue(brk.getCash() == 2000)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -10)

		# Buy the 10 shares sold short plus 9 extra
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 19)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(sharePrice, sharePrice, sharePrice, sharePrice))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 9)
		self.assertTrue(brk.getCash() == sharePrice - commission)

	def testCancel(self):
		brk = broker.Broker(100)
		order = broker.MarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		order.cancel()
		brk.onBars(self.buildBars(10, 10, 10, 10))
		self.assertTrue(order.isCanceled())

class LimitOrderTestCase(BaseTestCase):
	def testBuyAndSell(self):
		brk = broker.Broker(11)

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = broker.LimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 11, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 11)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 1)

		# Sell
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = broker.LimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 15)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 15)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

	def testFailToBuy(self):
		brk = broker.Broker(5)

		order = broker.LimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 5, 1)

		# Fail to buy (couldn't get specific price).
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getPendingOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 0)

		# Fail to buy. Canceled.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(11, 15, 8, 12, True))
		self.assertTrue(order.isCanceled())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

	def testBuyAndSell_GTC(self):
		brk = broker.Broker(10)

		order = broker.LimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 4, 2, True)

		# Fail to buy (couldn't get specific price).
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)
		# Set sessionClose to true test that the order doesn't get canceled.
		brk.onBars(self.buildBars(10, 15, 8, 12, True))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getPendingOrders()) == 1)
		self.assertTrue(brk.getCash() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 0)

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(2, 15, 1, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 4)
		self.assertTrue(len(brk.getPendingOrders()) == 0)
		self.assertTrue(brk.getCash() == 2)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)
		self.assertTrue(cb.eventCount == 1)

def getTestCases():
	ret = []

	ret.append(MarketOrderTestCase("testBuyAndSell"))
	ret.append(MarketOrderTestCase("testFailToBuy"))
	ret.append(MarketOrderTestCase("testBuyAndSell_GTC"))
	ret.append(MarketOrderTestCase("testBuyAndSellInTwoSteps"))
	ret.append(MarketOrderTestCase("testPortfolioValue"))
	ret.append(MarketOrderTestCase("testBuyWithCommission"))
	ret.append(MarketOrderTestCase("testSellShort_1"))
	ret.append(MarketOrderTestCase("testSellShort_2"))
	ret.append(MarketOrderTestCase("testSellShort_3"))
	ret.append(MarketOrderTestCase("testSellShortWithCommission"))
	ret.append(MarketOrderTestCase("testCancel"))

	ret.append(LimitOrderTestCase("testBuyAndSell"))
	ret.append(LimitOrderTestCase("testFailToBuy"))
	ret.append(LimitOrderTestCase("testBuyAndSell_GTC"))

	return ret
