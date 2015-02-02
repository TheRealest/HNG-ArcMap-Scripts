# Name: Update_Meters_Fields.py
# Description: Updates meters attribute data with correct spatial data from RRC area and routes layers, as well as latitude and longitude of each meter location.
# Author: Réal R. Provencher 2012

print "Importing libraries..."
import arcpy
from arcpy import env
env.workspace = "S:\Hughes_ArcGIS\HNG new.gdb"

print "Setting up..."
RRC = "RRC_Areas"
Routes = "Route_Areas"
meters = "meter_ref"
suffix = "_layer"

arcpy.MakeFeatureLayer_management(RRC,RRC+suffix)
arcpy.MakeFeatureLayer_management(Routes,Routes+suffix)
arcpy.MakeFeatureLayer_management(meters,meters+suffix)
RRC += suffix
Routes += suffix
meters += suffix

# Update RRC_Area field
print
print "Updating RRC_Area field..."
areas = arcpy.SearchCursor(RRC)
for area in areas:
	arcpy.SelectLayerByAttribute_management(RRC,"NEW_SELECTION",'"OBJECTID" = ' + str(area.OBJECTID))
	arcpy.SelectLayerByLocation_management(meters,"WITHIN",RRC)
	areacode = str(area.usercode)
	print "Editing meters within " + areacode + "..."
	rows = arcpy.UpdateCursor(meters)
	for row in rows:
		row.RRC_Area = areacode
		rows.updateRow(row)
	del row
	del rows
	
# Update Route_no field
print
print "Updating route_no field..."
areas = arcpy.SearchCursor(Routes)
for area in areas:
	arcpy.SelectLayerByAttribute_management(Routes,"NEW_SELECTION",'"OBJECTID" = ' + str(area.OBJECTID))
	arcpy.SelectLayerByLocation_management(meters,"WITHIN",Routes)
	areacode = int(str(area.Number))
	print "Editing meters within route number " + str(areacode) + "..."
	rows = arcpy.UpdateCursor(meters)
	for row in rows:
		row.route_no = areacode
		rows.updateRow(row)
	del row
	del rows

# Update lat/long fields
print
print "Updating latitude and longitude fields..."
arcpy.SelectLayerByAttribute_management(meters)
arcpy.CalculateField_management(meters,"latitude","float(!Shape.firstPoint.Y!)","PYTHON_9.3")
print "Latitudes finished"
arcpy.CalculateField_management(meters,"longitude","float(!Shape.firstPoint.X!)","PYTHON_9.3")
print "Longitudes finished"

print
print "Done!"
raw_input('')
