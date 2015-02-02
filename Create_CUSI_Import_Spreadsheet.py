# Name: Create_CUSI_Import_Spreadsheet.py
# Author: Réal R. Provencher 2012
# Description: Exports the geographic meter location data to .csv for importing into the CUSI billing system.

print "Importing libraries..."
import arcpy
from arcpy import env
env.workspace = "S:\Hughes_ArcGIS\HNG new.gdb"
import csv

print "Setting up..."
meters = "meter_ref"
filepath = "S:\\Hughes_ArcGIS\\Python_Output\\CUSI_Import.csv"

def writePaddedRow(writer,latitude,longitude,serv_id,route,RRC):
	row = [latitude,longitude,serv_id] + [""] * 8 + [str(route).zfill(2)] + [""] * 18 + [RRC]
	writer.writerow(row)

writer = csv.writer(open(filepath,'wb'),dialect='excel')
writePaddedRow(writer,"latitude","longitude","serv_id","route_no","user5")

print "Writing lines..."
points = arcpy.SearchCursor(meters)
for point in points:
	writePaddedRow(writer, point.latitude, point.longitude, point.serv_id, point.route_no, point.RRC_Area)

print
print "Done!"
