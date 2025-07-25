# API Reference

## POST /price

Request JSON:

```json
{
  "S": 100,
  "K": 100,
  "T": 1,
  "r": 0.05,
  "sigma": 0.2,
  "option_type": "call",
  "q": 0.0
}
```

Response JSON:

```json
{
  "price": 10.45
}
```

## POST /greeks

Request JSON:

```json
{
  "S": 100,
  "K": 100,
  "T": 1,
  "r": 0.05,
  "sigma": 0.2,
  "option_type": "call",
  "q": 0.0
}
```

Response JSON:

```json
{
  "delta": 0.6368,
  "gamma": 0.0188,
  "theta": -0.0176,
  "vega": 0.3752,
  "rho": 0.5323
}
```
