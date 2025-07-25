import timeit
from black_scholes import black_scholes_price
from model_comparison import binomial_tree_price, monte_carlo_price

S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
option_type = "call"

print("Benchmarking option pricers (S=100, K=100, T=1, r=0.05, sigma=0.2, call)")

bs_time = timeit.timeit(lambda: black_scholes_price(S, K, T, r, sigma, option_type), number=1000)
print(f"Black-Scholes: {bs_time:.4f} sec (1000 runs)")

bt_time = timeit.timeit(lambda: binomial_tree_price(S, K, T, r, sigma, option_type), number=10)
print(f"Binomial Tree: {bt_time:.4f} sec (10 runs)")

mc_time = timeit.timeit(lambda: monte_carlo_price(S, K, T, r, sigma, option_type), number=10)
print(f"Monte Carlo: {mc_time:.4f} sec (10 runs)") 