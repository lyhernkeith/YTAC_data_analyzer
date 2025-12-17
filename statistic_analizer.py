from flask import Flask, render_template_string
# import pandas as pd
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi


application = Flask(__name__)

# BASE_DIR = os.path.dirname(os.path.abspath(_file_))
# CSV_FILE = os.path.join(BASE_DIR, "ytac_example_data.csv")

# INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
# INFLUX_TOKEN = "d459wOKNp3ZcThcXvKH8SYYBKt7UjhDIaVOAEaY3cU90fh7dJF_I859ROzYGx0u5z9QyaUBep5oNl3zLtvNYgg=="
# INFLUX_ORG = "567d0b44ef2669fe"
INFLUX_BUCKET = "Aquaris_GPS"

client = InfluxDBClient(
    url=os.environ["INFLUX_URL"],
    token=os.environ["INFLUX_TOKEN"],
    org=os.environ["INFLUX_ORG"]
)



# client = InfluxDBClient(
#     url=INFLUX_URL,
#     token=INFLUX_TOKEN,
#     org=INFLUX_ORG,
#     timeout=30_000
# )

query_api = client.query_api()



INTERVAL = 10


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pollution Monitoring Dashboard</title>
    <meta http-equiv="refresh" content="{{ interval }}">


    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>






    <style>
        body {
            margin: 0;
            background: #f7f9fb;
            font-family: "Segoe UI", Arial, sans-serif;
            padding: 30px;
        }

        .container {
            width: 100%;
            
            padding: 24px;
            margin: 0 auto; 
        }


        h1 {
            text-align: center;
            color: #1ca9c9;
        }

        
        .dashboard-grid {
            max-width: 1100px;
            width: 100%;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
        }

        .dashboard-card {
            background: white;
            border-radius: 15px;
            padding: 1.8rem;
            border: 2px solid #ffdb58;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .card-icon {
            width: 45px;
            height: 45px;
            background: #ffdb58;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #1ca9c9;
            font-size: 1.3rem;
        }

        .card-title {
            font-size: 1.3rem;
            font-weight: bold;
            color: #1ca9c9;
        }

        .card-value {
            font-size: 2.6rem;
            color: #ffdb58;
            text-align: center;
        }

        .gauge-container {
            position: relative;
            width: 200px;
            height: 200px;
            margin: auto;
        }

        .gauge {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: conic-gradient(
                #ffdb58 0deg,
                #ffdb58 calc(var(--gauge-value) * 1deg),
                #eaeaea calc(var(--gauge-value) * 1deg),
                #eaeaea 360deg
            );
        }

        .gauge::before {
            content: "";
            position: absolute;
            width: 150px;
            height: 150px;
            background: white;
            border-radius: 50%;
            top: 25px;
            left: 25px;
        }

        .gauge-value {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-weight: bold;
            font-size: 1.4rem;
            color: #1ca9c9;
        }

        .footer {
            grid-column: 1 / -1;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>

<body>



    <h>Water Pollution Dashboard</h>

    <div id="map" style="height: 400px; margin-bottom: 20px;"></div>







    <div class="container">
    <div class="dashboard-grid">

        <div class="dashboard-card">
            <div class="card-header">
                <div class="card-icon">📊</div>
                <div class="card-title">Total Pollution</div>
            </div>
            <div class="card-value">{{ total }}%</div>
        </div>

        <div class="dashboard-card">
            <div class="card-header">
                <div class="card-icon">🌡</div>
                <div class="card-title">Temperature</div>
            </div>
            <div class="gauge-container">
                <div class="gauge" style="--gauge-value: {{ temp_deg }}"></div>
                <div class="gauge-value">{{ temp }} °C</div>
            </div>
        </div>

        <div class="dashboard-card">
            <div class="card-header">
                <div class="card-icon">🌊</div>
                <div class="card-title">Turbidity</div>
            </div>
            <div class="gauge-container">
                <div class="gauge" style="--gauge-value: {{ turb_deg }}"></div>
                <div class="gauge-value">{{ turb }}NTU</div>
            </div>
        </div>

        <div class="dashboard-card">
            <div class="card-header">
                <div class="card-icon">🧪</div>
                <div class="card-title">pH Value</div>
            </div>
            <div class="gauge-container">
                <div class="gauge" style="--gauge-value: {{ ph_deg }}"></div>
                <div class="gauge-value">{{ PH }}</div>
            </div>
        </div>

        <div class="dashboard-card">
            <div class="card-header">
                <div class="card-icon">📍</div>
                <div class="card-title">GPS Location</div>
            </div>
            <div class="card-value">
                {{ lat }}, {{ lon }}
            </div>
        </div>
    </div>
    <div class="footer">
        Last updated: {{ last_updated }} (Asia/Kuala Lumpur) · Auto refresh {{ interval }}s
    </div>
</div>

<script>
window.onload = function() {
    var lat = {{ lat }};
    var lon = {{ lon }};

    var map = L.map('map').setView([lat, lon], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var redIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [25, 41],   
        iconAnchor: [12, 41], 
        popupAnchor: [1, -34],
        shadowSize: [41, 41]  
    });

    var marker = L.marker([lat, lon], { icon: redIcon })
        .addTo(map)
        .bindPopup("Current Location");

}
</script>


