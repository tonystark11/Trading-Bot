#!/usr/bin/env python3
"""Enhanced Interactive CLI for Binance Spot Testnet Trading Bot."""

from __future__ import annotations

import os
import sys
import time

from bot.client import BinanceClient
from bot.logging_config import setup_logging
from bot.orders import build_order_request, place_order
from bot.validators import ValidationError

logger = setup_logging()

# ── ANSI colours & styles ─────────────────────────────────────────────────────
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

# ── Helpers ───────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    clear()
    print(f"""
{CYAN}{BOLD}
  ╔═══════════════════════════════════════════════════╗
  ║        Binance Spot Testnet Trading Bot           ║
  ║              Interactive Mode  v1.0               ║
  ╚═══════════════════════════════════════════════════╝
{RESET}""")


def divider():
    print(f"{DIM}  {'─' * 51}{RESET}")


def success(msg: str):
    print(f"\n  {GREEN}{BOLD}✔  {msg}{RESET}")


def error(msg: str):
    print(f"\n  {RED}{BOLD}✘  {msg}{RESET}")


def warning(msg: str):
    print(f"\n  {YELLOW}⚠  {msg}{RESET}")


def info(msg: str):
    print(f"  {CYAN}ℹ  {msg}{RESET}")


def prompt(label: str, hint: str = "") -> str:
    hint_str = f" {DIM}({hint}){RESET}" if hint else ""
    return input(f"  {BOLD}{label}{RESET}{hint_str}: ").strip()


def loading(msg: str, duration: float = 1.0):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end = time.time() + duration
    i = 0
    while time.time() < end:
        print(f"\r  {CYAN}{frames[i % len(frames)]}{RESET}  {msg}", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print(f"\r  {GREEN}✔{RESET}  {msg}{'  '}", flush=True)


def menu(title: str, options: list[str]) -> int:
    """Display a numbered menu and return the user's choice (1-based index)."""
    print(f"\n  {BOLD}{CYAN}{title}{RESET}")
    divider()
    for i, opt in enumerate(options, 1):
        print(f"  {BOLD}{YELLOW}[{i}]{RESET}  {opt}")
    divider()
    while True:
        choice = prompt("Enter choice", f"1-{len(options)}")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice)
        error(f"Please enter a number between 1 and {len(options)}.")


def confirm(question: str) -> bool:
    while True:
        ans = prompt(f"{question} [y/n]").lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        error("Please enter y or n.")


# ── Input collection with validation ─────────────────────────────────────────

def ask_symbol() -> str:
    print(f"\n  {BOLD}Step 1 — Trading Pair{RESET}")
    divider()
    info("Common pairs: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT")
    while True:
        sym = prompt("Symbol", "e.g. BTCUSDT").upper()
        if sym and sym.isalnum():
            return sym
        error("Symbol must be alphanumeric with no spaces (e.g. BTCUSDT).")


def ask_side() -> str:
    choice = menu("Step 2 — Order Side", ["BUY  (go long)", "SELL (go short)"])
    return "BUY" if choice == 1 else "SELL"


def ask_order_type() -> str:
    choice = menu(
        "Step 3 — Order Type",
        [
            "MARKET  — execute immediately at current price",
            "LIMIT   — execute only at your specified price",
            "STOP_LOSS — trigger a market sell at a stop price",
        ],
    )
    return ["MARKET", "LIMIT", "STOP_LOSS"][choice - 1]


def ask_quantity() -> float:
    print(f"\n  {BOLD}Step 4 — Quantity{RESET}")
    divider()
    info("Enter the amount in base asset units (e.g. 0.001 BTC)")
    while True:
        raw = prompt("Quantity", "e.g. 0.001")
        try:
            q = float(raw)
            if q <= 0:
                raise ValueError
            return q
        except ValueError:
            error("Quantity must be a positive number (e.g. 0.001).")


def ask_price(order_type: str) -> float | None:
    if order_type != "LIMIT":
        return None
    print(f"\n  {BOLD}Step 5 — Limit Price{RESET}")
    divider()
    info("Order will only execute when market reaches this price.")
    while True:
        raw = prompt("Limit Price", "e.g. 80000")
        try:
            p = float(raw)
            if p <= 0:
                raise ValueError
            return p
        except ValueError:
            error("Price must be a positive number (e.g. 80000).")


