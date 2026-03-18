#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import sys
from bot.client import BinanceClient
from bot.logging_config import setup_logging
from bot.orders import OrderResult, build_order_request, place_order
from bot.validators import ValidationError

logger = setup_logging()

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{CYAN}{BOLD}  ╔══════════════════════════════════════════╗")
    print(f"  ║   Binance Spot Testnet Trading Bot       ║")
    print(f"  ╚══════════════════════════════════════════╝{RESET}\n")


def print_request_summary(args):
    print(f"{BOLD}── Order Request ─────────────────────────────{RESET}")
    print(f"  Symbol     : {CYAN}{args.symbol.upper()}{RESET}")
    print(f"  Side       : {GREEN if args.side.upper() == 'BUY' else RED}{args.side.upper()}{RESET}")
    print(f"  Order Type : {args.order_type.upper()}")
    print(f"  Quantity   : {args.quantity}")
    if args.order_type.upper() == "LIMIT":
        print(f"  Price      : {args.price}")
    if args.order_type.upper() == "STOP_LOSS":
        print(f"  Stop Price : {args.stop_price}")
    print()


def print_result(result: OrderResult):
    print(f"{BOLD}── Order Response ────────────────────────────{RESET}")
    if result.success:
        print(f"  {GREEN}{BOLD}✔ Order placed successfully!{RESET}")
        print(f"  Order ID     : {result.order_id}")
        print(f"  Status       : {result.status}")
        print(f"  Executed Qty : {result.executed_qty}")
        print(f"  Avg Price    : {result.avg_price if result.avg_price else 'N/A'}")
    else:
        print(f"  {RED}{BOLD}✘ Order failed.{RESET}")
        print(f"  Reason: {result.error}")
    print()


def main():
    parser = argparse.ArgumentParser(prog="trading_bot")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"])
    parser.add_argument("--type", dest="order_type", required=True,
                        choices=["MARKET", "LIMIT", "STOP_LOSS", "market", "limit", "stop_loss"])
    parser.add_argument("--quantity", required=True, type=float)
    parser.add_argument("--price", type=float, default=None)
    parser.add_argument("--stop-price", dest="stop_price", type=float, default=None)
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    global logger
    logger = setup_logging(args.log_level)

    print_banner()

    api_key = os.environ.get("BINANCE_TESTNET_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(f"{RED}Error: Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET{RESET}")
        sys.exit(1)

    try:
        order_req = build_order_request(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as exc:
        print(f"{RED}Validation error: {exc}{RESET}")
        sys.exit(1)

    print_request_summary(args)

    client = BinanceClient(api_key=api_key, api_secret=api_secret)
    result = place_order(client, order_req)
    print_result(result)

    if not result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()
