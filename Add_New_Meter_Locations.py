# Name: Add_New_Meter_Locations.py
# Author: Réal R. Provencher 2011
# Description: Looks through customer records in the CUSI_meters spreadsheet, compares it to meter locations already created in the ESRI_meters shapefile, and adds any missing meters to the geodatabase, using the latitude and longitude in the customer info table to place the point in the shapefile. Also checks for duplicate service IDs (which should be unique) among the customer records.
# NOTE: An updated version of this script has been incorporated into the Data_Integrity_Report.py maintenance script

try:
	# Import
	print "Importing libraries..."
	import arcpy
	from arcpy import env
	import xlrd

	# Environment settings
	print "Setting environment..."
	gdb = "S:\Hughes_ArcGIS\HNG new.gdb"
	env.workspace = gdb

	# Local variables
	print "Setting local variables..."
	ESRI_meters = "meter_ref"
	CUSI_meters = "S:\Hughes_ArcGIS\current_customer_info.xls"
	CUSI_reader = xlrd.open_workbook(CUSI_meters)
	CUSI_sheet = CUSI_reader.sheet_by_index(0)
	print

	# Getting lists of meters in the ESRI and CUSI databases
	print "Getting ESRI service IDs..."
	ESRI_cursor = arcpy.SearchCursor(ESRI_meters)
	ESRI_list = []
	for feature in ESRI_cursor:
		ESRI_list.append(int(feature.serv_id))
	ESRI_set = set(ESRI_list)
	print "ESRI has %i features (%i unique), last service ID is %i" % (len(ESRI_list),len(ESRI_set),ESRI_list[-1])
	print

	print "Getting CUSI service IDs..."
	CUSI_list = map(int,CUSI_sheet.col_values(2)[1:])
	CUSI_set = set(CUSI_list)
	print "CUSI has %i features (%i unique), last service ID is %i" % (len(CUSI_list), len(CUSI_set),CUSI_list[-1])
	print

	union = list(ESRI_set|CUSI_set)
	not_in_ESRI = list(CUSI_set-ESRI_set)
	print "Together they have %i unique features total, and %i meters are missing from ESRI" % (len(union),len(not_in_ESRI))

	ESRI_doubles_list = ESRI_list[:]
	for entry in list(ESRI_set):
		ESRI_doubles_list.remove(entry)
	if len(ESRI_doubles_list) > 0:
		print str(len(set(ESRI_doubles_list))) + " service IDs occur more than once in ESRI."

		# Create new search cursor to go through ESRI data, deleting old if nec.
		if ESRI_cursor: del ESRI_cursor
		ESRI_cursor = arcpy.SearchCursor(ESRI_meters)
		# This will print an array of lat/long/serv_id of all muliple data points
		ESRI_doubles_data = []
		for feature in ESRI_cursor:
			if int(feature.serv_id) in ESRI_doubles_list:
				ESRI_doubles_data.append([feature.serv_id,feature.latitude,feature.longitude])
		print "All ESRI features which have the same service ID as another feature:"
		print
		for feature in ESRI_doubles_data:
			print feature
		print
	else:
		print "Every service ID in ESRI is unique (no doubles)"
		print

	print "Service IDs missing from ESRI:"
	print not_in_ESRI
	print
	# now to see if we have lat/long data for the missing meters
	missing_meters = []
	dead_meters = []
	for i in range(CUSI_sheet.nrows)[1:]:
		if int(CUSI_sheet.row_values(i)[2]) in not_in_ESRI:
			missing_meters.append(CUSI_sheet.row_values(i)[:3])
	for feature in missing_meters:
		if str(feature[0]) != '':
			print "Service ID %i should be located at lat/long %s/%s" % (int(feature[2]),str(feature[0]),str(feature[1]))
		else:
			dead_meters.append(feature)
	print
	print "Still %i meters without any lat/long data." % (len(dead_meters))
	print "Service IDs: ",
	for feature in dead_meters:
		print str(int(feature[2])) + ",",
	print
	print

	add_cursor = arcpy.InsertCursor(ESRI_meters)
	# Now to create those missing meters
	print "Creating missing meters in ESRI..."
	for feature in missing_meters:
		if str(feature[0]) != '':
			new_feature = add_cursor.newRow()
			new_feature.Shape = arcpy.Point(feature[1],feature[0])
			new_feature.serv_id = feature[2]
			add_cursor.insertRow(new_feature)
			print "Added " + str(feature[2])
		else:
			print str(feature[2]) + " has no lat/long info and could not be added to ESRI"


	print
	print "Done!"
	raw_input('')
except Exception as e:
	print e
	raw_input('')
	raise
