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
INFLUX_BUCKET = "edmondliu"

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



INTERVAL = 60


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



    <h1>Water Pollution Dashboard</h1>

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
                <div class="gauge-value">{{ temp }} C</div>
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

    var map = L.map('map').setView([4.412461, 113.993664], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    var points = {{ points | tojson }};
    var maxPoint = {{ max_point | tojson }};

    var redIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41]
    });

    points.forEach(function(p) {

        var isMax = (
            p.lat === maxPoint.lat &&
            p.lon === maxPoint.lon
        );

        if (isMax) {
           
            L.marker([p.lat, p.lon], { icon: redIcon })
                .addTo(map)
                .bindPopup("Most Polluted<br>Score: " + p.score.toFixed(2) + "%");
        } else {
            
            L.circleMarker([p.lat, p.lon], {
                radius: 6,
                color: "#3388ff",
                fillColor: "#3388ff",
                fillOpacity: 0.8
            })
            .addTo(map)
            .bindPopup("Pollution: " + p.score.toFixed(2) + "%");
        }
    });

};
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



def get_all_points():
    query = f'''
    import "math"

    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -30d)
        |> filter(fn: (r) => r._measurement == "water_quality")
        |> pivot(
            rowKey: ["_time"],
            columnKey: ["_field"],
            valueColumn: "_value"
        )
        |> filter(fn: (r) =>
            r.Temperature >= 0.0 and r.Temperature <= 45.0 and
            r.Turbidity >= 0.0 and r.Turbidity <= 200.0 and
            r.PH >= 0.0 and r.PH <= 14.0 and
            r.Latitude > 1.0 and r.Longitude > 1.0
        )
        |> map(fn: (r) => ({{
            r with
            ph_pct: math.abs(x:r.PH - 7.0) / 7.0 * 100.0,
            temp_pct: math.abs(x:r.Temperature - 25.0) / 20.0 * 100.0,
            turb_pct: if r.Turbidity <= 0.0 then 0.0 else r.Turbidity / 200.0 * 100.0
        }}))
        |> map(fn: (r) => ({{
            r with
            pollution_score: (r.ph_pct + r.temp_pct + r.turb_pct) / 3.0
        }}))
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 9)
    '''

    tables = query_api.query(query)

    points = []
    for table in tables:
        for record in table.records:
            points.append({
                "lat": float(record.values.get("Latitude", 0)),
                "lon": float(record.values.get("Longitude", 0)),
                "score": float(record.values.get("pollution_score", 0)),
                "Temperature": float(record.values.get("Temperature", 0)),
                "Turbidity": float(record.values.get("Turbidity", 0)),
                "PH": float(record.values.get("PH", 0))
            })

    return points


@application.route("/")
def index():

    points = get_all_points()

    if not points:
        return "No data available"

    # find most polluted point
    max_point = max(points, key=lambda x: x["score"])

    temp = max(0, min(max_point["Temperature"], 45))
    turb = max(0, min(max_point["Turbidity"], 200))
    PH   = max(0, min(max_point["PH"], 14))

    lat = max_point["lat"]
    lon = max_point["lon"]

    temp_deg = min(360, (abs(temp) / 45) * 360)
    turb_deg = min(360, (abs(turb) / 200) * 360)
    ph_deg   = min(360, (abs(PH) / 14) * 360)

    last_updated = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S")

    return render_template_string(
        HTML_TEMPLATE,
        total=round(max_point["score"], 1),
        lat=lat,
        lon=lon,
        temp=temp,
        turb=turb,
        PH=PH,
        turb_deg=turb_deg,
        temp_deg=temp_deg,
        ph_deg=ph_deg,
        last_updated=last_updated,
        interval=INTERVAL,
        points=points,
        max_point=max_point
    )



if __name__ == "__main__":

    application.run(debug=True)



