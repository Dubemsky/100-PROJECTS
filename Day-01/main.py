# pip install customtkinter requests
import customtkinter as ctk
import requests


CITY_POOL = [
    ("London", 51.51, -0.13),
    ("Paris", 48.85, 2.35),
    ("New York", 40.71, -74.01),
    ("Tokyo", 35.68, 139.69),
    ("Sydney", -33.87, 151.21),
    ("Dubai", 25.20, 55.27),
    ("Cairo", 30.04, 31.24),
    ("Moscow", 55.75, 37.62),
    ("Rio de Janeiro", -22.91, -43.17),
    ("Mumbai", 19.08, 72.88),
    ("Toronto", 43.65, -79.38),
    ("Berlin", 52.52, 13.40),
    ("Nairobi", -1.29, 36.82),
    ("Bangkok", 13.75, 100.50),
    ("Los Angeles", 34.05, -118.24),
    ("Singapore", 1.35, 103.82),
    ("Cape Town", -33.92, 18.42),
    ("Mexico City", 19.43, -99.13),
    ("Istanbul", 41.01, 28.98),
    ("Reykjavik", 64.15, -21.94),
]

WINDY_THRESHOLD_KMH = 20
HOT_THRESHOLD_C = 30
COLD_THRESHOLD_C = 5

# ---------- GUI setup ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Weather App")
app.geometry("1100x600")

# layout: left column for search, right column for filters
app.grid_columnconfigure(0, weight=3)
app.grid_columnconfigure(1, weight=1)

main_frame = ctk.CTkFrame(app, fg_color="transparent")
main_frame.grid(row=0, column=0, sticky="nsew")

sidebar_frame = ctk.CTkFrame(app, width=280, corner_radius=15)
sidebar_frame.grid(row=0, column=1, sticky="ns", padx=20, pady=20)

# main frame widgets
city_label = ctk.CTkLabel(main_frame, text="Enter city:", font=("Arial", 20))
city_label.pack(pady=(60, 10))

city_entry = ctk.CTkEntry(main_frame, placeholder_text="e.g. London", width=300, height=40, font=("Arial", 16))
city_entry.pack(pady=10)

# display box for weather results
display_frame = ctk.CTkFrame(main_frame, width=400, height=260, corner_radius=15)
display_frame.pack(pady=30)
display_frame.pack_propagate(False)

city_name_label = ctk.CTkLabel(display_frame, text="", font=("Arial", 22, "bold"))
city_name_label.pack(pady=(20, 5))

emoji_label = ctk.CTkLabel(display_frame, text="", font=("Arial", 40))
emoji_label.pack(pady=5)

temp_label = ctk.CTkLabel(display_frame, text="", font=("Arial", 36))
temp_label.pack(pady=5)

feels_like_label = ctk.CTkLabel(display_frame, text="", font=("Arial", 16))
feels_like_label.pack(pady=5)

high_low_label = ctk.CTkLabel(display_frame, text="", font=("Arial", 16))
high_low_label.pack(pady=5)

sun_label = ctk.CTkLabel(display_frame, text="", font=("Arial", 16))
sun_label.pack(pady=5)

search_button = ctk.CTkButton(main_frame, text="Get Weather", command=lambda: get_weather(), width=200, height=45, font=("Arial", 16))
search_button.pack(pady=10)

# sidebar widgets: filter buttons + results list
filter_title_label = ctk.CTkLabel(sidebar_frame, text="Find cities that are:", font=("Arial", 16, "bold"))
filter_title_label.pack(pady=(20, 10))

sunny_button = ctk.CTkButton(sidebar_frame, text="☀️ Sunny", command=lambda: filter_cities("sunny"), width=200)
sunny_button.pack(pady=5)

rainy_button = ctk.CTkButton(sidebar_frame, text="🌧️ Rainy", command=lambda: filter_cities("rainy"), width=200)
rainy_button.pack(pady=5)

windy_button = ctk.CTkButton(sidebar_frame, text="💨 Windy", command=lambda: filter_cities("windy"), width=200)
windy_button.pack(pady=5)

snowy_button = ctk.CTkButton(sidebar_frame, text="❄️ Snowy", command=lambda: filter_cities("snowy"), width=200)
snowy_button.pack(pady=5)

hot_button = ctk.CTkButton(sidebar_frame, text="🥵 Hot", command=lambda: filter_cities("hot"), width=200)
hot_button.pack(pady=5)

