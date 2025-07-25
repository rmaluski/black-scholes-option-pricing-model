# Black-Scholes Option Pricing Model

[![pytest coverage](https://img.shields.io/badge/coverage-passing-brightgreen)](https://pytest.org/)

A comprehensive Python project for option pricing, analytics, and visualization using the Black-Scholes model and more.

## Performance

- To enable Numba JIT for Black-Scholes, set `USE_NUMBA=1` in your environment:
  ```sh
  set USE_NUMBA=1  # Windows
  export USE_NUMBA=1  # Linux/Mac
  ```
- Run the benchmark script:
  ```sh
  python benchmark.py
  ```

## Testing

- Run all tests and check coverage:
  ```sh
  pytest --cov=.
  ```

<!-- Trigger workflow run -->
