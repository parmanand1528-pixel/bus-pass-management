"""
================================================================================
Bus Pass Management System
Author: parmanand1528-pixel
================================================================================
"""

import os
import sys
import csv

# Script Directory and Data File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE_NAME = os.path.join(BASE_DIR, "buspass.txt")
CSV_FILE_NAME = os.path.join(BASE_DIR, "buspass.csv")

# Tariff Catalog: Pass types, validity duration, and standard base fees
PASS_TYPES = {
    "Monthly": {"days": 30, "fee": 500},
    "Quarterly": {"days": 90, "fee": 1350},
    "Yearly": {"days": 365, "fee": 4800}
}

# 25% Concession for students
STUDENT_DISCOUNT = 0.25


def resolve_file_path(filename: str) -> str:
    """Ensures file paths resolve relative to project root."""
    if os.path.isabs(filename):
        return filename
    cwd_path = os.path.join(os.getcwd(), filename)
    script_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(cwd_path) and os.getcwd() != BASE_DIR:
        return cwd_path
    return script_path


def load_passes_from_csv(csv_path: str) -> list:
    """Reads bus pass records directly from a CSV file into memory."""
    passes = []
    try:
        with open(csv_path, "r", encoding="utf-8") as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                fee_raw = str(row.get("Fee", "0")).replace("Rs.", "").replace("Rs", "").strip()
                try:
                    fee_val = float(fee_raw)
                    fee = int(fee_val) if fee_val.is_integer() else fee_val
                except ValueError:
                    fee = 0
                passes.append({
                    "id": str(row.get("Pass_ID", "")).strip(),
                    "name": str(row.get("Name", "")).strip(),
                    "route": str(row.get("Route", "")).strip(),
                    "type": str(row.get("Pass_Type", "")).strip(),
                    "category": str(row.get("Category", "General")).strip(),
                    "fee": fee,
                    "valid_days": int(row.get("Valid_Days", 30))
                })
    except Exception as e:
        print(f"Error reading CSV {csv_path}: {e}", file=sys.stderr)
    return passes


def load_passes(filename: str = DEFAULT_FILE_NAME) -> list:
    """
    Reads bus pass records from disk into memory as a list of dictionaries.
    Supports both pipe-delimited text storage (.txt) and tabular CSV format (.csv).
    """
    filepath = resolve_file_path(filename)
    passes = []

    if not os.path.exists(filepath):
        # Fallback to CSV if text file is not present
        csv_path = resolve_file_path(CSV_FILE_NAME)
        if os.path.exists(csv_path) and os.path.abspath(filepath) == os.path.abspath(DEFAULT_FILE_NAME):
            return load_passes_from_csv(csv_path)
        return passes

    if filepath.lower().endswith(".csv"):
        return load_passes_from_csv(filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 4:
                    continue

                pass_id = parts[0]
                name = parts[1]
                route = parts[2]
                pass_type = parts[3]

                category = "General"
                fee = PASS_TYPES.get(pass_type, {}).get("fee", 0)
                valid_days = PASS_TYPES.get(pass_type, {}).get("days", 30)

                # Parse fee if present
                if len(parts) >= 5:
                    fee_raw = parts[4].replace("Fee:", "").replace("Rs.", "").replace("Rs", "").strip()
                    try:
                        fee_val = float(fee_raw)
                        fee = int(fee_val) if fee_val.is_integer() else fee_val
                    except ValueError:
                        category = parts[4]

                if pass_type in PASS_TYPES:
                    valid_days = PASS_TYPES[pass_type]["days"]
                    base_f = PASS_TYPES[pass_type]["fee"]
                    if abs(fee - (base_f * (1.0 - STUDENT_DISCOUNT))) < 0.01:
                        category = "Student"

                passes.append({
                    "id": pass_id,
                    "name": name,
                    "route": route,
                    "type": pass_type,
                    "category": category,
                    "fee": fee,
                    "valid_days": valid_days
                })
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)

    return passes


