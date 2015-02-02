# Name: Data_Integrity_Report.py
# Author: Réal R. Provencher 2014
# ------------------------
# Combines several other reporting style ArcPy scripts to create a single
# spreadsheet report detailing the data integrity of our geodatabase. Each
# section of the report is divided into its own try/except block so a failing
# report will not prevent the entire report from being generated, and will
# also include an error message in the spreadsheet. The following info is
# included in the report:
    # - Taxing districts report (number of meters separated by ISD/ESD and 
    #    ACTIVE/INACTIVE/OFF meter location status)
    # - Pipeline length report (length of HNG lines separated by RRC area)
    # - New meter report (checks that all meters in ESRI and CUSI match each 
    #    other, that all meters are unique, that all meters have lat/longs, 
    #    and creates features in ESRI for missing service IDs)
    # - Check that all lines have a company ID, and report feature IDs for
    #    ones without
    # - Check that all meters are located with a RRC area and an ISD, and
    #    and report service IDs for meters which do not

### SCRIPT SETTINGS
# Settings which affect how the script runs. This is the only section which should be
# modified, and doing so only controls how the output is generated i.e. deciding
# whether to run certain modules, formatting results, etc.
MODULE_ON = {
    "TAXING_DISTRICTS": True,
    "PIPELINE_LENGTH": True,
    "VERIFY_METERS": True,
    "COMPANY_ID": True
}

OPTIONS = {
    "OUTPUT_FILEPATH": "S:\\Hughes_ArcGIS\\Python_Output\\Data_Integrity_Report.csv",
    "OVERWRITE_LAYERS": True,

    ### MODULE SPECIFIC OPTIONS
    # Organized by name of module
    "PIPELINE_LENGTH": {
        "TABLE_SETUP_QUERIES": [
            ["HNG PE", "company = 'HNG' AND (pipe_material = 'Black' OR pipe_material = 'Yellow' OR pipe_material = 'Orange')"],
            ["HNG Steel","company = 'HNG' AND pipe_material = 'Steel'"],
            ["Total HNG","company = 'HNG'"]
        ],
        "SIZE_CATEGORIES": {
            "<2\"": [0.75, 1.0, 1.25, 1.5],
            "2\"": [2],
            "3\"": [3],
            "4\"": [4],
            "6\"": [6],
            "Unknown": ['NULL']
        },
        "SIZE_ORDER": ["<2\"", "2\"", "3\"", "4\"", "6\"", "Unknown"]
    },
    "COMPANY_ID": {
        "INCLUDE_COMPANY": ["HNG", "AP"]
    }
}

### HELPER FUNCTIONS
# Several helper functions that are used in multiple modules

# Helpers to be used at the beginning and end of each module try block to indicate in
# the console where these events occure (must set variable modulename)
def print_module_start():
    print "--- STARTING %s MODULE ---" % (modulename)
def print_module_end():
    print "--- FINISHED %s MODULE ---" % (modulename)
    print

# Prints a helpful formatted version of the passed exception, running the passed
# block after pressing enter if one is included
def print_formatted_error(e, block=None):
    if type(e) is not SkipException:
        import sys
        line = sys.exc_info()[2].tb_lineno
        send("ERROR in module %s at line #%i" % (modulename,line))
    print e
    if block is not None:
        block()
    print "--- EXITED %s MODULE ---" % (modulename)
    print

# Custom Exception class for skipping modules
class SkipException(Exception):
    def __init__(self,module):
        self.module = module
    def __str__(self):
        return "Skipping module %s (disabled)..." % (self.module)

# Use this to send a string out to the console while running and also writer it to
# the spreadsheet output
def send(msg, blank=False):
    print msg
    if blank:
        writer.writerow(["",msg])
    else:
        writer.writerow([msg])

def format_query(field,value):
    if value == "NULL":
        return "%s IS NULL" % (field)
    elif type(value) == str:
        return "%s = '%s'" % (field, value)
    elif type(value) == int:
        return "%s = %i" %(field, value)
    elif type(value) == float:
        return "%s = %f" %(field, value)
    else:
        return "ERROR in format_query!"


