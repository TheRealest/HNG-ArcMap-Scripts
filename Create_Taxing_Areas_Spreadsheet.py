# Name: Create_Taxing_Areas_Spreadsheet.py
# Description: Generates taxing districts report spreadsheet in proper format for submittal to taxing authorities.
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
env.overwriteOutput = True

# Local variables
print "Setting local variables..."

# First define the suffix for MakeFeatureLayer, list of working layers (polygons only), and field name
layersuffix = "_layer"
meters = "meter_ref"
districts = "Districts"
ESDs_layer, ISDs_layer = districts + "\ESDs", districts + "\ISDs"
filename = "S:\\Hughes_ArcGIS\\Python_Output\\Taxing_Areas.csv"
customer_info_xls = "S:\Hughes_ArcGIS\current_customer_info.xls"
writer = csv.writer(open(filename,'wb'),dialect='excel')

# This is the header row in the *.csv file
print "Writing header row..."
writer.writerow(["County","ISD","ESD","ACTIVE/ON","INACTIVE/ON","OFF","TOTAL"])

print
# Next do MakeFeatureLayer on each layer, naming the new layer using the suffix
arcpy.MakeFeatureLayer_management(ESDs_layer,ESDs_layer+layersuffix)
arcpy.MakeFeatureLayer_management(ISDs_layer,ISDs_layer+layersuffix)
arcpy.MakeFeatureLayer_management(meters,meters+layersuffix)
ESDs_layer += layersuffix
ISDs_layer += layersuffix
meters += layersuffix

