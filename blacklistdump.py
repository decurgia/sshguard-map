import argparse
import sqlite3
import json

parser = argparse.ArgumentParser(description='Dump coordinates into file.')
parser.add_argument('-o', '--output',
                    default='./markers.json',
                    type=str,
                    help='Path to markers.json file (default: ./markers.json)')
args = parser.parse_args()

blacklist_db = sqlite3.connect('blacklist.sqlite')
blacklist_cursor = blacklist_db.cursor()
blacklist_cursor.execute('''SELECT latitude, longitude, organization, count() AS count
               FROM Blacklist
               WHERE latitude IS NOT NULL
               AND longitude IS NOT NULL
               GROUP BY latitude || longitude || organization
               ORDER BY longitude, count DESC;''')


markers_dict = {}
for row in blacklist_cursor:
    latitude = float(row[0])
    longitude = float(row[1])
    organization = str(row[2])
    count = int(row[3])
    markerid = str(latitude) + str(longitude)
    curmarker = markers_dict.get(markerid, (0, 0, "", 0))
    description = (curmarker[2]
                   + "\n"
                   + organization
                   + " ("
                   + str(count)
                   + ")").strip()
    description = description.replace('\n', '<br />')
    total = curmarker[3] + count
    markers_dict[markerid] = (latitude, longitude, description, total)
blacklist_cursor.close()

markers_list = []
for entry in markers_dict.values():
    marker = {}
    marker["latitude"] = entry[0]
    marker["longitude"] = entry[1]
    marker["description"] = entry[2]
    marker["total"] = entry[3]
    markers_list.append(marker)

markers_file = open(args.output, 'w')
markers_file.write("markers = " + json.dumps(markers_list, indent=4))
markers_file.close()

print("Dumped", len(markers_list), "markers")
