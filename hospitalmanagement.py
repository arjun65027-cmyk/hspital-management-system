# ==========================================================
#  HOSPITAL MANAGEMENT SYSTEM  (Python + MySQL, console only)
#
#  How to run: open this file in IDLE and press F5.
#  Needs:      pip install mysql-connector-python
#
#  Module 1 : Patient & Prescription Management
#  Module 2 : Emergency Scheduling & Pharmacy
#  Module 3 : Billing & Government Assistance
#
#  Main idea: every service (consultation, test, ER, medicines)
#  adds a CHARGE to the patient's ID. At checkout, all unbilled
#  charges are turned into one final bill.
# ==========================================================

import mysql.connector
from datetime import date, datetime, timedelta

# ---------- CHANGE THESE TO YOUR MYSQL DETAILS ----------
HOST = "localhost"
USER = 1234
PASSWORD = "your_password"
DB_NAME = "hospital_db"
# --------------------------------------------------------

con = None   # connection
cur = None   # cursor


# ==========================================================
#  SECTION A : DATABASE SETUP AND HELPER FUNCTIONS
# ==========================================================

def connect():
    # Connect to MySQL, create the database and tables if needed.
    global con, cur
    con = mysql.connector.connect(host=HOST, user=USER, password=1234)
    cur = con.cursor(dictionary=True, buffered=True)
    cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_NAME)
    cur.execute("USE " + DB_NAME)
    create_tables()
    add_default_tariff()


def create_tables():
    # Creates all tables (only the first time).
    tables = [
        "CREATE TABLE IF NOT EXISTS patients ( " +
            "patient_id VARCHAR(10) PRIMARY KEY, " +
            "name VARCHAR(100) NOT NULL, " +
            "dob DATE, " +
            "gender VARCHAR(10), " +
            "phone VARCHAR(15), " +
            "address VARCHAR(200), " +
            "registered_on DATE " +
            ")",
        "CREATE TABLE IF NOT EXISTS doctors ( " +
            "doctor_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "name VARCHAR(100) NOT NULL, " +
            "specialization VARCHAR(80), " +
            "phone VARCHAR(15), " +
            "consultation_fee DECIMAL(10,2) DEFAULT 0 " +
            ")",
        "CREATE TABLE IF NOT EXISTS medicines ( " +
            "medicine_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "name VARCHAR(100) NOT NULL, " +
            "unit_price DECIMAL(10,2) NOT NULL, " +
            "stock_qty INT DEFAULT 0, " +
            "expiry_date DATE, " +
            "reorder_level INT DEFAULT 10 " +
            ")",
        "CREATE TABLE IF NOT EXISTS appointments ( " +
            "appointment_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "patient_id VARCHAR(10), " +
            "doctor_id INT, " +
            "appt_date DATE, " +
            "appt_time VARCHAR(5), " +
            "status VARCHAR(15) DEFAULT 'Booked', " +
            "FOREIGN KEY (patient_id) REFERENCES patients(patient_id), " +
            "FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS visits ( " +
            "visit_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "patient_id VARCHAR(10), " +
            "doctor_id INT, " +
            "visit_date DATE, " +
            "visit_type VARCHAR(15), " +
            "diagnosis VARCHAR(300), " +
            "FOREIGN KEY (patient_id) REFERENCES patients(patient_id), " +
            "FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS prescriptions ( " +
            "prescription_no VARCHAR(10) PRIMARY KEY, " +
            "visit_id INT, " +
            "patient_id VARCHAR(10), " +
            "doctor_id INT, " +
            "issued_on DATE, " +
            "dispensed VARCHAR(3) DEFAULT 'No', " +
            "FOREIGN KEY (visit_id) REFERENCES visits(visit_id), " +
            "FOREIGN KEY (patient_id) REFERENCES patients(patient_id), " +
            "FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS prescription_items ( " +
            "item_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "prescription_no VARCHAR(10), " +
            "medicine_id INT, " +
            "dosage VARCHAR(30), " +
            "no_of_days INT, " +
            "quantity INT, " +
            "FOREIGN KEY (prescription_no) REFERENCES prescriptions(prescription_no), " +
            "FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS emergency_duty ( " +
            "duty_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "doctor_id INT, " +
            "duty_date DATE, " +
            "start_hour INT, " +
            "end_hour INT, " +
            "FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS pharmacy_receipts ( " +
            "receipt_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "prescription_no VARCHAR(10), " +
            "patient_id VARCHAR(10), " +
            "receipt_date DATE, " +
            "total DECIMAL(10,2), " +
            "FOREIGN KEY (prescription_no) REFERENCES prescriptions(prescription_no), " +
            "FOREIGN KEY (patient_id) REFERENCES patients(patient_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS pharmacy_receipt_items ( " +
            "id INT AUTO_INCREMENT PRIMARY KEY, " +
            "receipt_id INT, " +
            "medicine_id INT, " +
            "qty INT, " +
            "price DECIMAL(10,2), " +
            "FOREIGN KEY (receipt_id) REFERENCES pharmacy_receipts(receipt_id), " +
            "FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS tariff ( " +
            "tariff_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "item_name VARCHAR(100), " +
            "category VARCHAR(20), " +
            "fee DECIMAL(10,2) " +
            ")",
        "CREATE TABLE IF NOT EXISTS govt_schemes ( " +
            "scheme_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "name VARCHAR(100), " +
            "eligibility_rule VARCHAR(255), " +
            "concession_percent DECIMAL(5,2), " +
            "max_amount DECIMAL(10,2) DEFAULT 0 " +
            ")",
        "CREATE TABLE IF NOT EXISTS patient_schemes ( " +
            "id INT AUTO_INCREMENT PRIMARY KEY, " +
            "patient_id VARCHAR(10), " +
            "scheme_id INT, " +
            "card_no VARCHAR(30), " +
            "valid_till DATE, " +
            "FOREIGN KEY (patient_id) REFERENCES patients(patient_id), " +
            "FOREIGN KEY (scheme_id) REFERENCES govt_schemes(scheme_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS bills ( " +
            "bill_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "patient_id VARCHAR(10), " +
            "bill_type VARCHAR(15), " +
            "bill_date DATE, " +
            "total DECIMAL(10,2), " +
            "concession DECIMAL(10,2), " +
            "payable DECIMAL(10,2), " +
            "paid DECIMAL(10,2) DEFAULT 0, " +
            "status VARCHAR(10) DEFAULT 'Pending', " +
            "FOREIGN KEY (patient_id) REFERENCES patients(patient_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS charges ( " +
            "charge_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "patient_id VARCHAR(10), " +
            "charge_type VARCHAR(20), " +
            "description VARCHAR(200), " +
            "amount DECIMAL(10,2), " +
            "charge_date DATE, " +
            "billed VARCHAR(3) DEFAULT 'No', " +
            "bill_id INT NULL, " +
            "FOREIGN KEY (patient_id) REFERENCES patients(patient_id), " +
            "FOREIGN KEY (bill_id) REFERENCES bills(bill_id) " +
            ")",
        "CREATE TABLE IF NOT EXISTS payments ( " +
            "payment_id INT AUTO_INCREMENT PRIMARY KEY, " +
            "bill_id INT, " +
            "amount DECIMAL(10,2), " +
            "pay_mode VARCHAR(15), " +
            "paid_on DATE, " +
            "FOREIGN KEY (bill_id) REFERENCES bills(bill_id) " +
            ")"
    ]
    for sql in tables:
        cur.execute(sql)
    con.commit()


