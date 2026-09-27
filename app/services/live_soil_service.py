import requests


def get_live_soil_moisture(latitude: float, longitude: float):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "soil_moisture_0_to_1cm",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    current = data.get("current", {})

    soil_moisture = current.get(
        "soil_moisture_0_to_1cm"
    )

    if soil_moisture is None:
        raise Exception(
            "Soil moisture data unavailable"
        )

    # Open-Meteo returns volumetric soil water content.
    # Convert it to a percentage for the dashboard.
    soil_moisture_percent = round(
        soil_moisture * 100,
        2,
    )

    return {
        "soil_moisture": soil_moisture_percent,
        "recorded_at": current.get("time"),
    }