cold_button = ctk.CTkButton(sidebar_frame, text="🥶 Cold", command=lambda: filter_cities("cold"), width=200)
cold_button.pack(pady=5)

results_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")


# ---------- functions ----------

# map WMO weather codes to an emoji
def code_to_emoji(code):
    if code == 0:
        return "☀️"
    if code in (1, 2):
        return "🌤️"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "🌫️"
    if code in (51, 53, 55, 56, 57, 80, 81, 82):
        return "🌦️"
    if code in (61, 63, 65, 66, 67):
        return "🌧️"
    if code in (71, 73, 75, 77, 85, 86):
        return "❄️"
    if code in (95, 96, 99):
        return "⛈️"
    return "🌡️"


# check if a city's current weather matches a filter category
def matches_category(category, code, wind_speed, temp):
    if category == "sunny":
        return code in (0, 1)
    if category == "rainy":
        return code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99)
    if category == "windy":
        return wind_speed >= WINDY_THRESHOLD_KMH
    if category == "snowy":
        return code in (71, 73, 75, 77, 85, 86)
    if category == "hot":
        return temp >= HOT_THRESHOLD_C
    if category == "cold":
        return temp <= COLD_THRESHOLD_C
    return False


# show a list of matching cities in the sidebar
def render_results(cities):
    for widget in results_frame.winfo_children():
        widget.destroy()
    if not cities:
        ctk.CTkLabel(results_frame, text="No matches found", font=("Arial", 13)).pack(pady=5)
        return
    for name, temp, emoji in cities:
        row = ctk.CTkLabel(results_frame, text=f"{emoji}  {name} — {temp}°C", font=("Arial", 13), anchor="w")
        row.pack(fill="x", padx=10, pady=4)


# fetch weather for the whole city pool and show the first 5 matches
def filter_cities(category):
    results_frame.pack(pady=10, fill="x")
    for widget in results_frame.winfo_children():
        widget.destroy()
    ctk.CTkLabel(results_frame, text="Searching...", font=("Arial", 13)).pack(pady=5)
    sidebar_frame.update()

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": ",".join(str(c[1]) for c in CITY_POOL),
            "longitude": ",".join(str(c[2]) for c in CITY_POOL),
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    )
    results = response.json()

    matches = []
    for (name, _, _), city_data in zip(CITY_POOL, results):
        current = city_data["current"]
        code = current["weather_code"]
        wind_speed = current["wind_speed_10m"]
        temp = current["temperature_2m"]
        if matches_category(category, code, wind_speed, temp):
            matches.append((name, temp, code_to_emoji(code)))
        if len(matches) == 5:
            break

    render_results(matches)


# get weather for the searched city and fill in the display box
def get_weather():
    city = city_entry.get()
    if not city:
        city_name_label.configure(text="Please enter a city")
        emoji_label.configure(text="")
        temp_label.configure(text="")
        feels_like_label.configure(text="")
        high_low_label.configure(text="")
        sun_label.configure(text="")
        return

    # turn city name into coordinates
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
    )
    geo_results = geo_response.json().get("results")
    if not geo_results:
        city_name_label.configure(text=f"Couldn't find '{city}'")
        emoji_label.configure(text="")
        temp_label.configure(text="")
        feels_like_label.configure(text="")
        high_low_label.configure(text="")
        sun_label.configure(text="")
        return

    lat = geo_results[0]["latitude"]
    lon = geo_results[0]["longitude"]

    # get current weather for those coordinates
    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset",
            "timezone": "auto",
        },
    )
    data = weather_response.json()


    current_temp = data["current"]["temperature_2m"]
    feels_like = data["current"]["apparent_temperature"]
    weather_code = data["current"]["weather_code"]
    high = data["daily"]["temperature_2m_max"][0]
    low = data["daily"]["temperature_2m_min"][0]
    sunrise = data["daily"]["sunrise"][0].split("T")[1]
    sunset = data["daily"]["sunset"][0].split("T")[1]

    city_name_label.configure(text=city)
    emoji_label.configure(text=code_to_emoji(weather_code))
    temp_label.configure(text=f"{current_temp}°C")
    feels_like_label.configure(text=f"Feels like {feels_like}°C")
    high_low_label.configure(text=f"High {high}°C / Low {low}°C")
    sun_label.configure(text=f"🌅 {sunrise}   🌇 {sunset}")


app.mainloop()