def add_default_tariff():
    # Puts a few standard fees in the tariff table the first time.
    row = get_one("SELECT COUNT(*) AS c FROM tariff")
    if row["c"] == 0:
        items = [
            ("Emergency Room Fee", "ER", 1500),
            ("Blood Test", "Diagnosis", 400),
            ("X-Ray", "Diagnosis", 600),
            ("ECG", "Diagnosis", 350),
            ("Ultrasound", "Diagnosis", 900),
        ]
        for it in items:
            run("INSERT INTO tariff (item_name, category, fee) VALUES (%s, %s, %s)", it)


def run(sql, values=()):
    # Runs an INSERT / UPDATE and saves it. Returns the new auto ID.
    cur.execute(sql, values)
    con.commit()
    return cur.lastrowid


def get_all(sql, values=()):
    # Runs a SELECT and returns all rows.
    cur.execute(sql, values)
    return cur.fetchall()


def get_one(sql, values=()):
    # Runs a SELECT and returns one row (or None).
    cur.execute(sql, values)
    return cur.fetchone()


def rs(amount):
    # Formats a number as money, e.g. Rs. 250.00
    return "Rs. " + format(float(amount or 0), ".2f")


# ---------- input helpers (they keep asking until the input is valid) ----------

def ask(text):
    return input(text).strip()


def ask_int(text):
    while True:
        s = ask(text)
        if s.isdigit():
            return int(s)
        print("Please enter a whole number.")


def ask_float(text):
    while True:
        s = ask(text)
        try:
            v = float(s)
            if v >= 0:
                return v
        except ValueError:
            pass
        print("Please enter a valid amount.")


def ask_date(text, blank_ok=False):
    # Asks for a date as YYYY-MM-DD. Returns '' if blank is allowed.
    while True:
        s = ask(text + " (YYYY-MM-DD): ")
        if s == "" and blank_ok:
            return ""
        try:
            return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            print("Use the format YYYY-MM-DD, example 2026-10-19.")


def ask_date_today(text):
    # Same as ask_date but pressing Enter gives today's date.
    d = ask_date(text + " [Enter = today]", True)
    if d == "":
        d = str(date.today())
    return d


def ask_time(text):
    while True:
        s = ask(text + " (HH:MM, 24-hour): ")
        try:
            return datetime.strptime(s, "%H:%M").strftime("%H:%M")
        except ValueError:
            print("Use 24-hour format HH:MM, example 14:30.")


def ask_patient():
    # Asks for a patient ID. Returns the patient row, or None if not found.
    pid = ask("Patient ID: ").upper()
    p = get_one("SELECT * FROM patients WHERE patient_id = %s", (pid,))
    if p is None:
        print("No patient found with ID", pid)
    return p


def ask_doctor():
    # Shows the doctors, asks for an ID. Returns the doctor row or None.
    if not list_doctors():
        return None
    did = ask_int("Doctor ID: ")
    d = get_one("SELECT * FROM doctors WHERE doctor_id = %s", (did,))
    if d is None:
        print("No doctor found with that ID.")
    return d


def ask_mode():
    print("Payment mode: 1. Cash  2. Card  3. UPI")
    c = ask("Choice: ")
    if c == "2":
        return "Card"
    if c == "3":
        return "UPI"
    return "Cash"


def add_charge(patient_id, charge_type, description, amount):
    # THE LINK BETWEEN MODULES: every service posts its fee to the patient's
    # account through this function. Checkout later bills all of them together.
    run("INSERT INTO charges (patient_id, charge_type, description, amount, charge_date) "
        "VALUES (%s, %s, %s, %s, %s)",
        (patient_id, charge_type, description, amount, str(date.today())))


# ==========================================================
#  MODULE 1 : PATIENT & PRESCRIPTION MANAGEMENT
# ==========================================================

def generate_patient_id():
    # P0001, P0002, P0003 ...
    row = get_one("SELECT COUNT(*) AS c FROM patients")
    return "P" + str(row["c"] + 1).zfill(4)


