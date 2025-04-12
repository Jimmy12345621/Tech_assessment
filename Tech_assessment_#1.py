import requests
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import io


API_KEY = "3882e041eae69748fb01a46f35928e66"


def get_weather_by_city(city):
    #Fetch current weather data for a city name using HTTPS.
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    return response.json()


def get_forecast_by_city(city):
    #Fetch the 5-day weather forecast for a city name using HTTPS.
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    return response.json()


def fetch_icon(icon_code):
    #Fetch the weather icon image from OpenWeatherMap.
    icon_url = f"https://openweathermap.org/img/w/{icon_code}.png"
    response = requests.get(icon_url)
    if response.status_code == 200:
        image_data = response.content
        return Image.open(io.BytesIO(image_data))
    return None


class WeatherApp:
    def __init__(self, master):
        self.master = master
        master.title("Weather App")

        # --- Input Section ---
        self.input_frame = tk.Frame(master)
        self.input_frame.pack(pady=10)

        self.city_label = tk.Label(self.input_frame, text="Enter City:")
        self.city_label.pack(side=tk.LEFT, padx=5)

        self.city_entry = tk.Entry(self.input_frame, width=30)
        self.city_entry.pack(side=tk.LEFT, padx=5)

        self.get_weather_btn = tk.Button(self.input_frame, text="Get Weather", command=self.get_weather)
        self.get_weather_btn.pack(side=tk.LEFT, padx=5)

        # --- Current Weather Section ---
        self.weather_frame = tk.Frame(master)
        self.weather_frame.pack(pady=10)

        self.current_weather_label = tk.Label(self.weather_frame, text="", font=("Helvetica", 14))
        self.current_weather_label.pack()

        self.weather_icon_label = tk.Label(self.weather_frame)
        self.weather_icon_label.pack(pady=5)

        # --- Forecast Section ---
        self.forecast_frame = tk.Frame(master)
        self.forecast_frame.pack(pady=10)

        self.forecast_title = tk.Label(self.forecast_frame, text="5-Day Forecast (Midday):",
                                       font=("Helvetica", 12, "bold"))
        self.forecast_title.pack()

        self.forecast_container = tk.Frame(self.forecast_frame)
        self.forecast_container.pack(pady=5)

        # References to image objects to prevent garbage collection
        self.forecast_icon_images = {}

    def get_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showerror("Input Error", "Please enter a city name.")
            return

        weather_data = get_weather_by_city(city)
        forecast_data = get_forecast_by_city(city)

        if weather_data.get("cod") != 200:
            messagebox.showerror("Error", f"Weather error: {weather_data.get('message')}")
            return

        if forecast_data.get("cod") != "200":
            messagebox.showerror("Error", f"Forecast error: {forecast_data.get('message')}")
            return

        # Clear previous forecast images
        for widget in self.forecast_container.winfo_children():
            widget.destroy()
        self.forecast_icon_images.clear()

        self.display_current_weather(weather_data)
        self.display_forecast(forecast_data)

    def display_current_weather(self, data):
        city = data.get("name")
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        temperature = main.get("temp")
        humidity = main.get("humidity")
        description = weather.get("description")
        icon_code = weather.get("icon")

        weather_text = (f"Current Weather for {city}:\n"
                        f"Temperature: {temperature}°C\n"
                        f"Humidity: {humidity}%\n"
                        f"Description: {description.capitalize()}")
        self.current_weather_label.config(text=weather_text)

        # Display weather icon
        icon_image = fetch_icon(icon_code)
        if icon_image:
            icon_image = icon_image.resize((100, 100))
            photo = ImageTk.PhotoImage(icon_image)
            self.weather_icon_label.config(image=photo)
            self.weather_icon_label.image = photo  # Save reference

    def display_forecast(self, forecast_data):
        daily_forecasts = {}
        for entry in forecast_data.get("list", []):
            # Filter forecast for about midday (12:00:00)
            if "12:00:00" in entry.get("dt_txt", ""):
                date = entry["dt_txt"].split()[0]
                daily_forecasts[date] = entry

        # If no midday data found, display all entries
        if not daily_forecasts:
            daily_forecasts = {entry["dt_txt"]: entry for entry in forecast_data.get("list", [])}

        # Create forecast blocks
        for date, forecast in sorted(daily_forecasts.items()):
            frame = tk.Frame(self.forecast_container, bd=1, relief=tk.RIDGE, padx=5, pady=5)
            frame.pack(side=tk.LEFT, padx=5)

            temp = forecast["main"]["temp"]
            description = forecast["weather"][0]["description"]
            icon_code = forecast["weather"][0]["icon"]

            label_date = tk.Label(frame, text=date, font=("Helvetica", 10, "bold"))
            label_date.pack()

            label_temp = tk.Label(frame, text=f"{temp}°C")
            label_temp.pack()

            label_desc = tk.Label(frame, text=description.capitalize(), wraplength=100)
            label_desc.pack()

            # Display forecast icon
            icon_image = fetch_icon(icon_code)
            if icon_image:
                icon_image = icon_image.resize((50, 50))
                photo = ImageTk.PhotoImage(icon_image)
                label_icon = tk.Label(frame, image=photo)
                label_icon.image = photo  # Save reference
                label_icon.pack()
                self.forecast_icon_images[date] = photo  # Store to avoid garbage collection


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