def save_passes_csv(passes: list, filename: str = CSV_FILE_NAME) -> None:
    """Atomically exports records to CSV with standard column headers."""
    filepath = resolve_file_path(filename)
    temp_filepath = f"{filepath}.tmp"
    try:
        with open(temp_filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Pass_ID", "Name", "Route", "Pass_Type", "Category", "Fee", "Valid_Days"])
            for p in passes:
                writer.writerow([
                    p.get("id", ""),
                    p.get("name", ""),
                    p.get("route", ""),
                    p.get("type", ""),
                    p.get("category", "General"),
                    p.get("fee", 0),
                    p.get("valid_days", 30)
                ])
        if os.path.exists(filepath):
            os.replace(temp_filepath, filepath)
        else:
            os.rename(temp_filepath, filepath)
    except Exception as e:
        print(f"Error saving CSV: {e}", file=sys.stderr)
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass


def save_passes(passes: list, filename: str = DEFAULT_FILE_NAME) -> None:
    """
    Saves records to pipe-delimited text file or CSV format atomically via a temporary file.
    Automatically synchronizes buspass.csv when saving to default buspass.txt.
    """
    filepath = resolve_file_path(filename)
    if filepath.lower().endswith(".csv"):
        save_passes_csv(passes, filepath)
        return

    temp_filepath = f"{filepath}.tmp"
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            for p in passes:
                fee_display = f"Rs. {p['fee']}"
                f.write(f"{p['id']} | {p['name']} | {p['route']} | {p['type']} | {fee_display}\n")

        if os.path.exists(filepath):
            os.replace(temp_filepath, filepath)
        else:
            os.rename(temp_filepath, filepath)

        # Mirror updates to CSV database
        if os.path.abspath(filepath) == os.path.abspath(DEFAULT_FILE_NAME):
            save_passes_csv(passes, CSV_FILE_NAME)
    except Exception as e:
        print(f"Error saving {filepath}: {e}", file=sys.stderr)
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass


def generate_next_id(passes: list) -> str:
    """Computes next sequential pass ID starting from 'BP101'."""
    if not passes:
        return "BP101"

    max_num = 100
    for p in passes:
        pid = p.get("id", "").strip().upper()
        if pid.startswith("BP"):
            suffix = pid[2:]
            if suffix.isdigit():
                num = int(suffix)
                if num > max_num:
                    max_num = num

    return f"BP{max_num + 1}"


def calculate_fee(pass_type: str, category: str) -> tuple:
    """
    Calculates final fee and duration days based on pass tier and passenger category.
    Returns: (fee, valid_days)
    """
    info = PASS_TYPES[pass_type]
    base_fee = info["fee"]
    days = info["days"]

    if category.strip().capitalize() == "Student":
        discounted = base_fee * (1.0 - STUDENT_DISCOUNT)
        fee = int(discounted) if discounted.is_integer() else round(discounted, 2)
    else:
        fee = base_fee

    return fee, days


def normalize_pass_type(raw_type: str):
    """Validates and normalizes pass type."""
    if not raw_type:
        return None
    cleaned = raw_type.replace("Type:", "").replace("Type", "").strip()
    for valid in PASS_TYPES:
        if cleaned.lower() == valid.lower():
            return valid
    mapping = {
        "1": "Monthly",
        "m": "Monthly",
        "monthly": "Monthly",
        "2": "Quarterly",
        "q": "Quarterly",
        "quarterly": "Quarterly",
        "3": "Yearly",
        "y": "Yearly",
        "yearly": "Yearly"
    }
    cleaned_lower = cleaned.lower()
    if cleaned_lower in mapping:
        return mapping[cleaned_lower]
    return None


def normalize_category(raw_cat: str):
    """Validates and normalizes passenger category."""
    if not raw_cat:
        return None
    cleaned = raw_cat.replace("Category:", "").replace("Category", "").strip().lower()
    if cleaned in ["general", "gen", "g", "1"]:
        return "General"
    if cleaned in ["student", "stud", "s", "2"]:
        return "Student"
    return None


def issue_pass(passes: list, name: str = None, route: str = None,
               pass_type: str = None, category: str = None,
               filename: str = DEFAULT_FILE_NAME) -> dict:
    """Issue a new commuter bus pass with input validation and fee calculation."""
    if name is None:
        try:
            name = input("Name: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return None
    if route is None:
        try:
            route = input("Route: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return None
    if pass_type is None:
        try:
            pass_type = input("Type: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return None
    if category is None:
        try:
            category = input("Category: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return None

    name = name.replace("Name:", "").strip()
    route = route.replace("Route:", "").strip()

    if not name:
        print("Name cannot be empty. Pass not issued.")
        return None
    if not route:
        print("Route cannot be empty. Pass not issued.")
        return None

    valid_type = normalize_pass_type(pass_type)
    if not valid_type:
        print("Invalid pass type. Choose Monthly, Quarterly or Yearly. Pass not issued.")
        return None

    valid_cat = normalize_category(category)
    if not valid_cat:
        print("Invalid category. Choose Student or General. Pass not issued.")
        return None

    pass_id = generate_next_id(passes)
    fee, valid_days = calculate_fee(valid_type, valid_cat)

    new_pass = {
        "id": pass_id,
        "name": name,
        "route": route,
        "type": valid_type,
        "category": valid_cat,
        "fee": fee,
        "valid_days": valid_days
    }
    passes.append(new_pass)
    save_passes(passes, filename)

    print(f"Pass issued. ID: {pass_id} | {name} | {route} | {valid_type} | Fee: Rs. {fee} | Valid: {valid_days} days")
    return new_pass


def renew_pass(passes: list, pass_id: str = None, new_type: str = None,
               category: str = None, filename: str = DEFAULT_FILE_NAME) -> dict:
    """Renew an existing pass by updating duration tier and recalculating fee."""
    if pass_id is None:
        try:
            pass_id = input("Enter Pass ID to renew: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return None

    if not pass_id:
        print("Pass ID cannot be empty. Pass not renewed.")
        return None

    search_key = pass_id.replace("ID:", "").replace("ID", "").strip().upper()
    target = None
    for p in passes:
        if p["id"].strip().upper() == search_key:
            target = p
            break

    if not target:
        print(f"Pass ID {pass_id} not found.")
        return None

    if new_type is None:
        try:
            new_type = input(f"Enter Pass Type (Monthly/Quarterly/Yearly) [Current: {target['type']}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return None
        if not new_type:
            new_type = target["type"]

    if category is None:
        try:
            category = input(f"Enter Category (General/Student) [Current: {target['category']}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return None
        if not category:
            category = target["category"]

    valid_type = normalize_pass_type(new_type)
    if not valid_type:
        print("Invalid pass type. Choose Monthly, Quarterly or Yearly. Pass not renewed.")
        return None

    valid_cat = normalize_category(category)
    if not valid_cat:
        print("Invalid category. Choose Student or General. Pass not renewed.")
        return None

    fee, valid_days = calculate_fee(valid_type, valid_cat)

    target["type"] = valid_type
    target["category"] = valid_cat
    target["fee"] = fee
    target["valid_days"] = valid_days

    save_passes(passes, filename)
    print(f"Pass renewed. ID: {target['id']} | {target['name']} | {target['route']} | {valid_type} | Fee: Rs. {fee} | Valid: {valid_days} days")
    return target


def search_pass(passes: list, pass_id: str = None) -> dict:
    """Search for a pass by ID (case-insensitive) and display details."""
    if pass_id is None:
        try:
            pass_id = input("Enter Pass ID: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return None

    if not pass_id:
        print("Pass ID cannot be empty.")
        return None

    search_key = pass_id.replace("ID:", "").replace("ID", "").strip().upper()
    for p in passes:
        if p["id"].strip().upper() == search_key:
            print(f"{p['id']} | {p['name']} | {p['route']} | {p['type']} | Fee: Rs. {p['fee']}")
            return p

    print(f"Pass with ID {pass_id} not found.")
    return None


def view_all_passes(passes: list) -> None:
    """Displays all issued passes in formatted tabular rows."""
    if not passes:
        print("No passes issued yet.")
        return

    for p in passes:
        print(f"{p['id']} | {p['name']} | {p['route']} | {p['type']} | Fee: Rs. {p['fee']}")


def display_menu():
    """Displays interactive application menu."""
    print("\n" + "=" * 55)
    print("             BUS PASS MANAGEMENT SYSTEM")
    print("=======================================================")
    print("1. Issue New Pass")
    print("2. Renew Existing Pass")
    print("3. Search Pass by ID")
    print("4. View All Passes")
    print("5. Exit")
    print("=" * 55)


def run_self_tests() -> int:
    """Executes the automated acceptance test suite verifying all 5 test scenarios."""
    import unittest
    import io
    from contextlib import redirect_stdout

    test_file = os.path.join(BASE_DIR, "test_buspass_tmp.txt")

    class TestSuite(unittest.TestCase):
        def setUp(self):
            if os.path.exists(test_file):
                os.remove(test_file)

        def tearDown(self):
            if os.path.exists(test_file):
                os.remove(test_file)

        def test_case_1_normal_input(self):
            passes = []
            res = issue_pass(passes, name="Riya", route="Route 5", pass_type="Monthly", category="General", filename=test_file)
            self.assertIsNotNone(res)
            self.assertEqual(res["id"], "BP101")
            self.assertEqual(res["fee"], 500)
            self.assertEqual(res["valid_days"], 30)

        def test_case_2_boundary_minimum_input(self):
            passes = []
            captured = io.StringIO()
            with redirect_stdout(captured):
                view_all_passes(passes)
            self.assertEqual(captured.getvalue().strip(), "No passes issued yet.")

        def test_case_3_invalid_input(self):
            passes = []
            res = issue_pass(passes, name="Aman", route="Route 7", pass_type="Weekly", category="General", filename=test_file)
            self.assertIsNone(res)
            self.assertEqual(len(passes), 0)

        def test_case_4_different_valid_scenario(self):
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("BP101 | Riya | Route 5 | Monthly | Rs. 500\n")
            passes = load_passes(test_file)
            res = issue_pass(passes, name="Aman", route="Route 7", pass_type="Yearly", category="Student", filename=test_file)
            self.assertEqual(res["id"], "BP102")
            self.assertEqual(res["fee"], 3600)
            self.assertEqual(res["valid_days"], 365)
            s_res = search_pass(passes, "BP101")
            self.assertIsNotNone(s_res)
            self.assertEqual(s_res["name"], "Riya")

        def test_renew_pass_feature(self):
            passes = [{"id": "BP101", "name": "Riya", "route": "Route 5", "type": "Monthly", "category": "General", "fee": 500, "valid_days": 30}]
            renewed = renew_pass(passes, pass_id="BP101", new_type="Quarterly", category="Student", filename=test_file)
            self.assertIsNotNone(renewed)
            self.assertEqual(renewed["fee"], 1012.5)
            self.assertEqual(renewed["valid_days"], 90)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    return 0 if res.wasSuccessful() else 1


def main():
    """Main interactive driver loop with multi-dataset support."""
    data_file = DEFAULT_FILE_NAME
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        data_file = resolve_file_path(sys.argv[1])

    passes = load_passes(data_file)

    while True:
        display_menu()
        try:
            choice = input("Enter your choice (1-5): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting application. Goodbye!")
            break

        choice_clean = choice.lower().replace("-", " ").strip()

        if (
            choice_clean in ["1", "issue", "issue new pass", "issue pass"]
            or choice_clean.startswith("1.")
            or choice_clean.startswith("1 ")
            or choice_clean == "1"
        ):
            print("\n--- Issue New Pass ---")
            issue_pass(passes, filename=data_file)
        elif (
            choice_clean in ["2", "renew", "renew pass", "renew existing pass"]
            or choice_clean.startswith("2.")
            or choice_clean.startswith("2 ")
            or choice_clean == "2"
        ):
            print("\n--- Renew Pass ---")
            renew_pass(passes, filename=data_file)
        elif (
            choice_clean in ["3", "search", "search pass", "search pass by id"]
            or choice_clean.startswith("3.")
            or choice_clean.startswith("3 ")
            or choice_clean == "3"
        ):
            print("\n--- Search Pass by ID ---")
            search_pass(passes)
        elif (
            choice_clean in ["4", "view", "view all", "view all passes"]
            or choice_clean.startswith("4.")
            or choice_clean.startswith("4 ")
            or choice_clean == "4"
        ):
            print("\n--- View All Passes ---")
            view_all_passes(passes)
        elif (
            choice_clean in ["5", "exit", "quit", "q", "close"]
            or choice_clean.startswith("5.")
            or choice_clean.startswith("5 ")
            or choice_clean == "5"
        ):
            print("\nThank you for using Bus Pass Management System. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["--test", "-t", "test"]:
        sys.exit(run_self_tests())
    else:
        main()