try:
	# Joining the customer info for ACTIVE/INACTIVE calculation
	print "Joining customer info to meters layer..."
	customer_info_table = "customer_info_table"
	arcpy.ExcelToTable_conversion(customer_info_xls,customer_info_table,"servloc")
	arcpy.AddJoin_management(meters,"serv_id",customer_info_table,"serv_id")

	# Count meters for validation purposes
	metercount = int(str(arcpy.GetCount_management(meters)))
	print "%i features in meter layer" % (metercount)

	print "Setup complete."
	print


	# Now loop inside ESDs_layer and then ISDs_layer
	print "Creating *.csv file..."
	ESD_OBJECTID = {}
	ESDs = arcpy.SearchCursor(ESDs_layer)
	for ESD in ESDs:
		ESD_OBJECTID[ESD.OBJECTID] = [ESD.COUNTY,ESD.NUMBER]

	# total is the total number of meters counted, ISD_total is the total number of meters inside the current ISD, and ESD_counted is the number of meters in the current ISD which have been accounted for within an ESD. After ESD looping, the difference between ISD_total and ESD_counted is the number of meters inside the current ISD which do not have an ESD.
	activeontotal, inactiveontotal, offtotal, total = 0, 0, 0, 0
	ISD_total, ESD_counted = 0, 0
	# number_of_ISDs and ISD_counter are just used to print to the terminal to give an indication of how far along the scripts is.
	number_of_ISDs = arcpy.GetCount_management(ISDs_layer)
	ISD_counter = 0
	ISDs = arcpy.SearchCursor(ISDs_layer)
	for ISD in ISDs:
		ISD_counter += 1
		print "Calculating " + str(ISD_counter) + "/" + str(number_of_ISDs) + " (" + str(ISD.NAME) + ")"
		arcpy.SelectLayerByAttribute_management(ISDs_layer,"NEW_SELECTION",'"OBJECTID" = ' + str(ISD.OBJECTID))
		arcpy.SelectLayerByLocation_management(meters,"WITHIN",ISDs_layer)
		ISD_total = int(str(arcpy.GetCount_management(meters)))
		ESD_counted, ESD_active_on_counted = 0, 0
		ESD_inactive_on_counted, ESD_off_counted = 0, 0
		if ISD_total > 0:
			for ESD in ESD_OBJECTID:
				arcpy.SelectLayerByAttribute_management(ISDs_layer,"NEW_SELECTION",'"OBJECTID" = ' + str(ISD.OBJECTID))
				arcpy.SelectLayerByLocation_management(meters,"WITHIN",ISDs_layer)
				arcpy.SelectLayerByAttribute_management(ESDs_layer,"NEW_SELECTION",'"OBJECTID" = ' + str(ESD))
				arcpy.SelectLayerByLocation_management(meters,"WITHIN",ESDs_layer,"","SUBSET_SELECTION")
				count = int(str(arcpy.GetCount_management(meters)))
				print ".",
				if count > 0:
					arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.serv_stat = \'ACTIVE\'')
					arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.meter_on = 1')
					activeoncount = int(str(arcpy.GetCount_management(meters)))
					arcpy.SelectLayerByLocation_management(meters,"WITHIN",ISDs_layer)
					arcpy.SelectLayerByLocation_management(meters,"WITHIN",ESDs_layer,"","SUBSET_SELECTION")
					arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.serv_stat = \'INACTIVE\'')
					arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.meter_on = 1')
					inactiveoncount = int(str(arcpy.GetCount_management(meters)))
					arcpy.SelectLayerByLocation_management(meters,"WITHIN",ISDs_layer)
					arcpy.SelectLayerByLocation_management(meters,"WITHIN",ESDs_layer,"","SUBSET_SELECTION")
					arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.meter_on = 0')
					offcount = int(str(arcpy.GetCount_management(meters)))
					writer.writerow([ESD_OBJECTID[ESD][0],ISD.NAME2,ESD_OBJECTID[ESD][0] + " " + ESD_OBJECTID[ESD][1],activeoncount,inactiveoncount,offcount,count])
					
					ESD_counted += count
					ESD_active_on_counted += activeoncount
					ESD_inactive_on_counted += inactiveoncount
					ESD_off_counted += offcount

					total += count
					activeontotal += activeoncount
					inactiveontotal += inactiveoncount
					offtotal += offcount
			print
		if ESD_counted != ISD_total and ISD_total > 0:
			arcpy.SelectLayerByAttribute_management(ISDs_layer,"NEW_SELECTION",'"OBJECTID" = ' + str(ISD.OBJECTID))
			arcpy.SelectLayerByLocation_management(meters,"WITHIN",ISDs_layer)
			count = int(str(arcpy.GetCount_management(meters)))
			count -= ESD_counted
			arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.serv_stat = \'ACTIVE\'')
			activeoncount = int(str(arcpy.GetCount_management(meters)))
			activeoncount -= ESD_active_on_counted
			arcpy.SelectLayerByLocation_management(meters,"WITHIN",ISDs_layer)
			arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.serv_stat = \'INACTIVE\'')
			arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.meter_on = 1')
			inactiveoncount = int(str(arcpy.GetCount_management(meters)))
			inactiveoncount -= ESD_inactive_on_counted
			arcpy.SelectLayerByLocation_management(meters,"WITHIN",ISDs_layer)
			arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.serv_stat = \'INACTIVE\'')
			arcpy.SelectLayerByAttribute_management(meters,"SUBSET_SELECTION",customer_info_table+'.meter_on = 0')
			offcount = int(str(arcpy.GetCount_management(meters)))
			offcount -= ESD_off_counted
			writer.writerow(["",ISD.NAME2,"",activeoncount,inactiveoncount,offcount,count])

			total += count
			activeontotal += activeoncount
			inactiveontotal += inactiveoncount
			offtotal += offcount
									
	writer.writerow([])	
	writer.writerow(["","","TOTAL",activeontotal,inactiveontotal,offtotal,total])
	print
	print str(total) + " meters accounted for and " + str(metercount) + " total features in meter layer"
	if total == metercount:
		print "All meters accounted for!"
	else:
		print str(metercount - total) + " meters missing!"

	print

	print "Done!"
	raw_input('')
	arcpy.Delete_management(customer_info_table)
except Exception as e:
	import sys
	print "Line #%i:" % (sys.exc_info()[2].tb_lineno)
	print e
	raw_input('')
	arcpy.Delete_management(customer_info_table)
	raise
