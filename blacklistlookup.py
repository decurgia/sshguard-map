import argparse
import urllib.request
import urllib.parse
import urllib.error
import ssl
import base64
import sqlite3
import json

parser = argparse.ArgumentParser(description="Lookup coordinates of IP addresses.")
parser.add_argument(
    "-u",
    "--username",
    dest="username",
    required=True,
    type=str,
    help="Maxmind username",
)
parser.add_argument(
    "-p",
    "--password",
    dest="password",
    required=True,
    type=str,
    help="Maxmind password",
)

args = parser.parse_args()

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Sign-up at https://www.maxmind.com/en/geolite2/signup
# Then generate username & password at https://www.maxmind.com/en/accounts/current/license-key
b64auth = base64.standard_b64encode(
    (args.username + ":" + args.password).encode("utf-8")
).decode()


def retrieve_latlongorgiso(ip_address):
    url = "https://geolite.info/geoip/v2.1/city/" + ip_address
    request = urllib.request.Request(url)
    request.add_header("Authorization", "Basic " + b64auth)
    geoip_url = urllib.request.urlopen(request, context=ctx)
    geoip_data = geoip_url.read().decode()
    geoip_json = json.loads(geoip_data)
    latitude = 0.0
    longitude = 0.0
    organization = ""
    iso_code = ""
    try:
        latitude = geoip_json["location"]["latitude"]
        longitude = geoip_json["location"]["longitude"]
        organization = geoip_json.get["traits"]["autonomous_system_organization"]
        iso_code = geoip_json["country"]["iso_code"]
    except KeyError as err:
        print("KeyError", err)
        print(ip_address, geoip_json)
    return [latitude, longitude, organization, iso_code]


blacklist_db = sqlite3.connect("blacklist.sqlite")
cur_single = blacklist_db.cursor()

# First try to lookup the IPs without latitude and longitude
blacklist_incomplete_list = blacklist_db.cursor()
blacklist_incomplete_list.execute(
    """SELECT ip_address
               FROM Blacklist
               WHERE latitude is NULL
               OR longitude is NULL
               OR organization is NULL
               OR iso_code is NULL"""
)

for row in blacklist_incomplete_list:
    ip_address = str(row[0].strip())
    try:
        latlongorgiso = retrieve_latlongorgiso(ip_address)
    except urllib.error.HTTPError as err:
        print("Lookup incomplete", err)
        blacklist_db.commit()
        quit()
    cur_single.execute(
        """UPDATE Blacklist
                SET latitude = ?,
                    longitude = ?,
                    organization = ?,
                    iso_code = ?
                WHERE ip_address = ?""",
        (
            latlongorgiso[0],
            latlongorgiso[1],
            latlongorgiso[2],
            latlongorgiso[3],
            ip_address,
        ),
    )
blacklist_db.commit()
blacklist_incomplete_list.close()

# Then try to update the ones which were updated the last
blacklist_last_updated_list = blacklist_db.cursor()
blacklist_last_updated_list.execute(
    """SELECT ip_address
               FROM Blacklist
               WHERE updated_on < DATETIME('now', '-6 month')
               ORDER BY updated_on ASC"""
)

for row in blacklist_last_updated_list:
    ip_address = str(row[0].strip())
    try:
        latlongorgiso = retrieve_latlongorgiso(ip_address)
    except urllib.error.HTTPError as err:
        print("Lookup latest", err)
        blacklist_db.commit()
        quit()
    cur_single.execute(
        """UPDATE Blacklist
                SET latitude = ?,
                    longitude = ?,
                    organization = ?,
                    iso_code = ?
                WHERE ip_address = ?""",
        (
            latlongorgiso[0],
            latlongorgiso[1],
            latlongorgiso[2],
            latlongorgiso[3],
            ip_address,
        ),
    )
blacklist_db.commit()
blacklist_last_updated_list.close()

blacklist_db.commit()
