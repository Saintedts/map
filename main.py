import streamlit as st
import psycopg2
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import pandas as pd
import ast


tiles_url1 = 'https://{s}.tile.jawg.io/jawg-terrain/{z}/{x}/{y}{r}.png?access-token=VBXOveEDL91WcpFy807vDA2BIojRHSnIofnZ6xWitQpKIc5r3irS7aOzZbHBmo51'
tiles_url2 = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'


def type_name_to_type_id(type_name):
    object_type_number = {
        "Больницы": 1,
        "Поликлиники": 7,
        "Объекты культуры": 2,
        "Образовательные учреждения": 4,
        "Станции скорой помощи": 5,
        "Спортивные объекты": 6
    }
    return object_type_number[f'{type_name}']


def create_connection():
    connection = psycopg2.connect(user="postgres",
                                  password="postgres",
                                  host="127.0.0.1",
                                  port="5432",
                                  database="map")
    return connection.cursor()


def get_coordinates(type_id):
    cursor = create_connection()

    cursor.execute(
        f"select coordinates from geolocation full outer join object on object.geo_id = geolocation.geo_id where type = {type_id} order by geolocation.geo_id")
    record = cursor.fetchall()

    coordinates = []
    for i in range(0, len(record)):
        buff = record[i][0].replace('(', '').replace(')', '')
        buff = [float(val) for val in buff.split(',')]
        coordinates.append(buff[::-1])
    return coordinates


def get_address(type_id):
    cursor = create_connection()

    cursor.execute(
        f"select address from geolocation full outer join object on object.geo_id = geolocation.geo_id where type = {type_id} order by geolocation.geo_id")
    record = cursor.fetchall()

    address = []
    for i in range(0, len(record)):
        element = record[i][0].replace("('", "").replace("',)", "")
        address.append(element)
    return address


def get_names(type_id):
    cursor = create_connection()

    cursor.execute(f"select name from object where type = {type_id}  order by geo_id")
    record = cursor.fetchall()

    names = []
    for i in range(0, len(record)):
        name = record[i][0].replace("('", "").replace("',)", "")
        names.append(name)
    return names


def get_radius(type_name):
    object_type_radius = {
        "Больницы": 55,
        "Поликлиники": 30,
        "Объекты культуры": 21,
        "Образовательные учреждения": 14,
        "Станции скорой помощи": 55,
        "Спортивные объекты": 46
    }
    return object_type_radius[f'{type_name}']


def get_recommendation(type_id):
    recommendation_polygons_csv = pd.read_csv('data/recommendation_polygons.csv', sep=';')

    recommendation_polygons = []
    for i in range(0, len(recommendation_polygons_csv)):
        polygon = ast.literal_eval(recommendation_polygons_csv[f'{type_id}_type_object_recommendation_polygons'][i])
        recommendation_polygons.append(polygon[0])

    return recommendation_polygons


object_type = st.sidebar.radio('Тип социального объекта: ',
                               ['Больницы', 'Поликлиники', 'Объекты культуры',
                                'Образовательные учреждения', 'Станции скорой помощи', 'Спортивные объекты'])
type_id = type_name_to_type_id(object_type)

st.text(f'{object_type} на территории города')

coordinates = get_coordinates(type_id)
address = get_address(type_id)
names = get_names(type_id)

Map = folium.Map(location=[55.755819, 37.617644], zoom_start=11, tiles=None)
folium.TileLayer(tiles=tiles_url1, attr='toner-bcg', name="Схема").add_to(Map)
folium.TileLayer(tiles=tiles_url2, attr='toner-bcg', name="Спутник").add_to(Map)

objects = folium.FeatureGroup(name='Oбъекты инфраструктуры', show=False)
Map.add_child(objects)

for i in range(0, len(coordinates)):
    folium.Marker(coordinates[i], popup=f'{address[i]}', tooltip=f'{names[i]}').add_to(objects)

Heat_map = folium.FeatureGroup(name='Тепловая карта', show=True, overlay=False)
Map.add_child(Heat_map)
schema = folium.TileLayer(tiles=tiles_url1, attr='toner-bcg', name="Схема").add_to(Heat_map)
HeatMap(coordinates, radius=get_radius(object_type)).add_to(Heat_map)

Recommendation = folium.FeatureGroup(name='Области, рекомендованные к строительству',show=False)
Map.add_child(Recommendation)
folium.Polygon(locations=get_recommendation(type_id), color='red').add_to(Recommendation)


folium.LayerControl().add_to(Map)
folium_static(Map, 1300, 700)

st.text("Founded and designed by Saintests___")