def register_patient():
    print("\n--- Register Patient ---")
    name = ask("Name: ")
    if name == "":
        print("Name is required.")
        return
    dob = ask_date("Date of birth")
    gender = ask("Gender (M/F/Other): ")
    phone = ask("Phone: ")
    address = ask("Address: ")
    pid = generate_patient_id()
    run("INSERT INTO patients (patient_id, name, dob, gender, phone, address, registered_on) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (pid, name, dob, gender, phone, address, str(date.today())))
    print("Patient registered. Patient ID:", pid)


def add_doctor():
    print("\n--- Add Doctor ---")
    name = ask("Doctor name: ")
    if name == "":
        print("Name is required.")
        return
    spec = ask("Specialization: ")
    phone = ask("Phone: ")
    fee = ask_float("Consultation fee: ")
    did = run("INSERT INTO doctors (name, specialization, phone, consultation_fee) "
              "VALUES (%s, %s, %s, %s)", (name, spec, phone, fee))
    print("Doctor added. Doctor ID:", did)


def list_doctors():
    rows = get_all("SELECT * FROM doctors ORDER BY doctor_id")
    if not rows:
        print("No doctors added yet.")
        return rows
    print("\nID | Name | Specialization | Phone | Fee")
    for d in rows:
        print(d["doctor_id"], "|", d["name"], "|", d["specialization"], "|",
              d["phone"], "|", rs(d["consultation_fee"]))
    return rows


def book_appointment():
    print("\n--- Book Appointment ---")
    p = ask_patient()
    if p is None:
        return
    doc = ask_doctor()
    if doc is None:
        return
    appt_date = ask_date("Appointment date")
    if appt_date < str(date.today()):
        print("That date is in the past.")
        return
    appt_time = ask_time("Time")
    # a doctor cannot have two appointments at the same date and time
    clash = get_one("SELECT appointment_id FROM appointments WHERE doctor_id = %s "
                    "AND appt_date = %s AND appt_time = %s AND status = 'Booked'",
                    (doc["doctor_id"], appt_date, appt_time))
    if clash:
        print("Doctor is already booked at that time. Choose another slot.")
        return
    aid = run("INSERT INTO appointments (patient_id, doctor_id, appt_date, appt_time) "
              "VALUES (%s, %s, %s, %s)", (p["patient_id"], doc["doctor_id"], appt_date, appt_time))
    print("Appointment booked. Appointment ID:", aid)


def record_visit():
    # Records a visit and posts the consultation fee (OPD) or ER fee (Emergency).
    print("\n--- Record Patient Visit ---")
    p = ask_patient()
    if p is None:
        return
    doc = ask_doctor()
    if doc is None:
        return
    print("Visit type: 1. OPD  2. Emergency")
    vtype = "Emergency" if ask("Choice: ") == "2" else "OPD"
    diagnosis = ask("Diagnosis / notes: ")
    pid = p["patient_id"]
    visit_id = run("INSERT INTO visits (patient_id, doctor_id, visit_date, visit_type, diagnosis) "
                   "VALUES (%s, %s, %s, %s, %s)",
                   (pid, doc["doctor_id"], str(date.today()), vtype, diagnosis))
    if vtype == "OPD":
        add_charge(pid, "Consultation", "Consultation - Dr. " + doc["name"], doc["consultation_fee"])
    else:
        er = get_one("SELECT * FROM tariff WHERE category = 'ER' LIMIT 1")
        if er:
            add_charge(pid, "ER", er["item_name"], er["fee"])
    # if the patient had a booked appointment with this doctor today, mark it done
    run("UPDATE appointments SET status = 'Completed' WHERE patient_id = %s AND doctor_id = %s "
        "AND appt_date = %s AND status = 'Booked'", (pid, doc["doctor_id"], str(date.today())))
    print("Visit recorded. Visit ID:", visit_id, "- fee added to the patient's account.")


def record_test():
    # Orders a diagnostic test and posts its fee to the patient.
    print("\n--- Diagnostic Test ---")
    p = ask_patient()
    if p is None:
        return
    tests = get_all("SELECT * FROM tariff WHERE category = 'Diagnosis' ORDER BY tariff_id")
    if not tests:
        print("No tests in the tariff list. Add some in Module 3.")
        return
    for t in tests:
        print(t["tariff_id"], "|", t["item_name"], "|", rs(t["fee"]))
    tid = ask_int("Test ID: ")
    t = get_one("SELECT * FROM tariff WHERE tariff_id = %s AND category = 'Diagnosis'", (tid,))
    if t is None:
        print("Invalid test ID.")
        return
    add_charge(p["patient_id"], "Diagnosis", t["item_name"], t["fee"])
    print(t["item_name"], "added to the patient's account:", rs(t["fee"]))


def generate_prescription_no():
    # RX0001, RX0002, RX0003 ...
    row = get_one("SELECT COUNT(*) AS c FROM prescriptions")
    return "RX" + str(row["c"] + 1).zfill(4)


def create_prescription():
    print("\n--- Create Prescription ---")
    p = ask_patient()
    if p is None:
        return
    pid = p["patient_id"]
    visits = get_all("SELECT v.visit_id, v.visit_date, v.visit_type, v.diagnosis, d.name AS doctor "
                     "FROM visits v JOIN doctors d ON v.doctor_id = d.doctor_id "
                     "WHERE v.patient_id = %s ORDER BY v.visit_id", (pid,))
    if not visits:
        print("This patient has no visits. Record a visit first.")
        return
    print("Visits of", p["name"])
    for v in visits:
        print(v["visit_id"], "|", v["visit_date"], "|", v["visit_type"], "| Dr.", v["doctor"], "|", v["diagnosis"])
    vid = ask_int("Visit ID for this prescription: ")
    visit = get_one("SELECT * FROM visits WHERE visit_id = %s AND patient_id = %s", (vid, pid))
    if visit is None:
        print("That visit does not belong to this patient.")
        return
    if not list_medicines():
        print("Add medicines to the pharmacy inventory first (Module 2).")
        return

    items = []   # (medicine_id, dosage, days, quantity)
    while True:
        text = ask("Medicine ID (press Enter to finish): ")
        if text == "":
            break
        if not text.isdigit():
            print("Enter a number.")
            continue
        med = get_one("SELECT * FROM medicines WHERE medicine_id = %s", (int(text),))
        if med is None:
            print("No such medicine.")
            continue
        already = False
        for it in items:
            if it[0] == med["medicine_id"]:
                already = True
        if already:
            print("This medicine is already in the prescription.")
            continue
        dosage = ask("Dosage (example 1-0-1): ")
        days = ask_int("Number of days: ")
        qty = ask_int("Total quantity: ")
        if qty == 0:
            print("Quantity must be at least 1.")
            continue
        items.append((med["medicine_id"], dosage, days, qty))

    if not items:
        print("No medicines added. Prescription not created.")
        return
    rx_no = generate_prescription_no()
    run("INSERT INTO prescriptions (prescription_no, visit_id, patient_id, doctor_id, issued_on) "
        "VALUES (%s, %s, %s, %s, %s)", (rx_no, vid, pid, visit["doctor_id"], str(date.today())))
    for it in items:
        run("INSERT INTO prescription_items (prescription_no, medicine_id, dosage, no_of_days, quantity) "
            "VALUES (%s, %s, %s, %s, %s)", (rx_no, it[0], it[1], it[2], it[3]))
    print("Prescription created. Prescription No:", rx_no)


def view_patient_history():
    print("\n--- Patient History ---")
    p = ask_patient()
    if p is None:
        return
    pid = p["patient_id"]
    print("\nPatient:", p["name"], "| ID:", pid, "| DOB:", p["dob"], "| Gender:", p["gender"],
          "| Phone:", p["phone"])

    print("\nAppointments:")
    appts = get_all("SELECT a.*, d.name AS doctor FROM appointments a JOIN doctors d "
                    "ON a.doctor_id = d.doctor_id WHERE a.patient_id = %s ORDER BY a.appt_date", (pid,))
    if not appts:
        print("   none")
    for a in appts:
        print("  ", a["appointment_id"], "|", a["appt_date"], a["appt_time"], "| Dr.", a["doctor"], "|", a["status"])

    print("\nVisits:")
    visits = get_all("SELECT v.*, d.name AS doctor FROM visits v JOIN doctors d "
                     "ON v.doctor_id = d.doctor_id WHERE v.patient_id = %s ORDER BY v.visit_id", (pid,))
    if not visits:
        print("   none")
    for v in visits:
        print("  ", v["visit_id"], "|", v["visit_date"], "|", v["visit_type"], "| Dr.", v["doctor"],
              "| Diagnosis:", v["diagnosis"])

    print("\nPrescriptions:")
    rxs = get_all("SELECT * FROM prescriptions WHERE patient_id = %s ORDER BY issued_on", (pid,))
    if not rxs:
        print("   none")
    for rx in rxs:
        print("  ", rx["prescription_no"], "|", rx["issued_on"], "| Dispensed:", rx["dispensed"])
        items = get_all("SELECT pi.*, m.name FROM prescription_items pi JOIN medicines m "
                        "ON pi.medicine_id = m.medicine_id WHERE pi.prescription_no = %s",
                        (rx["prescription_no"],))
        for it in items:
            print("        -", it["name"], "|", it["dosage"], "|", it["no_of_days"], "days | qty", it["quantity"])

    row = get_one("SELECT SUM(amount) AS t FROM charges WHERE patient_id = %s AND billed = 'No'", (pid,))
    print("\nCharges not yet billed:", rs(row["t"]))


def patient_menu():
    while True:
        print("\n===== MODULE 1 : PATIENT & PRESCRIPTION =====")
        print("1. Register patient")
        print("2. Add doctor")
        print("3. List doctors")
        print("4. Book appointment")
        print("5. Record patient visit")
        print("6. Order diagnostic test")
        print("7. Create prescription")
        print("8. View patient history")
        print("0. Back to main menu")
        ch = ask("Enter choice: ")
        if ch == "1":
            safe(register_patient)
        elif ch == "2":
            safe(add_doctor)
        elif ch == "3":
            safe(list_doctors)
        elif ch == "4":
            safe(book_appointment)
        elif ch == "5":
            safe(record_visit)
        elif ch == "6":
            safe(record_test)
        elif ch == "7":
            safe(create_prescription)
        elif ch == "8":
            safe(view_patient_history)
        elif ch == "0":
            break
        else:
            print("Invalid choice.")


# ==========================================================
#  MODULE 2 : EMERGENCY SCHEDULING & PHARMACY
# ==========================================================

def check_shift_conflict(doctor_id, duty_date, start, end):
    # Returns the clashing duty row if this doctor already has an overlapping
    # duty on that date, otherwise None. Two shifts overlap when each one
    # starts before the other ends.
    return get_one("SELECT * FROM emergency_duty WHERE doctor_id = %s AND duty_date = %s "
                   "AND start_hour < %s AND end_hour > %s", (doctor_id, duty_date, end, start))


def assign_emergency_duty():
    print("\n--- Assign Emergency Duty ---")
    doc = ask_doctor()
    if doc is None:
        return
    duty_date = ask_date_today("Duty date")
    start = ask_int("Start hour (0-23): ")
    end = ask_int("End hour (1-24): ")
    if start > 23 or end < 1 or end > 24 or start >= end:
        print("Invalid hours. Start must be 0-23, end 1-24, and start must be before end.")
        return
    clash = check_shift_conflict(doc["doctor_id"], duty_date, start, end)
    if clash:
        print("Conflict: Dr.", doc["name"], "is already on duty from", clash["start_hour"],
              "to", clash["end_hour"], "on that date.")
        return
    run("INSERT INTO emergency_duty (doctor_id, duty_date, start_hour, end_hour) VALUES (%s, %s, %s, %s)",
        (doc["doctor_id"], duty_date, start, end))
    print("Duty assigned to Dr.", doc["name"], ":", start, "to", end, "on", duty_date)


def find_uncovered_hours(duty_date):
    # Returns a list of hours (0-23) that have no doctor on duty.
    duties = get_all("SELECT start_hour, end_hour FROM emergency_duty WHERE duty_date = %s", (duty_date,))
    uncovered = []
    for h in range(24):
        covered = False
        for d in duties:
            if d["start_hour"] <= h and h < d["end_hour"]:
                covered = True
        if not covered:
            uncovered.append(h)
    return uncovered


def print_hour_range(a, b):
    print("   ", str(a).zfill(2) + ":00 to " + str(b).zfill(2) + ":00")


def show_uncovered_hours():
    print("\n--- Uncovered Emergency Hours ---")
    duty_date = ask_date_today("Date")
    uncovered = find_uncovered_hours(duty_date)
    if not uncovered:
        print("All 24 hours are covered on", duty_date)
        return
    print("No doctor on duty during:")
    start = uncovered[0]
    prev = start
    for h in uncovered[1:]:
        if h != prev + 1:          # a gap in the list = a new range starts
            print_hour_range(start, prev + 1)
            start = h
        prev = h
    print_hour_range(start, prev + 1)


def view_daily_schedule():
    print("\n--- Emergency Duty Schedule ---")
    duty_date = ask_date_today("Date")
    rows = get_all("SELECT e.*, d.name, d.specialization FROM emergency_duty e JOIN doctors d "
                   "ON e.doctor_id = d.doctor_id WHERE e.duty_date = %s ORDER BY e.start_hour", (duty_date,))
    if not rows:
        print("No duties assigned on", duty_date)
        return
    print("Schedule for", duty_date)
    for r in rows:
        print(" ", str(r["start_hour"]).zfill(2) + ":00 - " + str(r["end_hour"]).zfill(2) + ":00 |",
              "Dr.", r["name"], "(" + str(r["specialization"]) + ")")
    print("Uncovered hours:", len(find_uncovered_hours(duty_date)), "of 24")


def add_medicine():
    print("\n--- Add Medicine ---")
    name = ask("Medicine name: ")
    if name == "":
        print("Name is required.")
        return
    if get_one("SELECT medicine_id FROM medicines WHERE name = %s", (name,)):
        print("This medicine already exists. Use 'Update stock' to add more.")
        return
    price = ask_float("Unit price: ")
    stock = ask_int("Stock quantity: ")
    expiry = ask_date("Expiry date")
    reorder = ask_int("Reorder level (alert when stock falls to this): ")
    mid = run("INSERT INTO medicines (name, unit_price, stock_qty, expiry_date, reorder_level) "
              "VALUES (%s, %s, %s, %s, %s)", (name, price, stock, expiry, reorder))
    print("Medicine added. Medicine ID:", mid)


def list_medicines():
    rows = get_all("SELECT * FROM medicines ORDER BY medicine_id")
    if not rows:
        print("No medicines in inventory yet.")
        return rows
    print("\nID | Name | Price | Stock | Expiry")
    for m in rows:
        print(m["medicine_id"], "|", m["name"], "|", rs(m["unit_price"]), "|", m["stock_qty"], "|", m["expiry_date"])
    return rows


def update_stock():
    print("\n--- Update Stock ---")
    if not list_medicines():
        return
    mid = ask_int("Medicine ID: ")
    med = get_one("SELECT * FROM medicines WHERE medicine_id = %s", (mid,))
    if med is None:
        print("No such medicine.")
        return
    qty = ask_int("Quantity received: ")
    new_expiry = ask_date("New expiry date (leave blank to keep " + str(med["expiry_date"]) + ")", True)
    if new_expiry == "":
        new_expiry = med["expiry_date"]
    run("UPDATE medicines SET stock_qty = stock_qty + %s, expiry_date = %s WHERE medicine_id = %s",
        (qty, new_expiry, mid))
    print("Stock updated. New stock of", med["name"], "=", med["stock_qty"] + qty)


def check_expiry_and_stock():
    print("\n--- Expiry and Low Stock Alerts ---")
    today = date.today()
    limit = today + timedelta(days=30)
    expired = get_all("SELECT * FROM medicines WHERE expiry_date < %s", (today,))
    soon = get_all("SELECT * FROM medicines WHERE expiry_date >= %s AND expiry_date <= %s", (today, limit))
    low = get_all("SELECT * FROM medicines WHERE stock_qty <= reorder_level")
    print("EXPIRED:")
    if not expired:
        print("   none")
    for m in expired:
        print("  ", m["name"], "| expired on", m["expiry_date"], "| stock", m["stock_qty"])
    print("EXPIRING IN 30 DAYS:")
    if not soon:
        print("   none")
    for m in soon:
        print("  ", m["name"], "| expires on", m["expiry_date"], "| stock", m["stock_qty"])
    print("LOW STOCK:")
    if not low:
        print("   none")
    for m in low:
        print("  ", m["name"], "| stock", m["stock_qty"], "| reorder level", m["reorder_level"])


def fetch_prescription(patient_id, prescription_no):
    # Returns the prescription (with an 'items' list) or None if it is not
    # found for that patient.
    rx = get_one("SELECT * FROM prescriptions WHERE prescription_no = %s AND patient_id = %s",
                 (prescription_no, patient_id))
    if rx is None:
        return None
    rx["items"] = get_all("SELECT pi.*, m.name, m.unit_price, m.stock_qty, m.expiry_date "
                          "FROM prescription_items pi JOIN medicines m ON pi.medicine_id = m.medicine_id "
                          "WHERE pi.prescription_no = %s", (prescription_no,))
    return rx


def show_prescription():
    print("\n--- Retrieve Prescription ---")
    p = ask_patient()
    if p is None:
        return
    rx_no = ask("Prescription number: ").upper()
    rx = fetch_prescription(p["patient_id"], rx_no)
    if rx is None:
        print("No such prescription for this patient.")
        return
    print("\nPrescription", rx["prescription_no"], "| Date:", rx["issued_on"], "| Dispensed:", rx["dispensed"])
    print("Patient:", p["name"])
    for it in rx["items"]:
        print("  -", it["name"], "|", it["dosage"], "|", it["no_of_days"], "days | qty", it["quantity"],
              "| in stock:", it["stock_qty"])


def dispense_medicines():
    # Checks stock and expiry, reduces stock, makes the receipt and posts
    # the medicine total to the patient's account.
    print("\n--- Dispense Medicines ---")
    p = ask_patient()
    if p is None:
        return
    rx_no = ask("Prescription number: ").upper()
    rx = fetch_prescription(p["patient_id"], rx_no)
    if rx is None:
        print("No such prescription for this patient.")
        return
    if rx["dispensed"] == "Yes":
        print("This prescription has already been dispensed.")
        return

    today = date.today()
    problems = []
    total = 0
    for it in rx["items"]:
        if it["expiry_date"] < today:
            problems.append(it["name"] + " is expired")
        elif it["stock_qty"] < it["quantity"]:
            problems.append(it["name"] + ": need " + str(it["quantity"]) + ", only " + str(it["stock_qty"]) + " in stock")
        total += float(it["unit_price"]) * it["quantity"]
    if problems:
        print("Cannot dispense:")
        for pr in problems:
            print("  -", pr)
        print("Restock the medicines and try again. Nothing was changed.")
        return

    receipt_id = run("INSERT INTO pharmacy_receipts (prescription_no, patient_id, receipt_date, total) "
                     "VALUES (%s, %s, %s, %s)", (rx_no, p["patient_id"], str(today), total))
    for it in rx["items"]:
        run("INSERT INTO pharmacy_receipt_items (receipt_id, medicine_id, qty, price) VALUES (%s, %s, %s, %s)",
            (receipt_id, it["medicine_id"], it["quantity"], it["unit_price"]))
        run("UPDATE medicines SET stock_qty = stock_qty - %s WHERE medicine_id = %s",
            (it["quantity"], it["medicine_id"]))
    run("UPDATE prescriptions SET dispensed = 'Yes' WHERE prescription_no = %s", (rx_no,))
    add_charge(p["patient_id"], "Medicine", "Pharmacy receipt No. " + str(receipt_id), total)
    print_receipt(receipt_id)


def print_receipt(receipt_id):
    r = get_one("SELECT r.*, p.name FROM pharmacy_receipts r JOIN patients p "
                "ON r.patient_id = p.patient_id WHERE r.receipt_id = %s", (receipt_id,))
    if r is None:
        print("No such receipt.")
        return
    print("\n========== PHARMACY RECEIPT ==========")
    print("Receipt No :", r["receipt_id"], "  Date:", r["receipt_date"])
    print("Patient    :", r["name"], "(" + r["patient_id"] + ")")
    print("Prescription:", r["prescription_no"])
    print("--------------------------------------")
    items = get_all("SELECT i.*, m.name FROM pharmacy_receipt_items i JOIN medicines m "
                    "ON i.medicine_id = m.medicine_id WHERE i.receipt_id = %s", (receipt_id,))
    for i in items:
        print(i["name"], "|", i["qty"], "x", rs(i["price"]), "=", rs(i["qty"] * float(i["price"])))
    print("--------------------------------------")
    print("TOTAL:", rs(r["total"]))


def reprint_receipt():
    rid = ask_int("Receipt number: ")
    print_receipt(rid)


def pharmacy_menu():
    while True:
        print("\n===== MODULE 2 : EMERGENCY & PHARMACY =====")
        print("1. Assign emergency duty")
        print("2. View daily duty schedule")
        print("3. Find uncovered hours")
        print("4. Add medicine")
        print("5. List medicines")
        print("6. Update stock")
        print("7. Expiry and low stock alerts")
        print("8. Retrieve prescription")
        print("9. Dispense medicines (creates receipt)")
        print("10. Reprint pharmacy receipt")
        print("0. Back to main menu")
        ch = ask("Enter choice: ")
        if ch == "1":
            safe(assign_emergency_duty)
        elif ch == "2":
            safe(view_daily_schedule)
        elif ch == "3":
            safe(show_uncovered_hours)
        elif ch == "4":
            safe(add_medicine)
        elif ch == "5":
            safe(list_medicines)
        elif ch == "6":
            safe(update_stock)
        elif ch == "7":
            safe(check_expiry_and_stock)
        elif ch == "8":
            safe(show_prescription)
        elif ch == "9":
            safe(dispense_medicines)
        elif ch == "10":
            safe(reprint_receipt)
        elif ch == "0":
            break
        else:
            print("Invalid choice.")


# ==========================================================
#  MODULE 3 : BILLING & GOVERNMENT ASSISTANCE
# ==========================================================

def add_scheme():
    print("\n--- Add Government Scheme ---")
    name = ask("Scheme name: ")
    if name == "":
        print("Name is required.")
        return
    rule = ask("Eligibility rule (text, example: family income below 2.5 lakh): ")
    percent = ask_float("Concession percent (0-100): ")
    if percent > 100:
        print("Percent cannot be more than 100.")
        return
    max_amt = ask_float("Maximum concession amount (0 = no limit): ")
    sid = run("INSERT INTO govt_schemes (name, eligibility_rule, concession_percent, max_amount) "
              "VALUES (%s, %s, %s, %s)", (name, rule, percent, max_amt))
    print("Scheme added. Scheme ID:", sid)


def list_schemes():
    rows = get_all("SELECT * FROM govt_schemes ORDER BY scheme_id")
    if not rows:
        print("No schemes added yet.")
        return rows
    print("\nID | Name | Concession | Max amount | Eligibility")
    for s in rows:
        print(s["scheme_id"], "|", s["name"], "|", s["concession_percent"], "% |",
              rs(s["max_amount"]), "|", s["eligibility_rule"])
    return rows


def link_scheme():
    # Registers a patient under a scheme (after staff checked the eligibility
    # rule and the patient's scheme card).
    print("\n--- Link Scheme to Patient ---")
    p = ask_patient()
    if p is None:
        return
    if not list_schemes():
        return
    sid = ask_int("Scheme ID: ")
    if get_one("SELECT scheme_id FROM govt_schemes WHERE scheme_id = %s", (sid,)) is None:
        print("No such scheme.")
        return
    card = ask("Scheme card number: ")
    valid_till = ask_date("Card valid till")
    run("INSERT INTO patient_schemes (patient_id, scheme_id, card_no, valid_till) VALUES (%s, %s, %s, %s)",
        (p["patient_id"], sid, card, valid_till))
    print("Patient linked to the scheme.")


def check_eligibility(patient_id):
    # Returns the best valid scheme (highest concession) of the patient,
    # or None if the patient has no scheme or the card has expired.
    return get_one("SELECT s.*, ps.card_no FROM patient_schemes ps JOIN govt_schemes s "
                   "ON ps.scheme_id = s.scheme_id WHERE ps.patient_id = %s AND ps.valid_till >= %s "
                   "ORDER BY s.concession_percent DESC LIMIT 1", (patient_id, date.today()))


def show_eligibility():
    print("\n--- Scheme Eligibility ---")
    p = ask_patient()
    if p is None:
        return
    s = check_eligibility(p["patient_id"])
    if s is None:
        print(p["name"], "has no valid government scheme. No concession.")
    else:
        print(p["name"], "is covered under", s["name"], "(card", s["card_no"] + ")")
        print("Concession:", s["concession_percent"], "% up to", rs(s["max_amount"]), "(0 = no limit)")


def list_tariff():
    rows = get_all("SELECT * FROM tariff ORDER BY tariff_id")
    print("\nID | Item | Category | Fee")
    for t in rows:
        print(t["tariff_id"], "|", t["item_name"], "|", t["category"], "|", rs(t["fee"]))


def add_tariff():
    print("\n--- Add Tariff Item ---")
    name = ask("Item name (example: CT Scan): ")
    if name == "":
        print("Name is required.")
        return
    print("Category: 1. Diagnosis test  2. ER fee")
    cat = "ER" if ask("Choice: ") == "2" else "Diagnosis"
    fee = ask_float("Fee: ")
    run("INSERT INTO tariff (item_name, category, fee) VALUES (%s, %s, %s)", (name, cat, fee))
    print("Tariff item added.")


def show_charges():
    print("\n--- Patient Charges ---")
    p = ask_patient()
    if p is None:
        return
    rows = get_all("SELECT * FROM charges WHERE patient_id = %s ORDER BY charge_id", (p["patient_id"],))
    if not rows:
        print("No charges yet.")
        return
    unbilled = 0
    for c in rows:
        status = "Billed (bill " + str(c["bill_id"]) + ")" if c["billed"] == "Yes" else "Not billed"
        print(c["charge_date"], "|", c["charge_type"], "|", c["description"], "|", rs(c["amount"]), "|", status)
        if c["billed"] == "No":
            unbilled += float(c["amount"])
    print("Total not yet billed:", rs(unbilled))


def add_other_charge():
    print("\n--- Add Other Charge (room, procedure, etc.) ---")
    p = ask_patient()
    if p is None:
        return
    desc = ask("Description: ")
    amount = ask_float("Amount: ")
    add_charge(p["patient_id"], "Other", desc, amount)
    print("Charge added to the patient's account.")


def make_payment(bill_id, amount, mode):
    # Saves a payment and updates the bill's paid amount and status.
    run("INSERT INTO payments (bill_id, amount, pay_mode, paid_on) VALUES (%s, %s, %s, %s)",
        (bill_id, amount, mode, str(date.today())))
    b = get_one("SELECT * FROM bills WHERE bill_id = %s", (bill_id,))
    paid = round(float(b["paid"]) + amount, 2)
    if paid >= round(float(b["payable"]), 2):
        status = "Paid"
    else:
        status = "Partial"
    run("UPDATE bills SET paid = %s, status = %s WHERE bill_id = %s", (paid, status, bill_id))


def checkout():
    # Turns all unbilled charges of a patient into one final bill.
    print("\n--- Patient Checkout ---")
    p = ask_patient()
    if p is None:
        return
    pid = p["patient_id"]
    charges = get_all("SELECT * FROM charges WHERE patient_id = %s AND billed = 'No' ORDER BY charge_id", (pid,))
    if not charges:
        print("No pending charges for this patient.")
        return

    total = 0
    bill_type = "OPD"
    print("\nCharges for", p["name"], "(" + pid + ")")
    for c in charges:
        print("  ", c["charge_date"], "|", c["charge_type"], "|", c["description"], "|", rs(c["amount"]))
        total += float(c["amount"])
        if c["charge_type"] == "ER":
            bill_type = "Emergency"

    # government scheme concession
    concession = 0
    scheme = check_eligibility(pid)
    if scheme:
        concession = total * float(scheme["concession_percent"]) / 100
        if float(scheme["max_amount"]) > 0 and concession > float(scheme["max_amount"]):
            concession = float(scheme["max_amount"])
        print("Scheme applied:", scheme["name"], "-", scheme["concession_percent"], "%")
    total = round(total, 2)
    concession = round(concession, 2)
    payable = round(total - concession, 2)
    print("\nTotal      :", rs(total))
    print("Concession :", rs(concession))
    print("Payable    :", rs(payable))

    bill_id = run("INSERT INTO bills (patient_id, bill_type, bill_date, total, concession, payable, paid, status) "
                  "VALUES (%s, %s, %s, %s, %s, %s, 0, 'Pending')",
                  (pid, bill_type, str(date.today()), total, concession, payable))
    run("UPDATE charges SET billed = 'Yes', bill_id = %s WHERE patient_id = %s AND billed = 'No'", (bill_id, pid))

    if payable == 0:
        run("UPDATE bills SET status = 'Paid' WHERE bill_id = %s", (bill_id,))
    else:
        print("\n1. Pay full amount now")
        print("2. Pay part of the amount now")
        if bill_type == "Emergency":
            print("3. Pay later (emergency case)")
        choice = ask("Choice: ")
        if choice == "1":
            make_payment(bill_id, payable, ask_mode())
        elif choice == "2":
            amount = ask_float("Amount paying now: ")
            if amount <= 0 or amount > payable:
                print("Invalid amount. Bill saved as Pending.")
            else:
                make_payment(bill_id, amount, ask_mode())
        elif choice == "3" and bill_type == "Emergency":
            print("Bill saved as Pending. Pay later from the 'Record payment' option.")
        else:
            print("Bill saved as Pending.")
    print_bill(bill_id)


def print_bill(bill_id):
    b = get_one("SELECT b.*, p.name FROM bills b JOIN patients p ON b.patient_id = p.patient_id "
                "WHERE b.bill_id = %s", (bill_id,))
    if b is None:
        print("No such bill.")
        return
    print("\n============= HOSPITAL BILL =============")
    print("Bill No :", b["bill_id"], "   Date:", b["bill_date"])
    print("Patient :", b["name"], "(" + b["patient_id"] + ")")
    print("Type    :", b["bill_type"])
    print("-----------------------------------------")
    items = get_all("SELECT * FROM charges WHERE bill_id = %s ORDER BY charge_id", (bill_id,))
    for c in items:
        print(c["charge_type"], "-", c["description"], ":", rs(c["amount"]))
    print("-----------------------------------------")
    print("Total      :", rs(b["total"]))
    print("Concession :", rs(b["concession"]))
    print("Payable    :", rs(b["payable"]))
    print("Paid       :", rs(b["paid"]))
    print("Balance    :", rs(float(b["payable"]) - float(b["paid"])))
    print("Status     :", b["status"])
    pays = get_all("SELECT * FROM payments WHERE bill_id = %s ORDER BY payment_id", (bill_id,))
    for pay in pays:
        print("   Payment", pay["paid_on"], "|", pay["pay_mode"], "|", rs(pay["amount"]))


def view_bill():
    bid = ask_int("Bill number: ")
    print_bill(bid)


def record_payment():
    # Pays towards an existing bill (pay-later or part-paid bills).
    print("\n--- Record Payment ---")
    bid = ask_int("Bill number: ")
    b = get_one("SELECT * FROM bills WHERE bill_id = %s", (bid,))
    if b is None:
        print("No such bill.")
        return
    balance = round(float(b["payable"]) - float(b["paid"]), 2)
    if balance <= 0:
        print("This bill is already fully paid.")
        return
    print("Balance due:", rs(balance))
    amount = ask_float("Amount paying: ")
    if amount <= 0 or amount > balance:
        print("Amount must be more than 0 and not more than the balance.")
        return
    make_payment(bid, amount, ask_mode())
    print("Payment recorded.")
    print_bill(bid)


def outstanding_balances():
    print("\n--- Outstanding Balances ---")
    rows = get_all("SELECT b.bill_id, b.bill_date, b.bill_type, b.payable, b.paid, b.status, "
                   "p.patient_id, p.name FROM bills b JOIN patients p ON b.patient_id = p.patient_id "
                   "WHERE b.status <> 'Paid' ORDER BY b.bill_date")
    if not rows:
        print("No outstanding bills.")
        return
    grand = 0
    for r in rows:
        bal = float(r["payable"]) - float(r["paid"])
        grand += bal
        print("Bill", r["bill_id"], "|", r["bill_date"], "|", r["patient_id"], r["name"], "|", r["bill_type"],
              "| Payable", rs(r["payable"]), "| Paid", rs(r["paid"]), "| Balance", rs(bal), "|", r["status"])
    print("Total outstanding:", rs(grand))


def financial_report():
    print("\n--- Financial Report ---")
    print("Leave both dates blank for the full period.")
    d1 = ask_date("From date", True)
    d2 = ask_date("To date", True)
    if d1 == "":
        d1 = "1000-01-01"
    if d2 == "":
        d2 = "9999-12-31"

    b = get_one("SELECT COUNT(*) AS n, SUM(total) AS total, SUM(concession) AS conc, "
                "SUM(payable) AS payable, SUM(paid) AS paid FROM bills "
                "WHERE bill_date BETWEEN %s AND %s", (d1, d2))
    collected = get_one("SELECT SUM(amount) AS t FROM payments WHERE paid_on BETWEEN %s AND %s", (d1, d2))
    print("\nBills raised          :", b["n"])
    print("Total billed          :", rs(b["total"]))
    print("Concessions given     :", rs(b["conc"]))
    print("Net payable           :", rs(b["payable"]))
    print("Money collected       :", rs(collected["t"]))
    print("Pending on these bills:", rs(float(b["payable"] or 0) - float(b["paid"] or 0)))

    print("\nIncome by type of charge:")
    rows = get_all("SELECT charge_type, SUM(amount) AS t FROM charges WHERE billed = 'Yes' "
                   "AND charge_date BETWEEN %s AND %s GROUP BY charge_type", (d1, d2))
    if not rows:
        print("   none")
    for r in rows:
        print("  ", r["charge_type"], ":", rs(r["t"]))


def billing_menu():
    while True:
        print("\n===== MODULE 3 : BILLING & GOVT ASSISTANCE =====")
        print("1. Add government scheme")
        print("2. List schemes")
        print("3. Link scheme to patient")
        print("4. Check scheme eligibility")
        print("5. View tariff list")
        print("6. Add tariff item")
        print("7. View patient charges")
        print("8. Add other charge")
        print("9. CHECKOUT patient (final bill)")
        print("10. Record payment")
        print("11. View a bill")
        print("12. Outstanding balances")
        print("13. Financial report")
        print("0. Back to main menu")
        ch = ask("Enter choice: ")
        if ch == "1":
            safe(add_scheme)
        elif ch == "2":
            safe(list_schemes)
        elif ch == "3":
            safe(link_scheme)
        elif ch == "4":
            safe(show_eligibility)
        elif ch == "5":
            safe(list_tariff)
        elif ch == "6":
            safe(add_tariff)
        elif ch == "7":
            safe(show_charges)
        elif ch == "8":
            safe(add_other_charge)
        elif ch == "9":
            safe(checkout)
        elif ch == "10":
            safe(record_payment)
        elif ch == "11":
            safe(view_bill)
        elif ch == "12":
            safe(outstanding_balances)
        elif ch == "13":
            safe(financial_report)
        elif ch == "0":
            break
        else:
            print("Invalid choice.")


# ==========================================================
#  MAIN PROGRAM
# ==========================================================

def safe(func):
    # Runs a menu action. If MySQL gives an error, it is shown and the
    # program carries on instead of crashing.
    try:
        func()
    except mysql.connector.Error as e:
        print("Database error:", e)


def main():
    try:
        connect()
    except mysql.connector.Error as e:
        print("Could not connect to MySQL:", e)
        print("Check HOST, USER and PASSWORD at the top of this file.")
        return
    print("Connected. Database ready:", DB_NAME)

    while True:
        print("\n========== HOSPITAL MANAGEMENT SYSTEM ==========")
        print("1. Patient & Prescription Management")
        print("2. Emergency Scheduling & Pharmacy")
        print("3. Billing & Government Assistance")
        print("0. Exit")
        ch = ask("Enter choice: ")
        if ch == "1":
            patient_menu()
        elif ch == "2":
            pharmacy_menu()
        elif ch == "3":
            billing_menu()
        elif ch == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")
    con.close()


main()
