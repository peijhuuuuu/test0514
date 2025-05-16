import streamlit as st
import ee
import geemap.foliumap as geemap
from google.oauth2 import service_account

# 初始化 GEE 
service_account_info = st.secrets["GEE_SERVICE_ACCOUNT"]
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/earthengine"]
)
ee.Initialize(credentials)

st.set_page_config(layout="wide")
st.title("🌍 使用 GEE 進行土地覆蓋分類（KMeans）")

# 1. 選擇地點與資料 
point = ee.Geometry.Point([120.5583462887228, 24.081653403304525])
image = ee.ImageCollection("COPERNICUS/S2_HARMONIZED") \
    .filterBounds(point) \
    .filterDate("2021-01-01", "2022-01-01") \
    .sort("CLOUDY_PIXEL_PERCENTAGE") \
    .first() \
    .select('B.*')

# 2. 抽樣訓練
training = image.sample(
    region=image.geometry(),
    scale=10,
    numPixels=10000,
    seed=0,
    geometries=True
)

# 3. 建立分群器與進行分類 
n_clusters = 10
clusterer = ee.Clusterer.wekaKMeans(nClusters=n_clusters).train(training)
classified = image.cluster(clusterer)

# 4. 設定圖例與視覺化參數
legend_dict = {
    'one': '#ab0000',
    'two': '#1c5f2c',
    'three': '#d99282',
    'four': '#466b9f',
    'five': '#ab6c28',
    'six': '#e6b800',
    'seven': '#5e3c99',
    'eight': '#7b3294',
    'nine': '#a6cee3',
    'ten': '#b15928'
}
palette = list(legend_dict.values())
vis_params_classified = {'min': 0, 'max': 9, 'palette': palette}
vis_params_rgb = {'min': 100,'max': 3500,'bands': ['B4', 'B3', 'B2']}

# 5. 建立地圖與滑動分割視窗
Map = geemap.Map()
Map.centerObject(image.geometry(), 12)

left_layer = geemap.ee_tile_layer(image, vis_params_rgb, "Sentinel-2 (RGB)")
right_layer = geemap.ee_tile_layer(classified, vis_params_classified, "KMeans Clustering")

Map.split_map(left_layer, right_layer)
Map.add_legend(title="Land Cover Cluster", legend_dict=legend_dict)

# 6. 輸出到 Streamlit 畫面
Map.to_streamlit(height=600)
