import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import requests
import mysql.connector
import json
import csv
import io
from datetime import datetime

API_KEY = "3882e041eae69748fb01a46f35928e66"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "010821",
    "database": "weather"
}


def get_connection():
    # Return a connection to the MySQL database.
    return mysql.connector.connect(**DB_CONFIG)


def get_forecast_by_city(city):
    # Fetch the 5‑day weather forecast for a city using HTTPS.
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    return response.json()


def filter_forecast_data(forecast_data, start_date, end_date):
    # Filter forecast entries so that only entries with dates within the provided date range are returned.
    filtered = []
    for entry in forecast_data.get("list", []):
        entry_date_str = entry.get("dt_txt").split()[0]
        try:
            entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
        except Exception:
            continue
        if start_date <= entry_date <= end_date:
            filtered.append(entry)
    return filtered


def validate_date_range(start_date_str, end_date_str):
    # Validate date strings (format: YYYY-MM-DD) and ensure the start date is not after the end date.
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Incorrect date format. Please use YYYY-MM-DD.")
    if start_date > end_date:
        raise ValueError("Start date must be before or equal to the end date.")
    return start_date, end_date


def fetch_icon(icon_code):
    # Fetch the weather icon image from OpenWeatherMap and return a PIL image.
    icon_url = f"https://openweathermap.org/img/w/{icon_code}.png"
    response = requests.get(icon_url)
    if response.status_code == 200:
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        return image
    return None


def create_table():
    # Ensure the weather_records table exists in the MySQL database.
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            location VARCHAR(255) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            query_date DATETIME NOT NULL,
            forecast_data TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()


