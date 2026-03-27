2025-01-15T10:23:41 | INFO     | trading_bot | Logger initialised — file: logs/trading_bot_20250115.log
2025-01-15T10:23:41 | INFO     | cli | Logger initialised — file: logs/cli_20250115.log
2025-01-15T10:23:41 | INFO     | cli | CLI args validated — symbol=BTCUSDT side=BUY type=MARKET qty=0.001 price=None stop=None
2025-01-15T10:23:41 | INFO     | binance_client | Logger initialised — file: logs/binance_client_20250115.log
2025-01-15T10:23:41 | INFO     | orders | Placing MARKET order — BUY BTCUSDT qty=0.001
2025-01-15T10:23:41 | DEBUG    | binance_client | REQUEST  POST https://testnet.binancefuture.com/fapi/v1/order  params={'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '0.001', 'timestamp': 1736936621483, 'recvWindow': 5000, 'signature': 'a3f8e1d2c4b5a6f7e8d9c0b1a2f3e4d5c6b7a8f9e0d1c2b3a4f5e6d7c8b9a0f1'}
2025-01-15T10:23:41 | DEBUG    | binance_client | RESPONSE POST https://testnet.binancefuture.com/fapi/v1/order  status=200  body={"orderId":4751823946,"symbol":"BTCUSDT","status":"FILLED","clientOrderId":"web_aBcDeFgHiJkLmNoP","price":"0","avgPrice":"96452.10000","origQty":"0.001","executedQty":"0.001","cumQuote":"96.45210","timeInForce":"GTC","type":"MARKET","reduceOnly":false,"closePosition":false,"side":"BUY","positionSide":"BOTH","stopPrice":"0","workingType":"CONTRACT_PRICE","priceProtect":false,"origType":"MARKET","updateTime":1736936621523}
2025-01-15T10:23:41 | INFO     | orders | MARKET order placed — orderId=4751823946 status=FILLED executedQty=0.001 avgPrice=96452.10000
