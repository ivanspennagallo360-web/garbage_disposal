
import json
from datetime import datetime
from html import escape
from pathlib import Path

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium


ORS_ROUTE_URL = (
    "https://api.openrouteservice.org/v2/directions/driving-car"
)

CUSTOMERS_FILE = Path("customers.json")


PLACES = [
    {
        "name": "Vega restoran",
        "lat": 44.011855041271275,
        "lon": 20.916311519638494,
    },
    {
        "name": "Srce",
        "lat": 44.01324185166865,
        "lon": 20.91201666710037,
    },
    {
        "name": "Restoran Dvoriste",
        "lat": 44.01646983546425,
        "lon": 20.92433264375116,
    },
    {
        "name": "Veliki Park",
        "lat": 44.017630642190554,
        "lon": 20.903026851772744,
    },
    {
        "name": "BIG Fashion Plaza",
        "lat": 44.00925320425192,
        "lon": 20.893582001586157,
    },
    {
        "name": "Muzej 21. Oktobar",
        "lat": 44.02176176693374,
        "lon": 20.896715629870332,
    },
    {
        "name": "Hotel Kragujevac",
        "lat": 44.01001815503685,
        "lon": 20.91482786655385,
    },
]


st.set_page_config(
    page_title="Collection Route",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)


try:
    API_KEY = st.secrets.openrouteservice.api_key
except Exception:
    st.error(
        "Missing [openrouteservice] api_key in Streamlit secrets."
    )
    st.stop()


def initialize_state():
    if "customers" not in st.session_state:
        st.session_state.customers = load_customers()

    if "route_result" not in st.session_state:
        st.session_state.route_result = None

    if "form_message" not in st.session_state:
        st.session_state.form_message = None


def load_customers():
    if not CUSTOMERS_FILE.exists():
        return []

    try:
        with CUSTOMERS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def save_customers():
    temporary_file = CUSTOMERS_FILE.with_suffix(".tmp")

    with temporary_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            st.session_state.customers,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_file.replace(CUSTOMERS_FILE)


def decode_polyline(encoded):
    coordinates = []
    index = 0
    latitude = 0
    longitude = 0

    while index < len(encoded):
        values = []

        for _ in range(2):
            shift = 0
            value = 0

            while True:
                byte = ord(encoded[index]) - 63
                index += 1

                value |= (byte & 31) << shift
                shift += 5

                if byte < 32:
                    break

            decoded = (
                ~(value >> 1)
                if value & 1
                else value >> 1
            )

            values.append(decoded)

        latitude += values[0]
        longitude += values[1]

        coordinates.append(
            (
                latitude / 100000,
                longitude / 100000,
            )
        )

    return coordinates


def get_route(start, destination):
    response = requests.post(
        ORS_ROUTE_URL,
        headers={
            "Authorization": API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "coordinates": [
                [
                    start["lon"],
                    start["lat"],
                ],
                [
                    destination["lon"],
                    destination["lat"],
                ],
            ]
        },
        timeout=20,
    )

    response.raise_for_status()

    route_data = response.json()["routes"][0]
    geometry = route_data["geometry"]

    if isinstance(geometry, str):
        route_coordinates = decode_polyline(geometry)
    else:
        route_coordinates = [
            (lat, lon)
            for lon, lat in geometry["coordinates"]
        ]

    return {
        "coordinates": route_coordinates,
        "distance_km": (
            route_data["summary"]["distance"] / 1000
        ),
        "duration_minutes": (
            route_data["summary"]["duration"] / 60
        ),
        "start": start,
        "destination": destination,
    }


def customer_as_route_place(customer):
    return {
        "name": f"Customer: {customer['name']}",
        "lat": customer["lat"],
        "lon": customer["lon"],
        "customer_id": customer["id"],
    }


def get_all_route_places():
    preset_places = [
        {
            "name": place["name"],
            "lat": place["lat"],
            "lon": place["lon"],
            "place_type": "preset",
        }
        for place in PLACES
    ]

    customer_places = [
        {
            "name": (
                f"Customer: {customer['name']} "
                f"— {customer['address'] or 'No address'}"
            ),
            "lat": customer["lat"],
            "lon": customer["lon"],
            "place_type": "customer",
            "customer_id": customer["id"],
        }
        for customer in st.session_state.customers
    ]

    return preset_places + customer_places


