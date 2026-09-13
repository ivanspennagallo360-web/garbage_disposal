import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

ORS_ROUTE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

st.set_page_config(
    page_title="Route Planner",
    page_icon="🚗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------- PRESET LOCATIONS IN KRAGUJEVAC ----------

KRAGUJEVAC_PLACES = [
    {
        "label": "Vega restoran",
        "lat": 44.011855041271275,
        "lon": 20.916311519638494,
    },
    {
        "label": "Srce",
        "lat": 44.01324185166865,
        "lon": 20.91201666710037,
    },
    {
        "label": "Restoran Dvoriste",
        "lat": 44.01646983546425,
        "lon": 20.92433264375116,
    },
    {
        "label": "Veliki Park",
        "lat": 44.017630642190554,
        "lon": 20.903026851772744,
    },
    {
        "label": "BIG Fashion Plaza",
        "lat": 44.00925320425192,
        "lon": 20.893582001586157,
    },
    {
        "label": "Muzej 21. Oktobar",
        "lat": 44.02176176693374,
        "lon": 20.896715629870332,
    },
    {
        "label": "Hotel Kragujevac",
        "lat": 44.01001815503685,
        "lon": 20.91482786655385,
    },
]

# ---------- ROUTING HELPER ----------

def decode_polyline(s):
    out = []
    i = 0
    lat = lon = 0
    while i < len(s):
        vals = []
        for _ in range(2):
            shift = result = 0
            while True:
                b = ord(s[i]) - 63
                i += 1
                result |= (b & 31) << shift
                shift += 5
                if b < 32:
                    break
            vals.append(~(result >> 1) if result & 1 else result >> 1)
        lat += vals[0]
        lon += vals[1]
        out.append((lat / 1e5, lon / 1e5))
    return out

def route(a, b, key):
    r = requests.post(
        ORS_ROUTE_URL,
        headers={"Authorization": key, "Content-Type": "application/json"},
        json={"coordinates": [[a[1], a[0]], [b[1], b[0]]]},
        timeout=20
    )
    r.raise_for_status()
    data = r.json()
    item = data["routes"][0]
    geom = item["geometry"]
    if isinstance(geom, str):
        coords = decode_polyline(geom)
    else:
        coords = [(lat, lon) for lon, lat in geom["coordinates"]]
    km = item["summary"]["distance"] / 1000.0
    mins = item["summary"]["duration"] / 60.0
    return coords, km, mins

# ---------- API KEY ----------

try:
    key = st.secrets.openrouteservice.api_key
except Exception:
    st.error("Add [openrouteservice] api_key to Streamlit secrets.")
    st.stop()

st.title("🚗 Route Planner")
st.caption("Kragujevac – preset locations")

# ---------- SESSION STATE ----------

if "start" not in st.session_state:
    st.session_state.start = None
if "end" not in st.session_state:
    st.session_state.end = None
if "route_result" not in st.session_state:
    st.session_state.route_result = None

# ---------- PRESET LOCATIONS UI ----------

preset_labels = [p["label"] for p in KRAGUJEVAC_PLACES]

col_start, col_end = st.columns(2)

with col_start:
    start_label = st.selectbox(
        "Start",
        preset_labels,
        key="start_sel",
        index=0
    )

with col_end:
    end_label = st.selectbox(
        "Destination",
        preset_labels,
        key="end_sel",
        index=4
    )

if st.button("Calculate route", type="primary", use_container_width=True):
    start_chosen = KRAGUJEVAC_PLACES[preset_labels.index(start_label)]
    end_chosen = KRAGUJEVAC_PLACES[preset_labels.index(end_label)]

    st.session_state.start = start_chosen
    st.session_state.end = end_chosen

    try:
        coords, km, mins = route(
            (start_chosen["lat"], start_chosen["lon"]),
            (end_chosen["lat"], end_chosen["lon"]),
            key
        )
        st.session_state.route_result = {
            "coords": coords,
            "km": km,
            "mins": mins,
            "start": start_chosen,
            "end": end_chosen,
        }
    except Exception as e:
        st.error(f"Route failed: {e}")
        st.session_state.route_result = None

# ---------- DISPLAY ROUTE & MAP ----------

if st.session_state.route_result:
    res = st.session_state.route_result

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Distance", f"{res['km']:.2f} km")
    with c2:
        st.metric("Estimated time", f"{res['mins']:.1f} min")

    # Center map roughly on Kragujevac, or on start point
    center_lat = (res["start"]["lat"] + res["end"]["lat"]) / 2
    center_lon = (res["start"]["lon"] + res["end"]["lon"]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13
    )

    folium.Marker(
        [res["start"]["lat"], res["start"]["lon"]],
        tooltip="Start",
        popup=res["start"]["label"],
        icon=folium.Icon(color="green")
    ).add_to(m)

    folium.Marker(
        [res["end"]["lat"], res["end"]["lon"]],
        tooltip="Destination",
        popup=res["end"]["label"],
        icon=folium.Icon(color="red")
    ).add_to(m)

    folium.PolyLine(res["coords"], color="blue", weight=5).add_to(m)

    st_folium(m, height=520, use_container_width=True)
else:
    # Show a simple overview map of Kragujevac when no route is selected
    center_kg = 44.01667
    lon_kg = 20.91667

    m0 = folium.Map(location=[center_kg, lon_kg], zoom_start=12)
    folium.Marker(
        [center_kg, lon_kg],
        tooltip="Kragujevac center",
        popup="Kragujevac center",
        icon=folium.Icon(color="gray", icon="info-sign")
    ).add_to(m0)

    st_folium(m0, height=520, use_container_width=True)
















































# import streamlit as st
# import requests
# import folium
# from streamlit_folium import st_folium

# ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
# ORS_ROUTE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

# st.set_page_config(
#     page_title="Route Planner",
#     page_icon="🚗",
#     layout="centered",
#     initial_sidebar_state="collapsed"
# )

# # ---------- PRESET LOCATIONS IN KRAGUJEVAC ----------

# KRAGUJEVAC_PLACES = [
#     {
#         "label": "Vega restoran",
#         "lat": 44.011855041271275,
#         "lon": 20.916311519638494,
#     },
#     {
#         "label": "Srce",
#         "lat": 44.01324185166865,
#         "lon": 20.91201666710037,
#     },
#     {
#         "label": "Restoran Dvoriste",
#         "lat": 44.01646983546425,
#         "lon": 20.92433264375116,
#     },
#     {
#         "label": "Veliki Park",
#         "lat": 44.017630642190554,
#         "lon": 20.903026851772744,
#     },
#     {
#         "label": "BIG Fashion Plaza",
#         "lat": 44.00925320425192,
#         "lon": 20.893582001586157,
#     },
#     {
#         "label": "Muzej 21. Oktobar",
#         "lat": 44.02176176693374,
#         "lon": 20.896715629870332,
#     },
#     {
#         "label": "Hotel Kragujevac",
#         "lat": 44.01001815503685,
#         "lon": 20.91482786655385,
#     },
# ]

# # ---------- GEOCODING & ROUTING HELPERS ----------

# @st.cache_data(ttl=300)
# def geocode(query, api_key):
#     r = requests.get(
#         ORS_GEOCODE_URL,
#         params={"text": query, "size": 5},
#         headers={"Authorization": api_key},
#         timeout=15
#     )
#     r.raise_for_status()
#     results = []
#     for f in r.json().get("features", []):
#         lon, lat = f["geometry"]["coordinates"]
#         props = f.get("properties", {})
#         label = props.get("label", props.get("name", query))
#         results.append({"label": label, "lat": lat, "lon": lon})
#     return results

# def decode_polyline(s):
#     out = []
#     i = 0
#     lat = lon = 0
#     while i < len(s):
#         vals = []
#         for _ in range(2):
#             shift = result = 0
#             while True:
#                 b = ord(s[i]) - 63
#                 i += 1
#                 result |= (b & 31) << shift
#                 shift += 5
#                 if b < 32:
#                     break
#             vals.append(~(result >> 1) if result & 1 else result >> 1)
#         lat += vals[0]
#         lon += vals[1]
#         out.append((lat / 1e5, lon / 1e5))
#     return out

# def route(a, b, key):
#     r = requests.post(
#         ORS_ROUTE_URL,
#         headers={"Authorization": key, "Content-Type": "application/json"},
#         json={"coordinates": [[a[1], a[0]], [b[1], b[0]]]},
#         timeout=20
#     )
#     r.raise_for_status()
#     data = r.json()
#     item = data["routes"][0]
#     geom = item["geometry"]
#     if isinstance(geom, str):
#         coords = decode_polyline(geom)
#     else:
#         coords = [(lat, lon) for lon, lat in geom["coordinates"]]
#     km = item["summary"]["distance"] / 1000.0
#     mins = item["summary"]["duration"] / 60.0
#     return coords, km, mins

# # ---------- API KEY ----------

# try:
#     key = st.secrets.openrouteservice.api_key
# except Exception:
#     st.error("Add [openrouteservice] api_key to Streamlit secrets.")
#     st.stop()

# st.title("🚗 Route Planner")
# st.caption("Mobile-friendly route planner for Kragujevac")

# # ---------- SESSION STATE ----------

# if "start" not in st.session_state:
#     st.session_state.start = None
# if "end" not in st.session_state:
#     st.session_state.end = None
# if "route_result" not in st.session_state:
#     st.session_state.route_result = None

# # ---------- PRESET LOCATIONS UI ----------

# st.subheader("1. Choose from preset locations")

# preset_labels = [p["label"] for p in KRAGUJEVAC_PLACES]

# st.markdown("**Start**")
# preset_start_label = st.selectbox(
#     "Preset start location",
#     preset_labels,
#     key="preset_start_sel",
#     index=0
# )
# if st.button("Use this as start", key="use_preset_start", type="secondary"):
#     chosen = KRAGUJEVAC_PLACES[preset_labels.index(preset_start_label)]
#     st.session_state.start = chosen
#     st.session_state.route_result = None

# st.markdown("**Destination**")
# preset_end_label = st.selectbox(
#     "Preset destination location",
#     preset_labels,
#     key="preset_end_sel",
#     index=4
# )
# if st.button("Use this as destination", key="use_preset_end", type="secondary"):
#     chosen = KRAGUJEVAC_PLACES[preset_labels.index(preset_end_label)]
#     st.session_state.end = chosen
#     st.session_state.route_result = None

# st.divider()

# # ---------- GEOCODED SEARCH UI ----------

# st.subheader("2. Or search any address")

# start_query = st.text_input(
#     "Search start address",
#     key="start_q",
#     placeholder="Kralja Petra I, Kragujevac, Serbia"
# )

# if start_query:
#     try:
#         start_choices = geocode(start_query, key)
#         if start_choices:
#             start_labels = [x["label"] for x in start_choices]
#             start_selected = st.selectbox("Choose start", start_labels, key="start_sel")
#             start_chosen = start_choices[start_labels.index(start_selected)]
#             if st.button("Set as start", key="set_start", type="secondary"):
#                 st.session_state.start = start_chosen
#                 st.session_state.route_result = None
#         else:
#             st.warning("No results. Try adding city and country.")
#     except requests.HTTPError as e:
#         st.error(f"Search failed: {e}")

# end_query = st.text_input(
#     "Search destination address",
#     key="end_q",
#     placeholder="Šumarice, Kragujevac, Serbia"
# )

# if end_query:
#     try:
#         end_choices = geocode(end_query, key)
#         if end_choices:
#             end_labels = [x["label"] for x in end_choices]
#             end_selected = st.selectbox("Choose destination", end_labels, key="end_sel")
#             end_chosen = end_choices[end_labels.index(end_selected)]
#             if st.button("Set as destination", key="set_end", type="secondary"):
#                 st.session_state.end = end_chosen
#                 st.session_state.route_result = None
#         else:
#             st.warning("No results. Try adding city and country.")
#     except requests.HTTPError as e:
#         st.error(f"Search failed: {e}")

# st.divider()

# # ---------- CURRENT SELECTION ----------

# st.subheader("3. Current selection")

# c1, c2 = st.columns(2)
# with c1:
#     start_label = st.session_state.start["label"] if st.session_state.start else "not selected"
#     st.write(f"**Start:** {start_label}")
# with c2:
#     end_label = st.session_state.end["label"] if st.session_state.end else "not selected"
#     st.write(f"**Destination:** {end_label}")

# if st.button("Clear selections", key="clear_sel", type="secondary"):
#     st.session_state.start = st.session_state.end = None
#     st.session_state.route_result = None
#     st.rerun()

# st.divider()

# # ---------- CALCULATE ROUTE ----------

# st.subheader("4. Route")

# if st.button("Calculate route", key="calc_route", type="primary", use_container_width=True):
#     if not st.session_state.start or not st.session_state.end:
#         st.warning("Select both locations first.")
#     else:
#         try:
#             coords, km, mins = route(
#                 (st.session_state.start["lat"], st.session_state.start["lon"]),
#                 (st.session_state.end["lat"], st.session_state.end["lon"]),
#                 key
#             )
#             st.session_state.route_result = {
#                 "coords": coords,
#                 "km": km,
#                 "mins": mins,
#                 "start": st.session_state.start,
#                 "end": st.session_state.end,
#             }
#         except Exception as e:
#             st.error(f"Route failed: {e}")
#             st.session_state.route_result = None

# # ---------- DISPLAY ROUTE ----------

# if st.session_state.route_result:
#     res = st.session_state.route_result

#     c1, c2 = st.columns(2)
#     with c1:
#         st.metric("Distance", f"{res['km']:.2f} km")
#     with c2:
#         st.metric("Estimated time", f"{res['mins']:.1f} min")

#     m = folium.Map(
#         location=[res["start"]["lat"], res["start"]["lon"]],
#         zoom_start=12
#     )
#     folium.Marker(
#         [res["start"]["lat"], res["start"]["lon"]],
#         tooltip="Start",
#         icon=folium.Icon(color="green")
#     ).add_to(m)

#     folium.Marker(
#         [res["end"]["lat"], res["end"]["lon"]],
#         tooltip="Destination",
#         icon=folium.Icon(color="red")
#     ).add_to(m)

#     folium.PolyLine(res["coords"], color="blue", weight=5).add_to(m)

#     st_folium(m, height=500, use_container_width=True)