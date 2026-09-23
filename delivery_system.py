import argparse
import csv
import json
import math
import random


# ---------------------------------------------------------------------------
# Task 1: Read and parse the JSON file
# ---------------------------------------------------------------------------

def load_data(path):
   
    with open(path, "r") as f:
        raw = json.load(f)

    warehouses = _normalize_locations(raw["warehouses"])
    agents = _normalize_locations(raw["agents"])
    packages = _normalize_packages(raw["packages"])
    return warehouses, agents, packages


def _normalize_locations(obj):
    """Accepts {"id": [x, y], ...} or [{"id": "id", "location": [x, y]}, ...]."""
    if isinstance(obj, dict):
        return {key: tuple(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return {item["id"]: tuple(item["location"]) for item in obj}
    raise ValueError(f"Unsupported location format: {type(obj)}")


def _normalize_packages(raw_packages):
    """Accepts a "warehouse" key or a "warehouse_id" key for each package."""
    packages = []
    for item in raw_packages:
        warehouse_id = item.get("warehouse", item.get("warehouse_id"))
        if warehouse_id is None:
            raise ValueError(f"Package {item.get('id')} has no warehouse reference")
        packages.append({
            "id": item["id"],
            "warehouse": warehouse_id,
            "destination": tuple(item["destination"]),
        })
    return packages


# ---------------------------------------------------------------------------
# Task 2: Euclidean distance + nearest-agent assignment
# ---------------------------------------------------------------------------

def euclidean_distance(point_a, point_b):
    """Straight-line distance between two (x, y) points."""
    return math.sqrt((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2)


def assign_packages(agents, warehouses, packages):
    assignments = {agent_id: [] for agent_id in agents}
    for package in packages:
        warehouse_location = warehouses[package["warehouse"]]
        nearest_agent = min(
            agents,
            key=lambda agent_id: (euclidean_distance(agents[agent_id], warehouse_location), agent_id),
        )
        assignments[nearest_agent].append(package)
    return assignments


# ---------------------------------------------------------------------------
# Task 3: Simulate the day's deliveries
# ---------------------------------------------------------------------------

def simulate_deliveries(agents, warehouses, assignments, delay_probability=0.0, rng=None):
    
    results = {}
    for agent_id, agent_packages in assignments.items():
        current_position = agents[agent_id]
        total_distance = 0.0
        delayed_packages = []

        for package in agent_packages:
            warehouse_location = warehouses[package["warehouse"]]
            total_distance += euclidean_distance(current_position, warehouse_location)
            total_distance += euclidean_distance(warehouse_location, package["destination"])
            current_position = package["destination"]

            # Bonus: random delivery delays
            if rng is not None and rng.random() < delay_probability:
                delayed_packages.append(package["id"])

        delivered = len(agent_packages)
        results[agent_id] = {
            "packages_delivered": delivered,
            "total_distance": round(total_distance, 2),
            "efficiency": round(total_distance / delivered, 2) if delivered else 0.0,
        }
        if rng is not None:
            results[agent_id]["delayed_packages"] = delayed_packages

    return results


# ---------------------------------------------------------------------------
# Task 4: Build the report
# ---------------------------------------------------------------------------

def generate_report(results):
   
    report = dict(results)
    active_agents = {aid: r for aid, r in results.items() if r["packages_delivered"] > 0}
    report["best_agent"] = min(active_agents, key=lambda aid: active_agents[aid]["efficiency"]) if active_agents else None
    return report


# ---------------------------------------------------------------------------
# Task 5: Save the report
# ---------------------------------------------------------------------------

def save_report(report, path="report.json"):
    """Writes the report dict to disk as formatted JSON."""
    with open(path, "w") as f:
        json.dump(report, f, indent=4)


# ---------------------------------------------------------------------------
# Bonus: ASCII visualization of routes
# ---------------------------------------------------------------------------

def visualize_routes_ascii(warehouses, agents, packages, width=50, height=20):
   
    all_points = list(warehouses.values()) + list(agents.values()) + [p["destination"] for p in packages]
    xs, ys = [p[0] for p in all_points], [p[1] for p in all_points]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)

    def scale(value, min_v, max_v, size):
        if max_v == min_v:
            return size // 2
        return int((value - min_v) / (max_v - min_v) * (size - 1))

    grid = [[" "] * width for _ in range(height)]

    def plot(x, y, symbol):
        gx = scale(x, min_x, max_x, width)
        gy = scale(y, min_y, max_y, height)
        row = height - 1 - gy  # flip so higher y draws near the top
        if grid[row][gx] == " ":
            grid[row][gx] = symbol

    for x, y in warehouses.values():
        plot(x, y, "W")
    for x, y in agents.values():
        plot(x, y, "A")
    for package in packages:
        x, y = package["destination"]
        plot(x, y, ".")

    return "\n".join("".join(row) for row in grid)


# ---------------------------------------------------------------------------
# Bonus: a new agent joining mid-day
# ---------------------------------------------------------------------------

def simulate_with_midday_agent(agents, warehouses, packages, new_agent_id, new_agent_location, split_index):
    
    morning_packages = packages[:split_index]
    afternoon_packages = packages[split_index:]

    # --- Morning: original roster only ---
    morning_assignments = assign_packages(agents, warehouses, morning_packages)
    morning_results = simulate_deliveries(agents, warehouses, morning_assignments)

    # Track where every agent ended up after the morning
    current_positions = dict(agents)
    for agent_id, agent_packages in morning_assignments.items():
        if agent_packages:
            current_positions[agent_id] = agent_packages[-1]["destination"]

    # --- New agent joins ---
    current_positions[new_agent_id] = new_agent_location

    # --- Afternoon: expanded roster, using each agent's current position ---
    afternoon_assignments = assign_packages(current_positions, warehouses, afternoon_packages)
    afternoon_results = simulate_deliveries(current_positions, warehouses, afternoon_assignments)

    # --- Merge morning + afternoon stats per agent ---
    merged = {}
    for agent_id in current_positions:
        m = morning_results.get(agent_id, {"packages_delivered": 0, "total_distance": 0.0})
        a = afternoon_results.get(agent_id, {"packages_delivered": 0, "total_distance": 0.0})
        delivered = m["packages_delivered"] + a["packages_delivered"]
        distance = round(m["total_distance"] + a["total_distance"], 2)
        merged[agent_id] = {
            "packages_delivered": delivered,
            "total_distance": distance,
            "efficiency": round(distance / delivered, 2) if delivered else 0.0,
        }

    return generate_report(merged)


# ---------------------------------------------------------------------------
# Bonus: export the top performer to CSV
# ---------------------------------------------------------------------------

def export_top_performer_csv(report, path="top_performer.csv"):
    """Writes the best agent's stats to a small CSV file."""
    best_agent = report.get("best_agent")
    if not best_agent:
        return None
    stats = report[best_agent]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["agent_id", "packages_delivered", "total_distance", "efficiency"])
        writer.writerow([best_agent, stats["packages_delivered"], stats["total_distance"], stats["efficiency"]])
    return path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(input_path, output_path="report.json", delay_probability=0.0, seed=None,
        ascii_map=False, export_csv=False, verbose=True):
    """Runs the full pipeline once and returns the report dict."""
    warehouses, agents, packages = load_data(input_path)

    assignments = assign_packages(agents, warehouses, packages)
    total_assigned = sum(len(pkgs) for pkgs in assignments.values())
    assert total_assigned == len(packages), "Not every package was assigned to an agent!"

    rng = random.Random(seed) if delay_probability > 0 else None
    results = simulate_deliveries(agents, warehouses, assignments, delay_probability, rng)

    total_delivered = sum(r["packages_delivered"] for r in results.values())
    assert total_delivered == len(packages), "Total packages delivered does not match total packages!"

    report = generate_report(results)
    save_report(report, output_path)

    if verbose:
        print(json.dumps(report, indent=4))
        if ascii_map:
            print("\nRoute map (W = warehouse, A = agent start, . = delivery):\n")
            print(visualize_routes_ascii(warehouses, agents, packages))
        if export_csv:
            path = export_top_performer_csv(report)
            if path:
                print(f"\nTop performer exported to {path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="FastBox Mystery Delivery System Simulator")
    parser.add_argument("input", nargs="?", default="data.json", help="Path to the input JSON file")
    parser.add_argument("-o", "--output", default="report.json", help="Path to write the report JSON")
    parser.add_argument("--delay-probability", type=float, default=0.0,
                         help="Bonus: probability (0-1) that a delivered package is randomly delayed")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible delay simulation")
    parser.add_argument("--ascii-map", action="store_true", help="Bonus: print an ASCII visualization of the routes")
    parser.add_argument("--export-csv", action="store_true", help="Bonus: export the top performer to top_performer.csv")
    args = parser.parse_args()

    run(
        input_path=args.input,
        output_path=args.output,
        delay_probability=args.delay_probability,
        seed=args.seed,
        ascii_map=args.ascii_map,
        export_csv=args.export_csv,
    )


if __name__ == "__main__":
    main()
