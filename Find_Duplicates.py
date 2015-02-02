# Name: Find_Duplicates.py
# Author: Réal R. Provencher 2013
# Description: Finds duplicate lines (identical spatially coincident line features) and reports them from review.

# Import
print "Importing libraries..."
import arcpy
from arcpy import env

# Environment settings
print "Setting environment..."
gdb = "S:\Hughes_ArcGIS\HNG new.gdb"
env.workspace = gdb

# Local variables
print "Setting local variables..."

# First define the suffix for MakeFeatureLayer, list of working layers (polygons only), and field name
layersuffix = "_layer"
lines = "Gas_Lines"
calculated_field = "length_ft"

# Next do MakeFeatureLayer on each layer, naming the new layer using the suffix
arcpy.MakeFeatureLayer_management(lines,lines+layersuffix)
lines += layersuffix

print "Setup complete."
print

try:
	# Grabbing only HNG lines
	arcpy.SelectLayerByAttribute_management(lines,"NEW_SELECTION",""" "company" = 'HNG' """)

	# Looping through line features
	features = arcpy.SearchCursor(lines)
	extralength = 0.0
	totallength = 0.0
	for feature in features:
		# Get line at cursor and select geometrically identical features
		arcpy.SelectLayerByAttribute_management(lines,"NEW_SELECTION",'"OBJECTID" = ' + str(feature.OBJECTID))
		arcpy.SelectLayerByLocation_management(lines,"ARE_IDENTICAL_TO",lines)
		dupes = int(str(arcpy.GetCount_management(lines)))
		if dupes > 1:
			length = str(feature.length_ft)
			if length == "None":
				length = 0.0
			else:
				length = float(length)
			print "Feature %i is identical to %i other feature and has length %.2f" % (feature.OBJECTID,(dupes-1),length)
			extralength += length*(float(dupes-1)/float(dupes))
			totallength += length
	print
	print "Total length of all features with duplicates: %f ft" % (totallength)
	print "Total extra length due to duplicates: %f ft (%f mi)" % (extralength,extralength/5280)
	print "Duplication factor: %f" % (totallength/(totallength-extralength))

	print "Cleaning up..."

	print "Done!"
	raw_input('')
except Exception as e:
	import sys
	print "Line #%i:" % (sys.exc_info()[2].tb_lineno)
	print e
	raw_input('')
	raise
