# Name: OneCall_Buffer-Intersect.py
# Author: Réal R. Provencher 2011
# Description: Creates a polygon shapefile with buffers around each line in the Gas_Lines layer, then splits these buffers along county lines. Each set of country buffers is exported to its own dated shapefile and zipped. These zips should be emailed to OneCall to serve as our dig safe areas.

# Import
print "Importing libraries..."
import arcpy
from arcpy import env
import datetime
import glob, os
import zipfile
import shutil
import time

# Environment settings
print "Setting environment..."
gdb = "S:\Hughes_ArcGIS\HNG new.gdb"
env.workspace = gdb

try:
	# Local variables
	print "Setting local variables..."
	today = datetime.date.today()
	formattedDate = today.strftime("%m%d%y")
	Gas_Lines = "Gas_Lines"
	Counties = "cty_big"
	desk = "OneCallWorkingDataset"
	destination = "S:\Hughes_ArcGIS\Python_Output\OneCall\\" + formattedDate + "\\"
	os.mkdir(destination)

	# Create a working area
	print "Creating temporary workspace..."
	if arcpy.Exists(desk):
		arcpy.Delete_management(desk)
	arcpy.CreateFeatureDataset_management(gdb,desk,Gas_Lines)

	# Working variables
	print "Setting working variables..."
	AP_Lines = desk + "\AP_Lines"
	HNG_Lines = desk + "\HNG_Lines"
	AP_Lines_Buffer = desk + "\AP_Lines_Buffer"
	HNG_Lines_Buffer = desk + "\HNG_Lines_Buffer"
	AP_Buffer_Width = "150 feet"
	HNG_Buffer_Width = "100 feet"
	AP_Lines_Intersect = desk + "\AP_Lines_Intersect"
	HNG_Lines_Intersect = desk + "\HNG_Lines_Intersect"
	AP_Lines_Multipart = desk + "\AP_Lines_Multipart"
	HNG_Lines_Multipart = desk + "\HNG_Lines_Multipart"

	print "Set up complete."
	print

	# Split Gas Lines by company
	print "Splitting Gas_Lines layer by company..."
	arcpy.Select_analysis(Gas_Lines,AP_Lines,'"company" = \'AP\'')
	print "-Created " + AP_Lines + ", number of features:"
	print arcpy.GetCount_management(AP_Lines)
	arcpy.Select_analysis(Gas_Lines,HNG_Lines,'"company" = \'HNG\'')
	print "-Created " + HNG_Lines + ", number of features:"
	print arcpy.GetCount_management(HNG_Lines)

	# Apply appropriate buffers to each company layer
	print "Buffering " + AP_Lines + " by " + AP_Buffer_Width + "..."
	arcpy.Buffer_analysis(AP_Lines,AP_Lines_Buffer,AP_Buffer_Width,"FULL","ROUND","ALL")
	print "Buffering " + HNG_Lines + " by " + HNG_Buffer_Width + "..."
	arcpy.Buffer_analysis(HNG_Lines,HNG_Lines_Buffer,HNG_Buffer_Width,"FULL","ROUND","ALL")

	# Intersect each buffered company layer with the counties layer
	print "Intersecting " + AP_Lines_Buffer + " with " + Counties + "..."
	arcpy.Intersect_analysis([AP_Lines_Buffer,Counties],AP_Lines_Intersect)
	print "Intersecting " + HNG_Lines_Buffer + " with " + Counties + "..."
	arcpy.Intersect_analysis([HNG_Lines_Buffer,Counties],HNG_Lines_Intersect)

	print

	# Select each feature out of the intersected layers to create the final batch of layers
	working_folders = []

	print "Pulling out each feature in " + AP_Lines_Intersect + "..."
	AP_features = arcpy.SearchCursor(AP_Lines_Intersect)
	for AP_feature in AP_features:
		shapefilename = "AP_Buffer_"+AP_feature.Name+"_"+formattedDate
		newdestination = destination + shapefilename + "\\"
		os.mkdir(newdestination)
		filepath = newdestination+shapefilename+".shp"
		arcpy.Select_analysis(AP_Lines_Intersect,filepath,'"Name" = \''+AP_feature.Name+'\'')
		# Created folder for layer
		
		zipped = zipfile.ZipFile(destination + shapefilename + ".zip","w")
		for name in glob.glob(newdestination+"\*"):
			zipped.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
		zipped.close()
		print "-Wrote to zip file " + shapefilename + ".zip"
		# Wrote folder to zip
		
		working_folders.append(destination + shapefilename)
		# Listing folder for deletion
		
	print
	print "Pulling out each feature in " + HNG_Lines_Intersect + "..."
	HNG_features = arcpy.SearchCursor(HNG_Lines_Intersect)
	for HNG_feature in HNG_features:
		shapefilename = "HNG_Buffer_"+HNG_feature.Name+"_"+formattedDate
		newdestination = destination + shapefilename + "\\"
		os.mkdir(newdestination)
		filepath = newdestination+shapefilename+".shp"
		HNG_Lines_Multipart_Feature = HNG_Lines_Multipart+'_'+HNG_feature.Name
		arcpy.Select_analysis(HNG_Lines_Intersect,HNG_Lines_Multipart_Feature,'"Name" = \''+HNG_feature.Name+'\'')
		arcpy.MultipartToSinglepart_management(HNG_Lines_Multipart_Feature,filepath)
		# Created folder for layer, pulled out single feature and separated disconnected pieces into features
		
		zipped = zipfile.ZipFile(destination + shapefilename + ".zip","w")
		for name in glob.glob(newdestination+"\*"):
			zipped.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
		zipped.close()
		print "-Wrote to zip file " + shapefilename + ".zip"
		
		working_folders.append(destination + shapefilename)
		# Listing folder for deletion

	# Wait for everything to settle
	print
	print "ZZzzz..."
	time.sleep(1)

	# Clean up
	print "Cleaning up..."
	for folder in working_folders:
		shutil.rmtree(folder)
	arcpy.Delete_management(desk)

	print "Done!"
except Exception as e:
	import sys
	print "Line #%i:" % (sys.exc_info()[2].tb_lineno)
	print e
	raw_input('')
	raise