</body>
</html>
"""

# def get_latest_data():
#     query = f'''
#     from(bucket: "{INFLUX_BUCKET}")
#       |> range(start: 0)
#       |> filter(fn: (r) => r._field == "Temperature")
#       |> max()
      
#     '''

#     tables = query_api.query(query)

#     data = {}

#     for table in tables:
#         for record in table.records:
#             data[record.get_field()] = record.get_value()

#     return data

def get_highest_temp_row():
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: 0)
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["Temperature"], desc: true)
      |> limit(n:1)
    '''

    tables = query_api.query(query)
    data = {}

    for table in tables:
        for record in table.records:
            # After pivot, each record contains all fields in one row
            data = record.values
            break  # only need the first record

    return data




@application.route("/")
def index():
    data = get_highest_temp_row()

    temp = float(data.get("Temperature", 0))
    turb = float(data.get("Turbidity", 0))
    PH = float(data.get("PH", 0))
    
    temp_deg = min(360, (temp / 32) * 360)
    turb_deg = min(360, (turb / 50) * 360)
    ph_deg = min(360, (PH / 14) * 360)

    last_updated = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")

    return render_template_string(
        HTML_TEMPLATE,
        total=data.get("Total%", 0),
        lat=float(data.get("Latitude", 0)),
        lon=float(data.get("Longitude", 0)),
        temp=temp,
        turb=turb,
        PH=PH,
        turb_deg=turb_deg,
        temp_deg=temp_deg,
        ph_deg=ph_deg,
        last_updated=last_updated,
        interval=INTERVAL
    )



# @application.route("/")
# def index():
#     df = pd.read_csv(CSV_FILE)
#     max_row = df.loc[df["Total%"].idxmax()]

#     temp = float(max_row["Temperature"])
#     turb = float(max_row["Turbidity"])
#     ph = float(max_row["PH"])

#     return render_template_string(
#         HTML_TEMPLATE,
#         total=round(max_row["Total%"], 1),
#         lat=max_row["Latitude"],
#         lon=max_row["Longitude"],
#         temp=temp,
#         turbidity=turb,
#         PH=ph,

#         temp_deg=min(360, (temp / 50) * 360),
#         turb_deg=min(360, (turb / 70) * 360),
#         ph_deg=min(360, (ph / 14) * 360),

#         last_updated=datetime.now(
#             ZoneInfo("Asia/Kuala_Lumpur")
#         ).strftime("%Y-%m-%d %H:%M:%S"),

#         interval=INTERVAL
#     )


if __name__ == "__main__":

    application.run(debug=True)



