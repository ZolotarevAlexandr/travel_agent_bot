import os
import json
import requests
import logging

from travel_bot.db_models import travel

logger = logging.getLogger(__name__)


def get_location_id(location: str) -> str | None:
    url = "https://hotels-com-provider.p.rapidapi.com/v2/regions"
    querystring = {"query": location, "domain": "GB", "locale": "en_GB"}
    headers = {
        "X-RapidAPI-Key": "",
        "X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        logger.warning("Location API error")
        return None
    resp_json = response.json()

    try:
        return resp_json["data"][0]["gaiaId"]
    except KeyError:
        return None


def get_hotels(location_id: str, start_date: str, end_date: str) -> dict:
    if os.path.exists(f".cache/hotels/{location_id}_{start_date}_{end_date}.json"):
        with open(
            f".cache/hotels/{location_id}_{start_date}_{end_date}.json", "r"
        ) as f:
            return json.load(f)

    url = "https://hotels-com-provider.p.rapidapi.com/v2/hotels/search"
    querystring = {
        "region_id": location_id,
        "locale": "en_GB",
        "checkin_date": start_date,
        "sort_order": "REVIEW",
        "adults_number": "1",
        "domain": "GB",
        "checkout_date": end_date,
        "available_filter": "SHOW_AVAILABLE_ONLY",
    }
    headers = {
        "X-RapidAPI-Key": "",
        "X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        logger.warning("Hotels API error")
        return {"hotels": {}, "info": {"error": "API error", "error_code": 1}}

    resp_json = response.json()
    hotels = resp_json["properties"]
    hotels_response = {"hotels": {}, "info": {"error": None, "error_code": 0}}
    for idx, hotel in enumerate(hotels[:5]):
        hotels_response["hotels"][idx] = {
            "name": hotel["name"],
            "stars": hotel["star"],
            "user_rating": hotel["reviews"]["score"],
            "price": hotel["price"]["lead"]["formatted"],
            "distance": hotel["destinationInfo"]["distanceFromDestination"]["value"],
        }

    with open(f".cache/hotels/{location_id}_{start_date}_{end_date}.json", "w") as f:
        json.dump(hotels_response, f)
    return hotels_response


def get_hotels_for_travel(user_travel: "travel.Travel") -> dict:
    if not os.path.exists(".cache/hotels"):
        os.makedirs(".cache/hotels")

    response = {"hotels": {}, "info": {"error": None, "error_code": 0}}
    for location in user_travel.locations:
        location_id = get_location_id(location.name)
        if not location_id:
            return {
                "hotels": {},
                "info": {"error": "Location API error", "error_code": 1},
            }
        response["hotels"][location.name] = get_hotels(
            location_id, user_travel.start_date, user_travel.end_date
        )

    return response