def find_customer(customer_id):
    for customer in st.session_state.customers:
        if customer["id"] == customer_id:
            return customer

    return None


def customer_popup_html(customer):
    name = escape(customer.get("name", ""))
    address = escape(
        f"{customer.get('address', '')}, "
        f"{customer.get('city', '')}".strip(", ")
    )
    floor = escape(customer.get("floor", "") or "-")
    door = escape(customer.get("door", "") or "-")
    phone = escape(customer.get("phone", "") or "-")
    bags = escape(str(customer.get("bags", 0)))
    notes = escape(customer.get("notes", "") or "No instructions")
    status = escape(customer.get("status", "Pending"))

    return f"""
    <div style="font-size: 14px; min-width: 220px;">
        <h4 style="margin: 0 0 8px 0;">{name}</h4>
        <b>Address:</b> {address}<br>
        <b>Floor:</b> {floor}<br>
        <b>Door:</b> {door}<br>
        <b>Phone:</b> {phone}<br>
        <b>Bags:</b> {bags}<br>
        <b>Status:</b> {status}<br>
        <b>Instructions:</b><br>
        {notes}
    </div>
    """


def create_map(route_result, customers):
    if route_result:
        start = route_result["start"]
        destination = route_result["destination"]

        center_lat = (
            start["lat"] + destination["lat"]
        ) / 2

        center_lon = (
            start["lon"] + destination["lon"]
        ) / 2

        map_object = folium.Map(
            location=[
                center_lat,
                center_lon,
            ],
            zoom_start=13,
        )

        folium.Marker(
            [
                start["lat"],
                start["lon"],
            ],
            tooltip=f"Start: {start['name']}",
            popup=start["name"],
            icon=folium.Icon(
                color="green",
                icon="play",
                prefix="fa",
            ),
        ).add_to(map_object)

        folium.Marker(
            [
                destination["lat"],
                destination["lon"],
            ],
            tooltip=(
                f"Destination: "
                f"{destination['name']}"
            ),
            popup=destination["name"],
            icon=folium.Icon(
                color="red",
                icon="flag",
                prefix="fa",
            ),
        ).add_to(map_object)

        folium.PolyLine(
            route_result["coordinates"],
            color="blue",
            weight=5,
            tooltip="Driving route",
        ).add_to(map_object)

    else:
        map_object = folium.Map(
            location=[
                44.01667,
                20.91667,
            ],
            zoom_start=13,
        )

    for customer in customers:
        if customer["status"] == "Pending":
            marker_color = "orange"
        else:
            marker_color = "gray"

        popup = folium.Popup(
            customer_popup_html(customer),
            max_width=320,
        )

        tooltip = (
            f"{customer['name']} — "
            f"{customer['address'] or 'No address'}"
        )

        folium.Marker(
            [
                customer["lat"],
                customer["lon"],
            ],
            tooltip=tooltip,
            popup=popup,
            icon=folium.Icon(
                color=marker_color,
                icon="user",
                prefix="fa",
            ),
        ).add_to(map_object)

    return map_object


initialize_state()


st.title("🚛 Collection Route")

st.caption(
    "Customers are saved locally in customers.json "
    "for testing."
)


if st.session_state.form_message:
    st.success(
        st.session_state.form_message
    )
    st.session_state.form_message = None


left_column, right_column = st.columns(
    [2, 1],
    gap="large",
)