def create_record_in_db(location, start_date_str, end_date_str, forecast_json):
    # Insert a new record in the database and return the new record ID.
    conn = get_connection()
    cursor = conn.cursor()
    query_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
        INSERT INTO weather_records (location, start_date, end_date, query_date, forecast_data)
        VALUES (%s, %s, %s, %s, %s)
    '''
    cursor.execute(sql, (location, start_date_str, end_date_str, query_date, forecast_json))
    conn.commit()
    record_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return record_id


def get_all_records():
    # Retrieve all weather records from the database.
    conn = get_connection()
    cursor = conn.cursor()
    sql = "SELECT id, location, start_date, end_date, query_date, forecast_data FROM weather_records"
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def update_record_in_db(record_id, location, start_date_str, end_date_str, forecast_json):
    # Update an existing record.
    conn = get_connection()
    cursor = conn.cursor()
    query_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = '''
        UPDATE weather_records
        SET location=%s, start_date=%s, end_date=%s, query_date=%s, forecast_data=%s
        WHERE id=%s
    '''
    cursor.execute(sql, (location, start_date_str, end_date_str, query_date, forecast_json, record_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_record_in_db(record_id):
    # Delete a record from the database.
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM weather_records WHERE id=%s"
    cursor.execute(sql, (record_id,))
    conn.commit()
    cursor.close()
    conn.close()


def export_data_csv():
    # Export all records from the database to a CSV file.
    records = get_all_records()
    if not records:
        messagebox.showinfo("Export", "No records to export.")
        return
    filename = "weather_records_export.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ID", "Location", "Start Date", "End Date", "Query Date", "Forecast Data"])
        for row in records:
            writer.writerow(row)
    messagebox.showinfo("Export", f"Data exported to {filename}")


class WeatherAppGUI:
    def __init__(self, master):
        self.master = master
        master.title("Advanced Weather App (MySQL + Image Display)")
        master.geometry("900x600")

        # --- Top Bar: Developer Name and Info Button ---
        top_bar = tk.Frame(master)
        top_bar.pack(fill=tk.X, pady=5)
        dev_label = tk.Label(top_bar, text="Developed by Yizhou Ma", font=("Helvetica", 10, "italic"))
        dev_label.pack(side=tk.LEFT, padx=10)
        info_button = tk.Button(top_bar, text="Info", command=self.show_info)
        info_button.pack(side=tk.RIGHT, padx=10)

        create_table()

        # Create Record Frame
        self.create_frame = tk.LabelFrame(master, text="Create Weather Record")
        self.create_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(self.create_frame, text="Location:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.location_entry = tk.Entry(self.create_frame, width=30)
        self.location_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(self.create_frame, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.start_date_entry = tk.Entry(self.create_frame, width=15)
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        tk.Label(self.create_frame, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.end_date_entry = tk.Entry(self.create_frame, width=15)
        self.end_date_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        self.create_button = tk.Button(self.create_frame, text="Create Record", command=self.create_record_gui)
        self.create_button.grid(row=3, column=0, columnspan=2, pady=5)

        # Records Display Frame
        self.records_frame = tk.LabelFrame(master, text="Weather Records")
        self.records_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.records_tree = ttk.Treeview(self.records_frame,
                                         columns=("ID", "Location", "Start", "End", "Query Date"),
                                         show="headings")
        self.records_tree.heading("ID", text="ID")
        self.records_tree.heading("Location", text="Location")
        self.records_tree.heading("Start", text="Start Date")
        self.records_tree.heading("End", text="End Date")
        self.records_tree.heading("Query Date", text="Query Date")
        self.records_tree.column("ID", width=30)
        self.records_tree.column("Location", width=150)
        self.records_tree.column("Start", width=100)
        self.records_tree.column("End", width=100)
        self.records_tree.column("Query Date", width=150)
        self.records_tree.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        self.records_tree.bind("<<TreeviewSelect>>", self.on_record_select)

        scrollbar = ttk.Scrollbar(self.records_frame, orient="vertical", command=self.records_tree.yview)
        self.records_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="left", fill="y")

        # Actions Frame
        self.action_frame = tk.Frame(master)
        self.action_frame.pack(fill="x", padx=10, pady=5)

        self.update_button = tk.Button(self.action_frame, text="Update Record", command=self.update_record_gui)
        self.update_button.pack(side="left", padx=5)
        self.delete_button = tk.Button(self.action_frame, text="Delete Record", command=self.delete_record_gui)
        self.delete_button.pack(side="left", padx=5)
        self.export_button = tk.Button(self.action_frame, text="Export CSV", command=export_data_csv)
        self.export_button.pack(side="left", padx=5)
        self.refresh_button = tk.Button(self.action_frame, text="Refresh Records", command=self.refresh_records)
        self.refresh_button.pack(side="left", padx=5)

        # Details Frame (includes text details and an image display)
        self.details_frame = tk.LabelFrame(master, text="Record Details")
        self.details_frame.pack(fill="x", padx=10, pady=5)

        self.details_text = tk.Text(self.details_frame, height=8)
        self.details_text.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.image_label = tk.Label(self.details_frame)
        self.image_label.pack(side="left", padx=5, pady=5)

        self.refresh_records()

    def show_info(self):
        """Display PM Accelerator info in a message box."""
        info_text = (
            "PM Accelerator (Product Manager Accelerator)\n\n"
            "PM Accelerator is a program designed to help aspiring product managers "
            "enhance their skills, network with experienced professionals, and accelerate "
            "their careers through real-world projects and mentorship.\n\n"
            "For more information, please visit our LinkedIn page:\n"
            "https://www.linkedin.com/company/pm-accelerator/"
        )
        messagebox.showinfo("PM Accelerator Info", info_text)

    def create_record_gui(self):
        location = self.location_entry.get().strip()
        start_date_str = self.start_date_entry.get().strip()
        end_date_str = self.end_date_entry.get().strip()

        if not location or not start_date_str or not end_date_str:
            messagebox.showerror("Input Error", "All fields are required.")
            return

        try:
            start_date, end_date = validate_date_range(start_date_str, end_date_str)
        except ValueError as ve:
            messagebox.showerror("Date Error", str(ve))
            return

        forecast_data = get_forecast_by_city(location)
        if forecast_data.get("cod") != "200":
            messagebox.showerror("API Error", f"Error fetching forecast: {forecast_data.get('message')}")
            return

        filtered_forecast = filter_forecast_data(forecast_data, start_date, end_date)
        forecast_json = json.dumps(filtered_forecast)
        record_id = create_record_in_db(location, start_date_str, end_date_str, forecast_json)
        messagebox.showinfo("Success", f"Record created with ID: {record_id}")

        # Display external links for extra information.
        links = (f"Google Maps: https://www.google.com/maps/search/{location.replace(' ', '+')}\n"
                 f"YouTube Travel Videos: https://www.youtube.com/results?search_query={location.replace(' ', '+')}+travel")
        messagebox.showinfo("External Links", links)
        self.refresh_records()

    def refresh_records(self):
        for row in self.records_tree.get_children():
            self.records_tree.delete(row)
        records = get_all_records()
        for rec in records:
            rec_id, location, start_date, end_date, query_date, _ = rec
            self.records_tree.insert("", "end", values=(rec_id, location, start_date, end_date, query_date))

    def on_record_select(self, event):
        selected = self.records_tree.selection()
        if not selected:
            return
        item = self.records_tree.item(selected[0])
        record_id = item["values"][0]
        records = get_all_records()
        for rec in records:
            if rec[0] == record_id:
                self.details_text.delete("1.0", tk.END)
                details = f"ID: {rec[0]}\nLocation: {rec[1]}\nDate Range: {rec[2]} to {rec[3]}\nQuery Date: {rec[4]}\n"
                try:
                    forecast_list = json.loads(rec[5]) if rec[5] else []
                    if forecast_list:
                        details += "Forecast Data (first entry):\n"
                        first_entry = forecast_list[0]
                        dt_txt = first_entry.get("dt_txt")
                        temp = first_entry.get("main", {}).get("temp")
                        description = first_entry.get("weather", [{}])[0].get("description")
                        details += f"{dt_txt}: {temp}°C, {description}\n"
                        icon_code = first_entry.get("weather", [{}])[0].get("icon")
                        icon_image = fetch_icon(icon_code)
                        if icon_image:
                            icon_image = icon_image.resize((100, 100))
                            photo = ImageTk.PhotoImage(icon_image)
                            self.image_label.config(image=photo)
                            self.image_label.image = photo
                        else:
                            self.image_label.config(image="")
                    else:
                        details += "No forecast data available."
                        self.image_label.config(image="")
                except Exception as e:
                    details += "Error parsing forecast data."
                    self.image_label.config(image="")
                self.details_text.insert(tk.END, details)
                break

    def update_record_gui(self):
        selected = self.records_tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a record to update.")
            return
        item = self.records_tree.item(selected[0])
        record_id = item["values"][0]

        records = get_all_records()
        rec = None
        for r in records:
            if r[0] == record_id:
                rec = r
                break
        if not rec:
            messagebox.showerror("Error", "Record not found.")
            return

        new_location = simpledialog.askstring("Update", "Enter new location:", initialvalue=rec[1])
        new_start = simpledialog.askstring("Update", "Enter new start date (YYYY-MM-DD):", initialvalue=str(rec[2]))
        new_end = simpledialog.askstring("Update", "Enter new end date (YYYY-MM-DD):", initialvalue=str(rec[3]))

        if not new_location or not new_start or not new_end:
            messagebox.showerror("Input Error", "All fields are required for update.")
            return

        try:
            start_date, end_date = validate_date_range(new_start, new_end)
        except ValueError as ve:
            messagebox.showerror("Date Error", str(ve))
            return

        forecast_data = get_forecast_by_city(new_location)
        if forecast_data.get("cod") != "200":
            messagebox.showerror("API Error", f"Error fetching forecast: {forecast_data.get('message')}")
            return

        filtered_forecast = filter_forecast_data(forecast_data, start_date, end_date)
        forecast_json = json.dumps(filtered_forecast)

        update_record_in_db(record_id, new_location, new_start, new_end, forecast_json)
        messagebox.showinfo("Success", "Record updated successfully.")
        self.refresh_records()

    def delete_record_gui(self):
        selected = self.records_tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a record to delete.")
            return
        item = self.records_tree.item(selected[0])
        record_id = item["values"][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete record {record_id}?"):
            delete_record_in_db(record_id)
            messagebox.showinfo("Deleted", "Record deleted successfully.")
            self.refresh_records()


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherAppGUI(root)
    root.mainloop()
