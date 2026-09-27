import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_live_weather(latitude: float, longitude: float):

    if not API_KEY:
        raise Exception("OPENWEATHER_API_KEY is missing from .env")

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()
    rain = data.get("rain", {})

    return {
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "rainfall_mm": rain.get("1h", 0),
        "recorded_at": data["dt"],
    }


def get_weather_forecast(latitude: float, longitude: float):

    if not API_KEY:
        raise Exception("OPENWEATHER_API_KEY is missing from .env")

    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    return data