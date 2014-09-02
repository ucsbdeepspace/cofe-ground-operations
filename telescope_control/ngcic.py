# ngcic.py
# process and retrieve positions of objects in the NGC/IC catalogs

import csv

# pos_list: retrieve a list of all objects from the catalog
#
#   csv_file: ';' delimited file with format: _RAJ2000;_DEJ2000;Cat;NGC/IC
#
# -> result -> list([name, point -> [ra, de]]): list of objects and positions
def pos_list (csv_file):
    fp = open(csv_file, "rb")
    reader = csv.reader(fp, delimeter=';')
    
    result = []
    start = False
    
    for row in reader:
        if row: # skip blank lines
        
            if start: # read data if we're past headers
                result.append([ # name
                    (row[2] == "I" and "IC " or "NGC ") + str(int(row[3])),
                    # equatorial position
                    [float(row[0]), float(row[1])]])
            
            # update whether we've past headers
            if not start and row[0][:1] == "--":
                start = True