### SETUP MODULE
# Imports necessary libraries, sets environment workspace, and creates CSV writer
# object.
try:
    modulename = "SETUP"
    print_module_start()

    print "Importing libraries..."
    import arcpy
    from arcpy import env
    import csv
    import xlrd

    # Environment settings
    print "Setting environment..."
    gdb = "S:\Hughes_ArcGIS\HNG new.gdb"
    env.workspace = gdb
    env.overwriteOutput = OPTIONS["OVERWRITE_LAYERS"]

    # Local variables
    print "Setting local variables..."
    writer = csv.writer(open(OPTIONS["OUTPUT_FILEPATH"],'wb'),dialect='excel')

    print_module_end()
except Exception as e:
    print_formatted_error(e)


### TAXING DISTRICTS MODULE
# Counts meters per ISD/ESD pair and ISD w/o an ESD. Also splits count up by
# ACTIVE/ON, INACTIVE/ON, and OFF. Checks that every meter is contained within an ISD
# and includes the number which don't.
try:
    modulename = "TAXING_DISTRICTS"
    print_module_start()
    if not MODULE_ON[modulename]: raise SkipException(modulename)

    ### Module variables 
    # First define the suffix for MakeFeatureLayer, working polygon layers, and
    # customer table
    print "Setting module variables..."
    layersuffix = "_layer"
    meters = "meter_ref"
    districts = "Districts"
    ESDs_layer, ISDs_layer = districts + "\ESDs", districts + "\ISDs"
    customer_info_xls = "S:\Hughes_ArcGIS\current_customer_info.xls"

    # This is the header row in the *.csv file
    print "Writing header row..."
    writer.writerow(["County","ISD","ESD","ACTIVE/ON","INACTIVE/ON","OFF","TOTAL"])

    # Next do MakeFeatureLayer on each layer, naming the new layer using the suffix
    print "Performing MakeFeatureLayer..."
    arcpy.MakeFeatureLayer_management(ESDs_layer,ESDs_layer+layersuffix)
    arcpy.MakeFeatureLayer_management(ISDs_layer,ISDs_layer+layersuffix)
    arcpy.MakeFeatureLayer_management(meters,meters+layersuffix)
    ESDs_layer += layersuffix
    ISDs_layer += layersuffix
    meters += layersuffix
    print "Module setup complete"
    print


    ### Analysis/reporting
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
    print "Writing data..."
    ESD_OBJECTID = {}
    ESDs = arcpy.SearchCursor(ESDs_layer)
    for ESD in ESDs:
        ESD_OBJECTID[ESD.OBJECTID] = [ESD.COUNTY,ESD.NUMBER]

    # Check that joined table actually carried over data
    print "Checking join..."
    pts = arcpy.SearchCursor(meters)
    pt = pts.next()
    if pt.getValue(customer_info_table+".serv_id") is None:
        send("**ERROR**")
        send("    Data in joined table not coming through, expect zeroes for ACTIVE/INACTIVE and ON/OFF columns (did you remember to delete column \"desc\"?)")
        send("*********")

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
    writer.writerow([]) 
    writer.writerow([]) 
    print
    print str(total) + " meters accounted for and " + str(metercount) + " total features in meter layer"
    if total == metercount:
        print "All meters accounted for!"
    else:
        print str(metercount - total) + " meters missing!"

    print

    arcpy.Delete_management(customer_info_table)
    print_module_end()
except Exception as e:
    print_formatted_error(e)


