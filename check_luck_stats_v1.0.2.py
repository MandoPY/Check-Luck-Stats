import requests
import time
import sys
import math

def print_timer(seconds):
    mins, secs = divmod(seconds, 60)
    return f"Next Update: {mins:02}:{secs:02}"

def get_miner_data(wallet):
    url = f"https://luckpool.net/verus/miner/{wallet}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extrair os workers
        raw_workers = data.get("workers", [])
        workers = []
        for w in raw_workers:
            fields = w.split(":")
            if len(fields) >= 4:
                name = fields[0]
                status = fields[3]
                workers.append((name, status))
            else:
                workers.append((w, "desconhecido"))

        return {
            "balance": data.get("balance", "0.00000000"),
            "hashrateString": data.get("hashrateString", "0 H/s"),
            "immature": data.get("immature", "0.00000000"),
            "paid": data.get("paid", "0.00000000"),
            "workers": workers
        }
    except Exception as e:
        return {
            "balance": f"Error: {e}",
            "hashrateString": f"Error: {e}",
            "immature": f"Error: {e}",
            "paid": f"Error: {e}",
            "workers": []
        }

def get_market_data():
    url = "https://luckpool.net/verus/market"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return {
            "rank": str(data.get("rank", "N/A")),
            "price_usd": str(data.get("price_usd", "N/A")),
            "percent_change_1h": str(data.get("percent_change_1h", "0")),
            "percent_change_24h": str(data.get("percent_change_24h", "0")),
            "percent_change_7d": str(data.get("percent_change_7d", "0"))
        }
    except Exception as e:
        return {
            "rank": f"Error: {e}",
            "price_usd": f"Error: {e}",
            "percent_change_1h": f"Error: {e}",
            "percent_change_24h": f"Error: {e}",
            "percent_change_7d": f"Error: {e}"
        }

def color_percent_change(value):
    try:
        val = float(value)
        if val > 0:
            return f"\033[1;32m{value}%\033[0m"
        elif val < 0:
            return f"\033[1;31m{value}%\033[0m"
        else:
            return f"{value}%"
    except:
        return value

# global variables to control workers layouts
base_rows = 0  # quantity of lines defined to first run
all_workers_names = []  # wokers names

def print_workers(current_workers):
    global all_workers_names

    # update global list
    for w_name, w_status in current_workers:
        found = False
        for i, (name, status) in enumerate(all_workers_names):
            if name == w_name:
                # update status if exist
                all_workers_names[i] = (w_name, w_status)
                found = True
                break
        if not found:
            # Novo worker
            all_workers_names.append((w_name, w_status))

    # reorder workers "on" first, "off" later
    on_workers = [w for w in all_workers_names if w[1] == "on"]
    off_workers = [w for w in all_workers_names if w[1] != "on"]
    sorted_workers = on_workers + off_workers

    #  table with 4 fixed lines
    rows = 4
    total_workers = len(sorted_workers)
    cols = math.ceil(total_workers / rows)

    # matrix (4 lines, 'cols')
    matrix = []
    for r in range(rows):
        row = []
        for c in range(cols):
            idx = c * rows + r
            if idx < total_workers:
                row.append(sorted_workers[idx])
            else:
                row.append(("", ""))  # vazio
        matrix.append(row)

    # check max len from work name
    max_len = 0
    for row in matrix:
        for (name, status) in row:
            if len(name) > max_len:
                max_len = len(name)

    print("Workers:")
    for row in matrix:
        line_str = "   "  # empty space to format
        for (name, status) in row:
            if name == "":
                line_str += " " * max_len + "    "
            else:
                # Cor do worker
                if status == "on":
                    color = "\033[1;32m"
                else:
                    color = "\033[1;31m"
                line_str += f"{color}{name}\033[0m".ljust(max_len, ' ') + "    "
        print(line_str.rstrip())