with right_column:
    st.subheader("Customer management")

    with st.expander(
        "➕ Add new customer",
        expanded=False,
    ):
        with st.form(
            "customer_form",
            clear_on_submit=True,
        ):
            name = st.text_input(
                "Customer name *"
            )

            phone = st.text_input(
                "Phone"
            )

            address = st.text_input(
                "Address / street"
            )

            city = st.text_input(
                "City",
                value="Kragujevac",
            )

            floor = st.text_input(
                "Floor"
            )

            door = st.text_input(
                "Door / apartment"
            )

            bags = st.number_input(
                "Expected bags",
                min_value=0,
                step=1,
            )

            notes = st.text_area(
                "Pickup instructions"
            )

            st.write("Coordinates")

            latitude = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=44.01667,
                format="%.8f",
            )

            longitude = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=20.91667,
                format="%.8f",
            )

            save_customer_button = (
                st.form_submit_button(
                    "Save customer",
                    type="primary",
                    use_container_width=True,
                )
            )

        if save_customer_button:
            if not name.strip():
                st.error(
                    "Customer name is required."
                )
            else:
                new_customer = {
                    "id": datetime.now().strftime(
                        "%Y%m%d%H%M%S%f"
                    ),
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "address": address.strip(),
                    "city": city.strip(),
                    "floor": floor.strip(),
                    "door": door.strip(),
                    "bags": int(bags),
                    "notes": notes.strip(),
                    "lat": float(latitude),
                    "lon": float(longitude),
                    "status": "Pending",
                    "completed_at": None,
                }

                st.session_state.customers.append(
                    new_customer
                )

                save_customers()

                st.session_state.form_message = (
                    f"Customer '{new_customer['name']}' "
                    "was added."
                )

                st.rerun()

    st.subheader("Customer list")

    if not st.session_state.customers:
        st.info(
            "No customers added yet."
        )
    else:
        status_filter = st.selectbox(
            "Filter customers",
            [
                "All",
                "Pending",
                "Completed",
            ],
            key="customer_filter",
        )

        for customer in st.session_state.customers:
            if (
                status_filter != "All"
                and customer["status"] != status_filter
            ):
                continue

            with st.container(border=True):
                st.write(
                    f"**{customer['name']}** — "
                    f"{customer['status']}"
                )

                st.caption(
                    f"{customer['address']}, "
                    f"{customer['city']}"
                )

                st.caption(
                    f"Floor: "
                    f"{customer['floor'] or '-'} · "
                    f"Door: "
                    f"{customer['door'] or '-'}"
                )

                st.caption(
                    f"Coordinates: "
                    f"{customer['lat']:.6f}, "
                    f"{customer['lon']:.6f}"
                )

                if customer["phone"]:
                    st.caption(
                        f"Phone: {customer['phone']}"
                    )

                if customer["notes"]:
                    st.caption(
                        f"Instructions: "
                        f"{customer['notes']}"
                    )

                if customer["status"] == "Pending":
                    button_label = (
                        "Mark as completed"
                    )
                else:
                    button_label = (
                        "Mark as pending"
                    )

                if st.button(
                    button_label,
                    key=f"toggle_{customer['id']}",
                    use_container_width=True,
                ):
                    if customer["status"] == "Pending":
                        customer["status"] = "Completed"
                        customer["completed_at"] = (
                            datetime.now().isoformat(
                                timespec="minutes"
                            )
                        )
                    else:
                        customer["status"] = "Pending"
                        customer["completed_at"] = None

                    save_customers()
                    st.rerun()


with left_column:
    st.subheader("Route map")

    route_places = get_all_route_places()
    route_place_names = [
        place["name"]
        for place in route_places
    ]

    start_name = st.selectbox(
        "Start location",
        route_place_names,
        index=0,
        key="route_start",
    )

    destination_name = st.selectbox(
        "Destination",
        route_place_names,
        index=min(
            4,
            len(route_place_names) - 1,
        ),
        key="route_destination",
    )

    if st.button(
        "Calculate route",
        type="primary",
        use_container_width=True,
    ):
        start = next(
            place
            for place in route_places
            if place["name"] == start_name
        )

        destination = next(
            place
            for place in route_places
            if place["name"] == destination_name
        )

        try:
            st.session_state.route_result = get_route(
                start,
                destination,
            )

        except Exception as error:
            st.error(
                f"Route failed: {error}"
            )
            st.session_state.route_result = None

    if st.session_state.route_result:
        result = st.session_state.route_result

        metric_col1, metric_col2 = (
            st.columns(2)
        )

        with metric_col1:
            st.metric(
                "Distance",
                f"{result['distance_km']:.2f} km",
            )

        with metric_col2:
            st.metric(
                "Estimated time",
                f"{result['duration_minutes']:.1f} min",
            )

    map_object = create_map(
        st.session_state.route_result,
        st.session_state.customers,
    )

    st_folium(
        map_object,
        height=600,
        use_container_width=True,
    )






