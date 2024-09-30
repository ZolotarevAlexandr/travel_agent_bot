import datetime
import requests
import os
import json
import logging

from travel_bot.db_models import travel

logger = logging.getLogger(__name__)


def get_weather_in_city(
    lat: float, lon: float, start_date: datetime.date, end_date: datetime.date
) -> dict:
    start_date = datetime.date.strftime(start_date, "%Y-%m-%d")
    end_date = datetime.date.strftime(end_date, "%Y-%m-%d")
    if os.path.exists(
        f".cache/weather/weather_{lat}_{lon}_{start_date}_{end_date}.json"
    ):
        with open(
            f".cache/weather/weather_{lat}_{lon}_{start_date}_{end_date}.json", "r"
        ) as f:
            return json.load(f)

    base_url = r"https://api.open-meteo.com/v1/forecast"
    response = requests.get(
        base_url,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
            ],
        },
    )
    response = response.json()
    if "error" in response:
        return {"weather": {}, "info": {"error": response["reason"], "error_code": 1}}

    weather = {"weather": {}, "info": {"error": None, "error_code": 0}}
    days, temp_max, temp_min, precip = (
        response["daily"]["time"],
        response["daily"]["temperature_2m_max"],
        response["daily"]["temperature_2m_min"],
        response["daily"]["precipitation_probability_max"],
    )
    for day, tmax, tmin, precip in zip(days, temp_max, temp_min, precip):
        weather["weather"][day] = {"max_temp": tmax, "min_temp": tmin, "precip": precip}

    if not os.path.exists(".cache/weather"):
        os.makedirs(".cache/weather")
    with open(
        f".cache/weather/weather_{lat}_{lon}_{start_date}_{end_date}.json", "w"
    ) as f:
        json.dump(weather, f)

    return weather


def get_weather(user_travel: "travel.Travel") -> dict:
    if user_travel.start_date > datetime.date.today() + datetime.timedelta(days=14):
        return {
            "weather": {},
            "info": {"error": "Weather data is not available yet", "error_code": 1},
        }
    end_date = user_travel.end_date
    if end_date > datetime.date.today() + datetime.timedelta(days=14):
        end_date = datetime.date.today() + datetime.timedelta(days=14)

    response = {"weather": {}, "info": {"error": None, "error_code": 0}}
    for loc in user_travel.locations:
        weather = get_weather_in_city(
            loc.latitude, loc.longitude, user_travel.start_date, end_date
        )
        if weather["info"]["error_code"] != 0:
            logger.warning(f"Weather API error: {weather['info']['error_code']}")
            return {"weather": {}, "info": {"error": "API error", "error_code": 2}}
        response["weather"][loc.name] = weather["weather"]

    return response


def get_short_weather(user_travel: "travel.Travel") -> dict:
    weather_data = get_weather(user_travel)
    if weather_data["info"]["error_code"] != 0:
        return weather_data

    response = {"weather": {}, "info": {"error": None, "error_code": 0}}
    for loc in user_travel.locations:
        avg_day_temp = sum(
            weather_data["weather"][loc.name][day]["max_temp"]
            for day in weather_data["weather"][loc.name]
        ) / len(weather_data["weather"][loc.name])
        avg_night_temp = sum(
            weather_data["weather"][loc.name][day]["min_temp"]
            for day in weather_data["weather"][loc.name]
        ) / len(weather_data["weather"][loc.name])
        rainy_days = [
            day
            for day in weather_data["weather"][loc.name]
            if weather_data["weather"][loc.name][day]["precip"]
            and weather_data["weather"][loc.name][day]["precip"] > 50
        ]
        response["weather"][loc.name] = {
            "avg_day_temp": avg_day_temp,
            "avg_night_temp": avg_night_temp,
            "rainy_days": rainy_days,
        }
    return response