### PIPELINE LENGTH MODULE
# Counts pipeline length, split up by RRC area. The OPTIONS dictionary defined in the
# settings sections above determines which company IDs will be counted (not
# implemented, currently only calculates for HNG as this is the most common case).
try:
    modulename = "PIPELINE_LENGTH"
    print_module_start()
    if not MODULE_ON[modulename]: raise SkipException(modulename)

    ### Module variables 
    # First define the suffix for MakeFeatureLayer, list of working layers (polygons only), and field name
    print "Setting module variables..."
    layersuffix = "_layer"
    lines = "Gas_Lines"
    RRC = "RRC_Areas"
    intersection = "intersection"
    calculated_field = "length_ft"

    # Next do MakeFeatureLayer on each layer, naming the new layer using the suffix
    print "Performing MakeFeatureLayer..."
    arcpy.MakeFeatureLayer_management(lines,lines+layersuffix)
    lines += layersuffix
    arcpy.MakeFeatureLayer_management(RRC,RRC+layersuffix)
    RRC += layersuffix

    print "Module setup complete"
    print

    areas = [{'Name': row.Name, 'OBJECTID': row.OBJECTID} for row in arcpy.SearchCursor(RRC)]
    for tablesetup in OPTIONS[modulename]["TABLE_SETUP_QUERIES"]:
        writer.writerow([tablesetup[0]])

        # Header row for this module
        print "Creating table '%s' with setup query \"%s\"..." % (tablesetup[0],tablesetup[1])
        sizes = OPTIONS[modulename]["SIZE_CATEGORIES"]
        sizeorder = OPTIONS[modulename]["SIZE_ORDER"]
        header = ["Area"]
        for label in sizeorder:
            header.append(label)
        header.append("")
        header.append("Area Subtotal")
        writer.writerow(header)

        # Creating intersection layer based on table setup query
        print "Creating intersection layer based on table setup query..."
        intersection = intersection.strip(layersuffix)
        arcpy.SelectLayerByAttribute_management(lines,"NEW_SELECTION",tablesetup[1])
        arcpy.SelectLayerByAttribute_management(RRC,"CLEAR_SELECTION")
        arcpy.Intersect_analysis([lines,RRC],intersection,"","","LINE")
        arcpy.CalculateField_management(intersection,calculated_field,"float(!SHAPE.length@FEET!)","PYTHON")

        arcpy.MakeFeatureLayer_management(intersection,intersection+layersuffix)
        intersection += layersuffix
        print arcpy.GetCount_management(intersection)


        # Making the table
        print "Calculating table cells..."
        totallength = 0.0
        sizesubtotal = {}

        for area in areas:
            arealength = 0.0
            row = [str(area['Name'])]
            arcpy.SelectLayerByAttribute_management(RRC,"NEW_SELECTION",'"OBJECTID" = ' + str(area['OBJECTID']))
            
            for sizelabel in sizeorder:
                length = 0.0
                for size in sizes[sizelabel]:
                    arcpy.SelectLayerByLocation_management(intersection,"WITHIN",RRC)
                    arcpy.SelectLayerByAttribute_management(intersection,"SUBSET_SELECTION",format_query('pipe_size',size))

                    for feature in arcpy.da.SearchCursor(intersection,['length_ft']):
                        if isinstance(feature[0],float):
                            length += feature[0]

                lengthmi = round(length/5280,3)
                row.append(lengthmi)
                if sizelabel in sizesubtotal:
                    sizesubtotal[sizelabel] += lengthmi
                else:
                    sizesubtotal[sizelabel] = lengthmi
                arealength += lengthmi
            print "%.3f mi of pipe in area %s" % (arealength, str(area['Name']))
            row.append("")
            row.append(arealength)
            writer.writerow(row)
            totallength += arealength

        print "%.3f mi of pipe total for '%s'" % (totallength,tablesetup[0])
        writer.writerow([])

        row = ["Size Subtotal"]
        for label in sizeorder:
            row.append(sizesubtotal[label])
        row.append("")
        row.append(totallength)
        writer.writerow(row)
        writer.writerow([])

        print "Cleaning up table '%s'..." % (tablesetup[0])
        arcpy.Delete_management(intersection)
        print

    # Check Total calculation for verification
    arcpy.SelectLayerByAttribute_management(lines,"NEW_SELECTION",""" "company" = 'HNG' """)
    arcpy.CalculateField_management(lines,calculated_field,"float(!SHAPE.length@FEET!)","PYTHON")
    checktotal = 0.0
    for line in arcpy.SearchCursor(lines):
        checktotal += line.length_ft
    checktotal = round(checktotal/5280,3)

    row = [""]
    for label in sizeorder:
        row.append("")
    row.append("Check Total")
    row.append(checktotal)
    writer.writerow(row)
    print "Check total has %.3f mi of pipe" % (checktotal)

    writer.writerow([]) 
    writer.writerow([]) 

    print_module_end()
except Exception as e:
    print_formatted_error(e)


