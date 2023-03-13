import glob
import os
from flask import Flask


# run using `flask --app serve run`
app = Flask(__name__, static_url_path='', static_folder='static')
refresh_interval = 4.95  # refresh interval in seconds; slightly less double the extractor's rate

header1 = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">"""

header2 = """
    <link rel="stylesheet" type="text/css" href="style.css">
    <title>"""

header3 = """</title>
</head>
<body><div id="main">"""

footer = """</div></body>
</html>"""

refresh = ""
if refresh_interval:
    refresh = f"""<meta http-equiv="refresh" content="{refresh_interval}" />"""


@app.route("/")
def show_velocity():
    content = header1 + refresh + header2 + "Info" + header3
    try:
        list_of_files = glob.glob("journey_started_*.csv")
        latest_file = max(list_of_files, key=os.path.getctime)
        with open(latest_file, 'r') as f:
            last_line = f.readlines()[-1]
            cells = last_line.split(";")
            # print(cells)  # log for debugging

            velocity = cells[1]
            content += f"""<div id="train_velocity">{velocity} km/h</div>"""

            lat = float(cells[-3])
            lon = float(cells[-2])

            # <div id="annotations"><a href="https://www.google.de/maps/@{lat},{lon},12z">Google Maps</a>
            content += f"""<div id="train_position">{lat:.6f}°{'N' if lat >= 0 else 'S'}, 
            {lon:.6f}°{'E' if lon >= 0 else 'W'}</div>
            <a href="https://www.openstreetmap.org/?mlat={lat}&mlon={lon}" target="_blank">OpenStreetMap</a>
            </div>"""
    except:  # TODO/FIXME: use a more specific exception handler
        content += "No journey file found or a processing error occurred."
    content += footer
    return content