def main():
    wallet = "WALLET"  # change wallet here
    interval = 600  # interval in seconds

    miner_data = get_miner_data(wallet)
    market_data = get_market_data()

    old_miner_data = miner_data.copy()
    old_market_data = market_data.copy()

    # Convert price_usd to float
    try:
        price_usd =float(market_data['price_usd'])
    except:
        price_usd = 0.0

    # convert the value to dolar
    def to_usd(value_str):
        try:
            val = float(value_str)
            return val * price_usd
        except:
            return 0.0

    paid_usd = to_usd(miner_data['paid'])
    balance_usd = to_usd(miner_data['balance'])
    immature_usd = to_usd(miner_data['immature'])

    # format the values to usd with 3 decimals
    paid_usd_str = f"{paid_usd:.3f}"
    balance_usd_str = f"{balance_usd:.3f}"
    immature_usd_str = f"{immature_usd:.3f}"

    # initial print
    print(f"Paid: \033[1;32m{miner_data['paid']} VRSC ( = ${paid_usd_str} )\033[0m")
    print(f"Balance: \033[1;34m{miner_data['balance']} VRSC ( + ${balance_usd_str} )\033[0m")
    print(f"Immature: \033[38;5;208m{miner_data['immature']} VRSC ( ~ ${immature_usd_str} )\033[0m")
    print(f"Hashrate: {miner_data['hashrateString']}")
    print_workers(miner_data['workers'])

    print(f"Rank: {market_data['rank']}")
    print(f"Price(USD): {market_data['price_usd']}")
    print(f"1h Change: {color_percent_change(market_data['percent_change_1h'])}")
    print(f"24h Change: {color_percent_change(market_data['percent_change_24h'])}")
    print(f"7d Change: {color_percent_change(market_data['percent_change_7d'])}")

    # countdown
    for remaining_time in range(interval, 0, -1):
        sys.stdout.write("\033[K")
        print(print_timer(remaining_time), end="\r")
        sys.stdout.flush()
        time.sleep(1)

    while True:
        new_miner_data = get_miner_data(wallet)
        new_market_data = get_market_data()

        # update price_usd
        try:
            price_usd = float(new_market_data['price_usd'])
        except:
            price_usd = 0.0

        paid_usd = to_usd(new_miner_data['paid'])
        balance_usd = to_usd(new_miner_data['balance'])
        immature_usd = to_usd(new_miner_data['immature'])

        paid_usd_str = f"{paid_usd:.3f}"
        balance_usd_str = f"{balance_usd:.3f}"
        immature_usd_str = f"{immature_usd:.3f}"

        # clean screen
        sys.stdout.write("\033[2J\033[H")

        # Paid (green)
        print(f"Paid: \033[1;32m{new_miner_data['paid']} VRSC ( = ${paid_usd_str} )\033[0m")

        # Balance (blue)
        print(f"Balance: \033[1;34m{new_miner_data['balance']} VRSC ( + ${balance_usd_str} )\033[0m")

        # Immature (orange/yellow)
        print(f"Immature: \033[38;5;208m{new_miner_data['immature']} VRSC ( ~ ${immature_usd_str} )\033[0m")

        # Hashrate
        print(f"Hashrate: {new_miner_data['hashrateString']}")

        # Workers
        print_workers(new_miner_data['workers'])

        # Rank
        print(f"Rank: {new_market_data['rank']}")
        
        # Price(USD)
        print(f"Price(USD): {new_market_data['price_usd']}")

        # Percent Changes
        print(f"1h Change: {color_percent_change(new_market_data['percent_change_1h'])}")
        print(f"24h Change: {color_percent_change(new_market_data['percent_change_24h'])}")
        print(f"7d Change: {color_percent_change(new_market_data['percent_change_7d'])}")

        old_miner_data = new_miner_data.copy()
        old_market_data = new_market_data.copy()

        # countdown
        for remaining_time in range(interval, 0, -1):
            sys.stdout.write("\033[K")
            print(print_timer(remaining_time), end="\r")
            sys.stdout.flush()
            time.sleep(1)

if __name__ == "__main__":
    main()