### VERIFY METERS MODULE
# Verifies that meter info in CUSI and ESRI match.
try:
    modulename = "VERIFY_METERS"
    print_module_start()
    if not MODULE_ON[modulename]: raise SkipException(modulename)

    ### Module variables 
    print "Setting module variables..."
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
    writer.writerow(["Meter Report"])
    send("ESRI has %i features (%i unique), last service ID is %i" % (len(ESRI_list),len(ESRI_set),ESRI_list[-1]))
    print

    print "Getting CUSI service IDs..."
    CUSI_list = map(int,CUSI_sheet.col_values(2)[1:])
    CUSI_set = set(CUSI_list)
    send("CUSI has %i features (%i unique), last service ID is %i" % (len(CUSI_list), len(CUSI_set),CUSI_list[-1]))
    print

    union = list(ESRI_set|CUSI_set)
    not_in_ESRI = list(CUSI_set-ESRI_set)
    send("Together they have %i unique features total, and %i meters are missing from ESRI" % (len(union),len(not_in_ESRI)))

    ESRI_doubles_list = ESRI_list[:]
    for entry in list(ESRI_set):
        ESRI_doubles_list.remove(entry)
    if len(ESRI_doubles_list) > 0:
        send(str(len(set(ESRI_doubles_list))) + " service IDs occur more than once in ESRI.")

        # Create new search cursor to go through ESRI data, deleting old if nec.
        if ESRI_cursor: del ESRI_cursor
        ESRI_cursor = arcpy.SearchCursor(ESRI_meters)
        # This will print an array of lat/long/serv_id of all muliple data points
        ESRI_doubles_data = []
        for feature in ESRI_cursor:
            if int(feature.serv_id) in ESRI_doubles_list:
                ESRI_doubles_data.append([feature.serv_id,feature.latitude,feature.longitude])
        send("All ESRI features which have the same service ID as another feature:")
        print
        for feature in ESRI_doubles_data:
            writer.writerow(["",feature])
            print feature
        print
    else:
        send("Every service ID in ESRI is unique (no doubles)")
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
    send("Still %i meters without any lat/long data." % (len(dead_meters)))
    print "Service IDs: ",
    for feature in dead_meters:
        servid = str(int(feature[2]))
        writer.writerow(["",servid])
        print servid + ",",
    print
    print

    add_cursor = arcpy.InsertCursor(ESRI_meters)
    # Now to create those missing meters
    print "Creating missing meters in ESRI..."
    added_meters = 0
    for feature in missing_meters:
        if str(feature[0]) != '':
            new_feature = add_cursor.newRow()
            new_feature.Shape = arcpy.Point(feature[1],feature[0])
            new_feature.serv_id = feature[2]
            add_cursor.insertRow(new_feature)
            send("Added " + str(feature[2]))
            added_meters += 1
        else:
            send(str(feature[2]) + " has no lat/long info and could not be added to ESRI")
    send("Added %i new meters" % (added_meters))
    send("")

    print_module_end()
except Exception as e:
    print_formatted_error(e)


### COMPANY ID MODULE
# Uses the OPTIONS["COMPANY_ID"]["INCLUDE_COMPANY"] list to find and list line
# features which do not have the specified company IDs and lists them
try:
    modulename = "COMPANY_ID"
    print_module_start()
    if not MODULE_ON[modulename]: raise SkipException(modulename)

    ### Module variables 
    lines = "Gas_Lines"
    suffix = "_layer"
    allowed = OPTIONS["COMPANY_ID"]["INCLUDE_COMPANY"]

    ### Preparing lines layer
    print "Preparing lines..."
    arcpy.MakeFeatureLayer_management(lines,lines+suffix)
    lines += suffix

    ### Checking company ID
    first = True
    for company in allowed:
        if first:
            arcpy.SelectLayerByAttribute_management(lines,"NEW_SELECTION","company = \'%s\'" % (company))
            first = False
        else:
            arcpy.SelectLayerByAttribute_management(lines,"ADD_TO_SELECTION","company = \'%s\'" % (company))
    arcpy.SelectLayerByAttribute_management(lines,"SWITCH_SELECTION")
    total_bad = int(arcpy.GetCount_management(lines).getOutput(0))
    
    if total_bad > 0:
        send("%i gas line features without valid company IDs" % (total_bad))
        send("OBJECTIDs:")
        for line in arcpy.SearchCursor(lines):
            send(line.getValue("OBJECTID"),True)
    else:
        send("All gas lines have a valid company ID")

    send("")
    print_module_end()
except Exception as e:
    print_formatted_error(e)

### END OF SCRIPT
print "--- ALL MODULES COMPLETED ---"
# Wait for user input to allow for review of console messages (able to see results of
# script without having to open the report)
raw_input('(Press enter to save report and finish up)')
