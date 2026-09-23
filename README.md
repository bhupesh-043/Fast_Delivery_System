# FastBox Mystery Delivery System

A one-day logistics simulator for a fictional delivery company, FastBox.
Reads warehouses, agents, and packages from a JSON file, assigns each
package to the nearest agent, simulates the day's deliveries, and writes
a report showing packages delivered, distance traveled, and the most
efficient agent.

Project layout

delivery_system.py   Core logic (all 5 required tasks + bonus features)
run_all_tests.py      Runs the simulator against every file in test_cases/
data.json              Sample input straight from the assignment PDF
test_cases/            The 10 test cases + base_case.json provided with the assignment
reports/                Output of run_all_tests.py (one report per test case)
report.json             Output of the last delivery_system.py run

## Usage

Run on the default data.json, writes report.json
python delivery_system.py

Run on a specific input file, choose the output path
python delivery_system.py test_cases/test_case_3.json -o my_report.json

Run every provided test case at once
python run_all_tests.py

Bonus features (all optional, off by default)
python delivery_system.py --ascii-map                     # ASCII route map
python delivery_system.py --export-csv                    # top_performer.csv
python delivery_system.py --delay-probability 0.3 --seed 42  # random delays


How it works

1. **Load & parse (`load_data`)** — reads the JSON file with the standard
   `json` module. Two input schemas show up across the provided files
   (dict-style warehouses/agents used in the PDF and all 10 test cases,
   list-style with `"warehouse_id"` used in `base_case.json`), so the
   loader normalizes both into one internal shape.
2. **Assign (`assign_packages`)** — for each package, computes the
   Euclidean distance from every agent's current location to the
   package's warehouse, and assigns the package to the closest agent.
   Ties break alphabetically by agent id for reproducibility.
3. **Simulate (`simulate_deliveries`)** — each agent starts at its listed
   location and, for every package assigned to it (in input order),
   travels *current position → warehouse → destination*, then its
   position updates to that destination. This means distance accumulates
   realistically across the whole day rather than resetting to the
   agent's home base after each package — this is the one real design
   choice in the assignment, called out here in case a different
   interpretation was expected.
4. **Report (`generate_report`)** — per-agent `packages_delivered`,
   `total_distance`, and `efficiency` (distance ÷ packages delivered —
   lower is better), plus `best_agent`: whichever agent has the lowest
   efficiency score among agents who delivered at least one package.
5. **Save (`save_report`)** — writes the report as formatted JSON.

A couple of assertions in `run()` guard the two correctness notes from
the brief: every package must be assigned to exactly one agent, and the
total delivered must equal the total package count.

## Bonus features implemented

- **Random delivery delays** — `--delay-probability` flags a random
  subset of each agent's deliveries as delayed (seeded via `--seed` for
  reproducibility) and lists them under `delayed_packages` in the report.
- **ASCII route visualization** — `--ascii-map` prints a scaled text grid
  showing warehouses (`W`), agent start points (`A`), and package
  destinations (`.`).
- **New agent joining mid-day** — `simulate_with_midday_agent()` splits
  the package list, simulates the first half with the original roster,
  adds a new agent at a given location, then simulates the rest with the
  expanded roster (agent positions carry over between the two halves).
- **Export top performer to CSV** — `--export-csv` writes the best
  agent's stats to `top_performer.csv`.

## Testing

run_all_tests.py runs the simulator against all 11 provided input files
(base_case.json + `test_case_1.json`–`test_case_10.json`) and prints a
pass/fail line per file, checking that every package in the input ends
up delivered. All 11 currently pass.
