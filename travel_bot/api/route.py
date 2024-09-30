import os

import requests
import polyline
import staticmap

from travel_bot.db_models import city


def get_borders(
    coords: list[tuple[float, float]]
) -> tuple[tuple[float, float], tuple[float, float]]:
    coords.sort(key=lambda coord: coord[0])

    min_x = min(coord[0] for coord in coords)
    max_x = max(coord[0] for coord in coords)

    coords.sort(key=lambda coord: coord[1])

    min_y = min(coord[1] for coord in coords)
    max_y = max(coord[1] for coord in coords)

    return (min_x, max_x), (min_y, max_y)


def get_route(
    start_lon: float, start_lat: float, end_lon: float, end_lat: float
) -> list[tuple[float, float]]:
    url = "http://router.project-osrm.org/route/v1/driving/"
    loc = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    response = requests.get(url + loc)

    if response.status_code != 200:
        return []

    json_data = response.json()
    route = polyline.decode(json_data["routes"][0]["geometry"])
    return route


def get_png(*travel_cities: city.City) -> str:
    coords = [
        (travel_city.longitude, travel_city.latitude) for travel_city in travel_cities
    ]
    route_points = [
        get_route(coords_1[0], coords_1[1], coords_2[0], coords_2[1])
        for coords_1, coords_2 in zip(coords, coords[1:])
    ]
    route_points = [
        list(map(lambda x: x[::-1], city_points)) for city_points in route_points
    ]

    static_map = staticmap.StaticMap(800, 600)
    for city_route in route_points:
        static_map.add_line(staticmap.Line(city_route, color="blue", width=5))
    img = static_map.render()
    img.save(
        f".cache/maps/map_{'-'.join(str(travel_city.id) for travel_city in travel_cities)}.png"
    )
    return f".cache/maps/map_{'-'.join(str(travel_city.id) for travel_city in travel_cities)}.png"


def get_map_png(*travel_cities: city.City) -> bytes:
    if not os.path.exists(f".cache/maps"):
        os.makedirs(f".cache/maps")
    if os.path.exists(
        f".cache/maps/map_{'-'.join(str(travel_city.id) for travel_city in travel_cities)}.png"
    ):
        with open(
            f".cache/maps/map_{'-'.join(str(travel_city.id) for travel_city in travel_cities)}.png",
            "rb",
        ) as photo:
            img = photo.read()
        return img

    map_path = get_png(*travel_cities)
    with open(map_path, "rb") as photo:
        img = photo.read()
    return img
