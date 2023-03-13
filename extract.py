from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
import selenium.common.exceptions
import re
import math


def get_xyz_from_style(style):
    # extract the 3D translation coordinates from HTML style tag using regular expressions
    # 'translate3d(...)'; return as signed integer values
    re_result = re.search('translate3d\\((-?[0-9]+)px, (-?[0-9]+)px, (-?[0-9]+)px\\)', style)
    x = int(re_result.group(1))
    y = int(re_result.group(2))
    z = int(re_result.group(3))
    return x, y, z


def get_xy_zoom_from_map_tile_url(url):
    # extract the x, y, z coordinates from HTML style tag using regular expressions
    # 'maps/<zoom>/<x>/<y>.png'; return as signed integer values
    re_result = re.search('maps/([0-9]+)/([0-9]+)/([0-9]+)\\.png', url)
    zoom = int(re_result.group(1))
    x = int(re_result.group(2))
    y = int(re_result.group(3))
    return x, y, zoom


def get_lat_lon_from_xy_zoom(x, y, zoom):
    # get latitude and longitude in degrees from x, y and zoom
    n = 2.0 ** zoom
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def get_datetime_str(for_filename=False):
    # get date/time to be used for logging, as part of file name and exported CSV data
    if for_filename:
        datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime_str


def get_csv_line_from_entry(entry):
    # format CSV output line from dictionary
    line = f"{entry['datetime']};{entry['velocity']};"
    line += f"{entry['map_pane'][0]};{entry['map_pane'][1]};{entry['map_pane'][2]};"
    line += f"{entry['tile_container'][0]};{entry['tile_container'][1]};{entry['tile_container'][2]};"
    line += f"{entry['tile_loaded'][0]};{entry['tile_loaded'][1]};{entry['tile_loaded'][2]};"
    line += f"{entry['tile_coords'][0]};{entry['tile_coords'][1]};{entry['tile_coords'][2]};"
    line += f"{entry['tile_coords'][3]};{entry['tile_coords'][4]};"
    line += "\n"
    return line


if __name__ == '__main__':
    refresh_interval = 10  # refresh interval in seconds; the map seems to refresh every 10 seconds
    initial_startup_wait_time = 5  # in seconds
    no_such_window_err_text = "Browsing context has been discarded. Did you close Firefox?"
    wrong_wifi_err_text = "It's very likely that you're not connected to the train's WiFi."

    # get current date/time to be used for logging, as part of file name and exported CSV data
    datetime_str = get_datetime_str()

    browser = webdriver.Firefox()
    browser.get('https://iceportal.de/Karte_neu')
    sleep(initial_startup_wait_time)

    wifi_on_ice = False
    try:
        hint_elem = browser.find_element(
            By.XPATH, "/html/body/div")
        # are you actually connected with the train WiFi?
        # the following text will be part of the website when accessed from global internet
        if "Sind Sie mit dem WLAN im Zug verbunden?" in hint_elem.text:
            # raise ValueError(wrong_wifi_err_text)
            pass
        wifi_on_ice = True
    except selenium.common.exceptions.NoSuchWindowException as e:
        print(f"[{datetime_str}] " + no_such_window_err_text)
        raise e
    except ValueError as e:
        print(f"[{datetime_str}] " + wrong_wifi_err_text + " Aborting.")
        raise e

    filename = "journey_started_" + get_datetime_str(True) + ".csv"
    with open(filename, 'w') as f:
        while True:
            sleep(refresh_interval)

            # get updated current date/time to be used for logging, as part of file name and exported CSV data
            datetime_str = get_datetime_str()
            entry = {
                'datetime': datetime_str,
                'velocity': None,
                'map_pane': None,
                'tile_container': None,
                'tile_loaded': None,
                'tile_coords': None
            }
            try:
                print(f"[{datetime_str}] ", end="")

                velocity_elem = browser.find_element(
                    By.XPATH, "/html/body/div/div[2]/div/div/div[1]/a/div[1]/div/div/div")
                entry['velocity'] = int(velocity_elem.text.replace("\n", " ").replace("km/h", ""))

                map_tile_base_xpath = "/html/body/div/div[1]/div/div/main/section/div/div/div[1]"

                leaflet_map_pane_elem = browser.find_element(
                    By.XPATH, map_tile_base_xpath)
                x, y, z = get_xyz_from_style(leaflet_map_pane_elem.get_attribute("style"))
                entry['map_pane'] = [x, y, z]

                leaflet_tile_container_elem = browser.find_element(
                    By.XPATH, map_tile_base_xpath + "/div[1]/div/div")
                x, y, z = get_xyz_from_style(leaflet_tile_container_elem.get_attribute("style"))
                entry['tile_container'] = [x, y, z]

                leaflet_tile_loaded_elem = browser.find_element(
                    By.XPATH, map_tile_base_xpath + "/div[1]/div/div/img[1]")
                x, y, z = get_xyz_from_style(leaflet_tile_loaded_elem.get_attribute("style"))
                entry['tile_loaded'] = [x, y, z]

                map_tile_src_url = leaflet_tile_loaded_elem.get_attribute("src")
                x, y, zoom = get_xy_zoom_from_map_tile_url(map_tile_src_url)
                lat, lon = get_lat_lon_from_xy_zoom(x, y, zoom)
                entry['tile_coords'] = [x, y, zoom, lat, lon]

                print(entry)  # print extracted data, stored in dictionary for debugging
                csv_line = get_csv_line_from_entry(entry)

                # write a row to the csv file
                # print(csv_line)  # may print CSV line that's going to be written
                f.write(csv_line)
                f.flush()  # directly flush the data, so that it can be accessed by another application
            except selenium.common.exceptions.NoSuchElementException as e:
                print(wrong_wifi_err_text + " Retrying.")
                pass  # try again
            except selenium.common.exceptions.NoSuchWindowException as e:
                print(no_such_window_err_text)
                raise e
