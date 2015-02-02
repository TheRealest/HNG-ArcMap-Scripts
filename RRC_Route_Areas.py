# Name: RRC_Route_Areas.py
# Description: Generates report detailing meter counts split by various areas for taxing purposes.
# Author: Réal R. Provencher 2012

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
meters = "meter_ref"
layers = ["RRC_Areas", "Route_Areas", "ESDs", "ISDs"]
field = "Meters_Inside"
filepath = "S:\\Hughes_ArcGIS\\Python_Output\\"

# ReturnDesignator allows the calculation loop to report counts inside individual features in the terminal. The layer names need to include the suffix because this will be called at the end of the loop. Match these cases with the 'layers' array above

def ReturnDesignator(feature,layer):
	if layer == 'RRC_Areas' + layersuffix:
		return str(feature.Name)
	elif layer == 'Route_Areas' + layersuffix:
		return "route number " + str(feature.Number)
	elif layer == 'ESDs' + layersuffix:
		return "ESD #" + str(feature.NUMBER) + " in " + str(feature.COUNTY) + " county"
	elif layer == 'ISDs' + layersuffix:
		return str(feature.NAME)
	else:
		print "Update ReturnDesignator function!"	

# Next do MakeFeatureLayer on each layer, naming the new layer using the suffix
for layer in layers:
	arcpy.MakeFeatureLayer_management(layer,layer+layersuffix)
arcpy.MakeFeatureLayer_management(meters,meters+layersuffix)
meters += layersuffix

# Count meters for validation purposes
metercount = int(str(arcpy.GetCount_management(meters)))

print "Setup complete."
print

# Now the loop to count meters inside each feature in each layer, and calculate "Meters_Inside"
for layer in layers:
	writer = csv.writer(open(filepath+layer+".csv",'wb'),dialect='excel')
	writer.writerow(["Area","Count"])
	total = 0
	rows = []
	print "Counting meters in \"" + layer + "\"..."
	layer += layersuffix
	features = arcpy.SearchCursor(layer)
	for feature in features:
		arcpy.SelectLayerByAttribute_management(layer,"NEW_SELECTION",'"OBJECTID" = ' + str(feature.OBJECTID))
		arcpy.SelectLayerByLocation_management(meters,"WITHIN",layer)
		count = arcpy.GetCount_management(meters)
		count = int(str(count))
		arcpy.CalculateField_management(layer,field,count,"PYTHON","")
		print str(count) + " meters in " + ReturnDesignator(feature,layer)
		writer.writerow([ReturnDesignator(feature,layer),count])
		total += count
	print
	print str(total) + " meters accounted for and " + str(metercount) + " total meters"
	if total == metercount:
		print "All meters accounted for!"
	else:
		print str(metercount - total) + " meters missing!"
	
	print




print "Done!"
raw_input('')
