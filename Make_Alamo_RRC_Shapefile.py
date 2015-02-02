# Name: Make_Alamo_RRC_Shapefile.py
# Description: Exports Alamo Pipeline lines from the Gas_Lines layer to their own shapefile. Proper attribute fields are included.
# Author: Réal R. Provencher 2011

# Import
print "Importing libraries..."
import arcpy
from arcpy import env

# Environment settings
print "Setting environment..."
gdb = "T:\Hughes_ArcGIS\HNG new.gdb"
env.workspace = gdb

# Local variables
Gas_Lines = "Gas_Lines"
AlamoRRC = "AlamoRRC"

print "Set up complete."
print

# Split Gas Lines by company
if arcpy.Exists(AlamoRRC):
	arcpy.Delete_management(AlamoRRC)
print "Splitting Gas_Lines layer by company..."
arcpy.Select_analysis(Gas_Lines,AlamoRRC,'"company"=\'AP\'')
print "-Created " + AlamoRRC + ", number of features:"
print arcpy.GetCount_management(AlamoRRC)

# Correcting the fields
print "Dropping fields..."
arcpy.DeleteField_management(AlamoRRC,"pipe_size;depth;MAOP;tracing_wire;county;neighborhood_area;install_date;comment;manufacturer;manufacture_date;lot_num;length_ft;OBJID;company;pipe_material")
print "Adding fields..."
arcpy.AddField_management(AlamoRRC,"OPER_NM","TEXT")
arcpy.AddField_management(AlamoRRC,"SYS_ID","TEXT")
arcpy.AddField_management(AlamoRRC,"DIAMETER","TEXT")
arcpy.AddField_management(AlamoRRC,"COMMODITY1","TEXT")
arcpy.AddField_management(AlamoRRC,"CMDTY_DESC","TEXT")
arcpy.AddField_management(AlamoRRC,"INTERSTATE","TEXT")
arcpy.AddField_management(AlamoRRC,"STATUS_CD","TEXT")
arcpy.AddField_management(AlamoRRC,"QUALITY_CD","TEXT")
arcpy.AddField_management(AlamoRRC,"T4PERMIT","TEXT")
arcpy.AddField_management(AlamoRRC,"SYSTYPE","TEXT")
arcpy.AddField_management(AlamoRRC,"P5_NUM","TEXT")
arcpy.AddField_management(AlamoRRC,"TX_REG","TEXT")
arcpy.AddField_management(AlamoRRC,"T4_AMD","TEXT")

# ADD REPROJECTION IF NECESSARY
# GCS: GCS_North_American_1983
# Datum: D_North_American_1983

print "Done!"