def ask_stop_price(order_type: str) -> float | None:
    if order_type != "STOP_LOSS":
        return None
    print(f"\n  {BOLD}Step 5 — Stop Price{RESET}")
    divider()
    info("Order triggers when market price hits this level.")
    while True:
        raw = prompt("Stop Price", "e.g. 70000")
        try:
            sp = float(raw)
            if sp <= 0:
                raise ValueError
            return sp
        except ValueError:
            error("Stop price must be a positive number (e.g. 70000).")


# ── Order summary & confirmation ──────────────────────────────────────────────

def show_summary(symbol, side, order_type, quantity, price, stop_price):
    print(f"\n  {BOLD}{'─'*20} Order Summary {'─'*20}{RESET}")
    side_col = GREEN if side == "BUY" else RED
    print(f"  {'Symbol':<14}: {CYAN}{symbol}{RESET}")
    print(f"  {'Side':<14}: {side_col}{BOLD}{side}{RESET}")
    print(f"  {'Order Type':<14}: {order_type}")
    print(f"  {'Quantity':<14}: {quantity}")
    if price:
        print(f"  {'Limit Price':<14}: ${price:,.2f}")
    if stop_price:
        print(f"  {'Stop Price':<14}: ${stop_price:,.2f}")
    divider()


# ── Result display ────────────────────────────────────────────────────────────

def show_result(result):
    print(f"\n  {BOLD}{'─'*20} Order Result {'─'*21}{RESET}")
    if result.success:
        success("Order placed successfully!")
        print(f"  {'Order ID':<14}: {result.order_id}")
        print(f"  {'Status':<14}: {BOLD}{result.status}{RESET}")
        print(f"  {'Executed Qty':<14}: {result.executed_qty}")
        print(f"  {'Avg Price':<14}: {result.avg_price if result.avg_price and result.avg_price != '0' else 'N/A (pending)'}")
    else:
        error("Order failed!")
        print(f"\n  {RED}Reason: {result.error}{RESET}")
    divider()


# ── Credentials check ─────────────────────────────────────────────────────────

def get_credentials() -> tuple[str, str]:
    api_key = os.environ.get("BINANCE_TESTNET_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(f"\n  {BOLD}API Credentials Not Found{RESET}")
        divider()
        warning("Keys not found in environment variables.")
        info("You can set them now or set them before running.")
        print()
        api_key = prompt("API Key")
        api_secret = prompt("Secret Key")

        if not api_key or not api_secret:
            error("API Key and Secret are required.")
            sys.exit(1)

    return api_key, api_secret


# ── Main flow ─────────────────────────────────────────────────────────────────

def run_once(client: BinanceClient):
    """Run a single order interactively."""
    banner()
    print(f"  {DIM}Place an order on Binance Spot Testnet{RESET}\n")

    symbol     = ask_symbol()
    side       = ask_side()
    order_type = ask_order_type()
    quantity   = ask_quantity()
    price      = ask_price(order_type)
    stop_price = ask_stop_price(order_type)

    show_summary(symbol, side, order_type, quantity, price, stop_price)

    if not confirm("Confirm and place this order?"):
        warning("Order cancelled.")
        return

    loading("Placing order on Binance Testnet...", 1.2)

    try:
        order_req = build_order_request(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValidationError as exc:
        error(f"Validation failed: {exc}")
        return

    result = place_order(client, order_req)
    show_result(result)


def main():
    banner()
    print(f"  {DIM}Welcome! Let's set up your trading session.{RESET}\n")

    api_key, api_secret = get_credentials()

    loading("Connecting to Binance Spot Testnet...", 1.0)
    client = BinanceClient(api_key=api_key, api_secret=api_secret)
    success("Connected successfully!")

    while True:
        run_once(client)

        print()
        choice = menu(
            "What would you like to do next?",
            ["Place another order", "Exit"],
        )
        if choice == 2:
            banner()
            print(f"  {GREEN}{BOLD}Thanks for using the Trading Bot. Goodbye!{RESET}\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
