import json
import random
from datetime import datetime, timedelta


def simulate_spot_prices(num_hours=8760):
    spot_prices = []
    for hour in range(num_hours):
        month = (hour // 730) % 12 + 1  # Rough estimation of month based on hour
        if month in [12, 1, 2]:  # Winter
            if 6 <= (hour % 24) <= 9 or 17 <= (hour % 24) <= 20:
                spot_prices.append(random.uniform(8, 20))  # Higher prices in winter peak hours
            else:
                spot_prices.append(random.uniform(2, 10))  # Higher prices in winter off-peak hours
        elif month in [3, 4, 5]:  # Spring
            if 6 <= (hour % 24) <= 9 or 17 <= (hour % 24) <= 20:
                spot_prices.append(random.uniform(5, 15))  # Prices in spring peak hours
            else:
                spot_prices.append(random.uniform(-1, 5))  # Prices in spring off-peak hours
        elif month in [6, 7, 8]:  # Summer
            if 6 <= (hour % 24) <= 9 or 17 <= (hour % 24) <= 20:
                spot_prices.append(random.uniform(4, 12))  # Lower prices in summer peak hours
            else:
                spot_prices.append(random.uniform(-4, 4))  # Lower prices in summer off-peak hours
        else:  # Fall
            if 6 <= (hour % 24) <= 9 or 17 <= (hour % 24) <= 20:
                spot_prices.append(random.uniform(6, 16))  # Prices in fall peak hours
            else:
                spot_prices.append(random.uniform(2, 6))  # Prices in fall off-peak hours
    return spot_prices


def load_consumption_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def parse_time(time_str):
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s


def calculate_costs(consumption_data, spot_prices, fixed_rate, transfer_price, fixed_total):
    total_variable_cost = 0.0
    total_fixed_cost = fixed_total * 100 if fixed_total else 0.0
    peak_prices = []
    off_peak_prices = []

    for co in consumption_data:
        for cpo in co['consumption_periods']:
            start = parse_time(cpo['start_time'])
            stop = parse_time(cpo['stop_time'])
            kw_draw = cpo['kw_draw']
            months = cpo['months']
            for month in months:
                for day in range(30):  # Approximation: 30 days per month
                    for hour in range(24):
                        hour_idx = (month - 1) * 730 + day * 24 + hour
                        if hour_idx >= len(spot_prices):
                            break
                        current_hour = start // 3600 + hour
                        if start <= current_hour < stop or stop < start and (current_hour < stop or current_hour >= start):
                            spot_price = spot_prices[hour_idx]
                            if 6 <= (current_hour % 24) <= 9 or 17 <= (current_hour % 24) <= 20:
                                peak_prices.append(spot_price)
                            else:
                                off_peak_prices.append(spot_price)
                            total_variable_cost += (spot_price + transfer_price) * kw_draw
                            total_fixed_cost += 0 if fixed_total else (fixed_rate + transfer_price) * kw_draw

    highest_variable_price = max(spot_prices)
    lowest_variable_price = min(spot_prices)
    average_peak_price = sum(peak_prices) / len(peak_prices) if peak_prices else 0
    average_off_peak_price = sum(off_peak_prices) / len(off_peak_prices) if off_peak_prices else 0
    total_fixed_cost_euros = total_fixed_cost / 100
    total_variable_cost_euros = total_variable_cost / 100

    return {
        "total_cost_variable_price": total_variable_cost_euros,
        "highest_variable_price": highest_variable_price,
        "lowest_variable_price": lowest_variable_price,
        "average_peak_price": average_peak_price,
        "average_off_peak_price": average_off_peak_price,
        "total_cost_fixed_rate": total_fixed_cost_euros,
        "savings_with_spot_price": total_fixed_cost_euros  - total_variable_cost_euros
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Simulate annual electricity cost.')
    parser.add_argument('--seed', type=int, required=True, help='Seed for RNG')
    parser.add_argument('--fixed_rate', type=float, required=False, help='Fixed rate in euro cents per kwh')
    parser.add_argument('--fixed_total', type=float, required=False, help='Fixed annual total in euros')
    parser.add_argument('--transfer_price', type=float, required=True, help='Base transfer price in euro cents per kwh')
    parser.add_argument('--consumption_file', type=str, required=True, help='JSON file with consumption data')
    
    args = parser.parse_args()

    if not args.fixed_rate and not args.fixed_total:
        raise ValueError("Either fixed_rate or fixed_total must be provided")

    random.seed(args.seed)
    spot_prices = simulate_spot_prices()
    consumption_data = load_consumption_data(args.consumption_file)

    result = calculate_costs(
        consumption_data=consumption_data,
        spot_prices=spot_prices,
        fixed_rate=args.fixed_rate,
        transfer_price=args.transfer_price,
        fixed_total=args.fixed_total,
    )
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
