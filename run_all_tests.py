import json
import os

from delivery_system import run

TEST_CASES_DIR = "test_cases"
REPORTS_DIR = "reports"


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    test_files = sorted(f for f in os.listdir(TEST_CASES_DIR) if f.endswith(".json"))

    print(f"Running {len(test_files)} test case(s)...\n")
    for filename in test_files:
        input_path = os.path.join(TEST_CASES_DIR, filename)
        output_path = os.path.join(REPORTS_DIR, f"report_{filename}")

        with open(input_path) as f:
            total_packages = len(json.load(f)["packages"])

        report = run(input_path, output_path, verbose=False)
        total_delivered = sum(v["packages_delivered"] for k, v in report.items() if k != "best_agent")

        status = "OK" if total_delivered == total_packages else "MISMATCH"
        print(f"[{status}] {filename:<20} packages={total_packages:<3} "
              f"delivered={total_delivered:<3} best_agent={report['best_agent']}")

    print(f"\nAll reports written to {REPORTS_DIR}/")


if __name__ == "__main__":
    main()
