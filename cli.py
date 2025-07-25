import argparse
from black_scholes import black_scholes_price

def main():
    parser = argparse.ArgumentParser(description="Black-Scholes Option Pricer")
    parser.add_argument("--S", type=float, required=True, help="Spot price of the underlying asset")
    parser.add_argument("--K", type=float, required=True, help="Strike price")
    parser.add_argument("--T", type=float, required=True, help="Time to maturity in years")
    parser.add_argument("--r", type=float, required=True, help="Risk-free interest rate (annualized, decimal)")
    parser.add_argument("--sigma", type=float, required=True, help="Volatility (annualized, decimal)")
    parser.add_argument("--type", choices=["call", "put"], default="call", help="Option type: call or put")
    args = parser.parse_args()

    price = black_scholes_price(
        S=args.S,
        K=args.K,
        T=args.T,
        r=args.r,
        sigma=args.sigma,
        option_type=args.type
    )
    print(f"{args.type.capitalize()} option price: {price:.4f}")

if __name__ == "__main__":
    main() 