# Smart Crypto Portfolio Manager - Use Cases with Curl Commands

This document provides test cases using `curl` commands to interact with the Smart Crypto Portfolio Manager's agents following the A2A protocol.

## Agent Discovery

### 1. Discover Market Analysis Agent

```bash
curl -X GET http://localhost:8001/api/v1/agent
```

### 2. Discover Trade Execution Agent

```bash
curl -X GET http://localhost:8002/api/v1/agent
```

### 3. Discover Risk Management Agent

```bash
curl -X GET http://localhost:8003/api/v1/agent
```

### 4. Discover Reporting and Analytics Agent

```bash
curl -X GET http://localhost:8004/api/v1/agent
```

## Market Analysis Agent Use Cases

### 1. Analyze Market Trends for BTC/USD

```bash
curl -X POST http://localhost:8001/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "market_analysis",
    "parameters": {
      "crypto_pair": "BTC/USD",
      "timeframe": "1h",
      "indicators": ["RSI", "MACD", "Bollinger"]
    }
  }'
```

### 2. Perform Risk Assessment for a Potential Trade

```bash
curl -X POST http://localhost:8001/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "risk_assessment",
    "parameters": {
      "crypto_pair": "ETH/USD",
      "position_size": 5,
      "entry_price": 3500
    }
  }'
```

### 3. Get Task Status from Market Analysis Agent

```bash
curl -X GET http://localhost:8001/api/v1/tasks/{task_id}
```

## Trade Execution Agent Use Cases

### 1. Execute a Limit Buy Order

```bash
curl -X POST http://localhost:8002/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "capability": "execute_trade",
    "parameters": {
      "exchange": "binance",
      "crypto_pair": "BTC/USD",
      "action": "buy",
      "order_type": "limit",
      "quantity": 0.5,
      "price": 50000
    }
  }'
```

### 2. Execute a Market Sell Order

```bash
curl -X POST http://localhost:8002/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "capability": "execute_trade",
    "parameters": {
      "exchange": "coinbase",
      "crypto_pair": "ETH/USD",
      "action": "sell",
      "order_type": "market",
      "quantity": 2
    }
  }'
```

### 3. Check Order Status

```bash
curl -X POST http://localhost:8002/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "capability": "get_order_status",
    "parameters": {
      "exchange": "binance",
      "order_id": "12345678"
    }
  }'
```

## Risk Management Agent Use Cases

### 1. Assess Trade Risk

```bash
curl -X POST http://localhost:8003/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "assess_trade_risk",
    "parameters": {
      "crypto_pair": "BTC/USD",
      "action": "buy",
      "quantity": 1.5,
      "price": 48000
    }
  }'
```

### 2. Monitor Portfolio Risk

```bash
curl -X POST http://localhost:8003/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "monitor_portfolio_risk",
    "parameters": {
      "metrics": ["value_at_risk", "sharpe_ratio", "exposure", "volatility", "correlation"],
      "threshold_overrides": {
        "value_at_risk": 0.05
      }
    }
  }'
```

## Reporting and Analytics Agent Use Cases

### 1. Generate Daily Performance Report

```bash
curl -X POST http://localhost:8004/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "generate_performance_report",
    "parameters": {
      "time_period": "day",
      "include_metrics": [
        "total_return",
        "daily_returns",
        "drawdowns",
        "volatility",
        "sharpe_ratio"
      ],
      "format": "json"
    }
  }'
```

### 2. Generate Monthly Performance Report in PDF Format

```bash
curl -X POST http://localhost:8004/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "generate_performance_report",
    "parameters": {
      "time_period": "month",
      "include_metrics": [
        "total_return",
        "drawdowns",
        "volatility",
        "sharpe_ratio",
        "trade_statistics",
        "asset_allocation"
      ],
      "format": "pdf"
    }
  }'
```

### 3. Generate Portfolio Valuation Report

```bash
curl -X POST http://localhost:8004/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "generate_portfolio_valuation",
    "parameters": {
      "include_details": true,
      "valuation_currency": "USD",
      "format": "json"
    }
  }'
```

## Multi-Agent Workflow Test

### Complete Trading Workflow

This sequence demonstrates a complete trading workflow across multiple agents:

1. First, analyze the market to identify a trading opportunity:

```bash
curl -X POST http://localhost:8001/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "market_analysis",
    "parameters": {
      "crypto_pair": "ETH/USD",
      "timeframe": "4h",
      "indicators": ["RSI", "MACD", "Bollinger"]
    }
  }'
```

2. Assess risk for the identified trading opportunity:

```bash
curl -X POST http://localhost:8003/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "assess_trade_risk",
    "parameters": {
      "crypto_pair": "ETH/USD",
      "action": "buy",
      "quantity": 3,
      "price": 3200
    }
  }'
```

3. Execute the trade if risk is acceptable:

```bash
curl -X POST http://localhost:8002/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "capability": "execute_trade",
    "parameters": {
      "exchange": "binance",
      "crypto_pair": "ETH/USD",
      "action": "buy",
      "order_type": "limit",
      "quantity": 3,
      "price": 3200
    }
  }'
```

4. Update portfolio valuation after trade execution:

```bash
curl -X POST http://localhost:8004/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "generate_portfolio_valuation",
    "parameters": {
      "include_details": true,
      "valuation_currency": "USD",
      "format": "json"
    }
  }'
```

## Task Management

### 1. Get Task Status

```bash
curl -X GET http://localhost:8001/api/v1/tasks/{task_id}
```

### 2. Get Task Messages

```bash
curl -X GET http://localhost:8001/api/v1/tasks/{task_id}/messages
```

### 3. Send Message to Task

```bash
curl -X POST http://localhost:8001/api/v1/tasks/{task_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "text": "Additional parameters for the analysis",
      "data": {
        "additional_indicators": ["Volume", "OBV"]
      }
    }
  }'
``` 