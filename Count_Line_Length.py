# Name: Count_Line_Length.py
# Author: Réal R. Provencher 2013
# Description: Splits gas lines layer (only HNG lines) along RRC area borders and counts length of all lines in each area. Generates a .csv table to report the data.
# NOTE: An updated version of this script has been incorporated into the Data_Integrity_Report.py maintenance script

# Import
print "Importing libraries..."
import arcpy
from arcpy import env
import csv

# Environment settings
print "Setting environment..."
gdb = "S:\Hughes_ArcGIS\HNG new.gdb"
env.workspace = gdb

# Local variables
print "Setting local variables..."

# First define the suffix for MakeFeatureLayer, list of working layers (polygons only), and field name
layersuffix = "_layer"
lines = "Gas_Lines"
RRC = "RRC_Areas"
intersection = "intersection"
calculated_field = "length_ft"

# Next do MakeFeatureLayer on each layer, naming the new layer using the suffix
arcpy.MakeFeatureLayer_management(lines,lines+layersuffix)
lines += layersuffix
arcpy.MakeFeatureLayer_management(RRC,RRC+layersuffix)
RRC += layersuffix

filename = "S:\Hughes_ArcGIS\Python_Output\Pipeline_Lengths.csv"
writer = csv.writer(open(filename,'wb'),dialect='excel')
writer.writerow(["Area","Length (ft)"])

print "Setup complete."
print

try:
	# Grabbing only HNG lines, splitting along RRC area borders, and calculating length
	arcpy.SelectLayerByAttribute_management(lines,"NEW_SELECTION",""" "company" = 'HNG' """)
	arcpy.Intersect_analysis([lines,RRC],intersection,"","","LINE")
	arcpy.CalculateField_management(intersection,calculated_field,"float(!SHAPE.length@FEET!)","PYTHON")

	arcpy.MakeFeatureLayer_management(intersection,intersection+layersuffix)
	intersection += layersuffix

	# Now doing the individual totals
	totallength = 0.0
	areas = arcpy.SearchCursor(RRC)
	for area in areas:
	    arcpy.SelectLayerByAttribute_management(RRC,"NEW_SELECTION",'"OBJECTID" = ' + str(area.OBJECTID))
	    arcpy.SelectLayerByLocation_management(intersection,"WITHIN",RRC)
	    features = arcpy.SearchCursor(intersection)
	    length = 0.0
	    for feature in features:
	        if isinstance(feature.length_ft,float):
	            length += feature.length_ft
	    print str(int(length)) + " feet of pipe in " + str(area.Name)
	    writer.writerow([str(area.Name),int(length)])
	    totallength += length

	print str(int(totallength)) + " feet of pipe total (" + str(round(totallength/5280,1)) + " miles)"


	print "Cleaning up..."
	arcpy.Delete_management(intersection)

	print "Done!"
	raw_input('')
except Exception as e:
	import sys
	print "Line #%i:" % (sys.exc_info()[2].tb_lineno)
	print e
	raw_input('')
	if arcpy.Exists(intersection):
		arcpy.Delete_management(intersection)
	raise
