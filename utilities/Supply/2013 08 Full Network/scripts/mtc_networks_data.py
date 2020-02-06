'''
Create TeleAtlas node and link shapefiles for import into Cube
Created on Jun 27, 2012
@author: moonj, bts
'''
import arcpy
import os
import sys

#parameters
LINKS_INTERSECT_FEATURE_CLASS = 'ca_nw_Intersect'   # intersect of ca_nw and ABAG_blockgroups_Dissolve
LINKS_INTERSECT_FEATURE_CLASS_TEMP = 'ca_nw_Intersect_Temp'

LINKS_FEATURE_CLASS = 'ca_nw'
NODES_FEATURE_CLASS = 'ca_jc'
NODES_RELEVANT_FEATURE_CLASS = 'ca_jc_relevant'     # nodes of ca_nw_Intersect

ABAG_BLOCKGROUPS_DISSOLVE = '/projects/MTC/networks/networks data/abag.gdb/ABAG_blockgroups_Dissolve'
INTERSECT_PATH = '/projects/MTC/networks/networks data/Intersect.gdb/'
SHAPEFILE_DIR = '/projects/MTC/networks/networks data/shapefiles/'
GDB_PATH = '/projects/MTC/networks/networks data/ca_tana2011.gdb/' #master TeleAtlas network
TELEATLAS_NODE_OFFSET = 3000000


#convert TeleAtlas 14 digit ID to 7 digit ID for Cube
RECODE_ID_FUNC = """def recodeID(id):
  #prefix codes
  prefix_recode = dict()
  prefix_recode["7840020"] = ''
  
  #prefix recode
  prefix = prefix_recode[str(id)[0:7]]
  
  #suffix recode
  suffix = int(str(id)[7:14])
 
  return(int(prefix + str(suffix)) + TELEATLAS_NODE_OFFSET)"""

# Re-code function for the link direction field (oneway) so that the Cube network build script correctly
# sets direction.
ONEWAY_RECODE_FUNCTION = """def onewayRecode(id):
  # treat BLANK and N as open in both directions (default)
  rec = 2
  if (id == 'FT'):
    rec = 1
  elif (id == 'TF'):
    rec = -1
  return(rec)"""

def main():
    print 'In main...'
    
    # intersect links with ABAG_blockgroups_Dissolve
    arcpy.env.workspace = INTERSECT_PATH
    if arcpy.Exists(INTERSECT_PATH + LINKS_INTERSECT_FEATURE_CLASS_TEMP):
        arcpy.Delete_management(LINKS_INTERSECT_FEATURE_CLASS_TEMP)
    arcpy.Intersect_analysis([GDB_PATH + LINKS_FEATURE_CLASS, ABAG_BLOCKGROUPS_DISSOLVE], LINKS_INTERSECT_FEATURE_CLASS_TEMP)
    
    #remove bad ID links at boundary and those outside the nine counties
    if arcpy.Exists(INTERSECT_PATH + LINKS_INTERSECT_FEATURE_CLASS):
        arcpy.Delete_management(LINKS_INTERSECT_FEATURE_CLASS)
    arcpy.MakeFeatureLayer_management(LINKS_INTERSECT_FEATURE_CLASS_TEMP, "layer")
    arcpy.SelectLayerByAttribute_management("layer", "NEW_SELECTION", "F_JNCTID < 79999999999999 AND T_JNCTID < 79999999999999")
    arcpy.CopyFeatures_management("layer", INTERSECT_PATH + LINKS_INTERSECT_FEATURE_CLASS)

    # get nodes for intersect link set
    arcpy.env.workspace = INTERSECT_PATH
    CreateNodesDictionary()
    arcpy.env.workspace = INTERSECT_PATH
    GetRelevantNodes()

    #create new IDs
    NewIDs()

    # write shapefiles
    if not os.path.exists(SHAPEFILE_DIR):
        os.mkdir(SHAPEFILE_DIR)
    arcpy.env.workspace = INTERSECT_PATH
    WriteIntersectsToShape()

def GetRelevantNodes():
    print 'Getting relevant nodes...'

    if arcpy.Exists(NODES_RELEVANT_FEATURE_CLASS):
        arcpy.Delete_management(NODES_RELEVANT_FEATURE_CLASS)
    arcpy.CreateFeatureclass_management(INTERSECT_PATH, NODES_RELEVANT_FEATURE_CLASS, 'POINT', GDB_PATH + NODES_FEATURE_CLASS, "DISABLED", "DISABLED", GDB_PATH + NODES_FEATURE_CLASS)

    # add required fields
    arcpy.AddField_management(NODES_RELEVANT_FEATURE_CLASS, 'ID', 'Double')
    arcpy.AddField_management(NODES_RELEVANT_FEATURE_CLASS, 'FEATTYP', 'Short')
    arcpy.AddField_management(NODES_RELEVANT_FEATURE_CLASS, 'JNCTTYP', 'Short')
    arcpy.AddField_management(NODES_RELEVANT_FEATURE_CLASS, 'ELEV', 'Short')
    arcpy.AddField_management(NODES_RELEVANT_FEATURE_CLASS, 'ID_hash', 'Long')

    # create insert cursor
    relevantNodes = arcpy.InsertCursor(NODES_RELEVANT_FEATURE_CLASS)
    # create search cursor
    nodes = arcpy.SearchCursor(GDB_PATH + NODES_FEATURE_CLASS)

    # loop through the nodes
    for row in nodes:
        # if node in dictionary
        if row.getValue('ID') in nodesDict:
            # save it to the relevant nodes feature class
            relevantNodes.insertRow(row)
    del row
    del nodes
    print 'Got relevant nodes...'

def CreateNodesDictionary():
    print 'Creating nodes dictionary...'

    global nodesDict

    nodesDict = dict()
    nodeCount = 0

    # loop through intersected links
    linksIntersectTable = arcpy.SearchCursor(LINKS_INTERSECT_FEATURE_CLASS)
    for row in linksIntersectTable:
        fieldname = 'F_JNCTID'
        #print 'F_JNCTID: %(fieldname)s' % {'fieldname':row.getValue(fieldname)}
        nodeID = row.getValue(fieldname)
        if not nodeID in nodesDict:
            nodesDict.update({nodeID:nodeCount})
            nodeCount += 1

        fieldname = 'T_JNCTID'
        #print 'T_JNCTID: %(fieldname)s' % {'fieldname':row.getValue(fieldname)}
        #print ''
        nodeID = row.getValue(fieldname)
        if not nodeID in nodesDict:
            nodesDict.update({nodeID:nodeCount})
            nodeCount += 1

def FieldExists(featureclass, fieldname):
        fieldList = arcpy.ListFields(featureclass, fieldname)
        fieldCount = len(fieldList)

        if (fieldCount == 1):
            return True
        else:
            return False

def NewIDs():
    print 'Calculating new IDs...'

    #============= NODES ==================
    # add field ID_hash
    nodesFC = arcpy.ListFeatureClasses(NODES_RELEVANT_FEATURE_CLASS,'')[0]
    if FieldExists(nodesFC, "ID_hash"):
        arcpy.DeleteField_management(nodesFC, "ID_hash")
    arcpy.AddField_management(nodesFC, "ID_hash", "LONG", "", "", "20")
    
    # hash ID
    arcpy.CalculateField_management(nodesFC, "ID_hash", 'recodeID(!ID!)', "PYTHON", RECODE_ID_FUNC)

    #============= LINKS ==================
    linksFC = arcpy.ListFeatureClasses(LINKS_INTERSECT_FEATURE_CLASS,'')[0]
    
    # add field F_JNCTID_hash
    if FieldExists(linksFC, "F_JNCTID_h"):
        arcpy.DeleteField_management(linksFC, "F_JNCTID_h")
    arcpy.AddField_management(linksFC, "F_JNCTID_h", "LONG", "", "", "20")
    
    # hash F_JNCTID
    arcpy.CalculateField_management(linksFC, "F_JNCTID_h", 'recodeID(!F_JNCTID!)', "PYTHON", RECODE_ID_FUNC)

    # add field T_JNCTID_hash
    if FieldExists(linksFC, "T_JNCTID_h"):
        arcpy.DeleteField_management(linksFC, "T_JNCTID_h")
    arcpy.AddField_management(linksFC, "T_JNCTID_h", "LONG", "", "", "20")
    
    # hash T_JNCTID
    arcpy.CalculateField_management(linksFC, "T_JNCTID_h", 'recodeID(!T_JNCTID!)', "PYTHON", RECODE_ID_FUNC)

def WriteIntersectsToShape():
    print 'Writing shapefiles...'
    nodesFC = arcpy.ListFeatureClasses(NODES_RELEVANT_FEATURE_CLASS,'')[0]
    linksFC = arcpy.ListFeatureClasses(LINKS_INTERSECT_FEATURE_CLASS,'')[0]
    
    nodesFCsp = nodesFC + "_sp"
    linksFCsp = linksFC + "_sp"
    
    # if the shapefiles already exist, delete them
    nodesShapefile = SHAPEFILE_DIR + nodesFCsp + '.shp'
    linksShapefile = SHAPEFILE_DIR + linksFCsp + '.shp'
    if os.path.exists(nodesShapefile):
        arcpy.Delete_management(nodesShapefile)
    if os.path.exists(linksShapefile):
        arcpy.Delete_management(linksShapefile)
    install_dir = arcpy.GetInstallInfo()['InstallDir']
    out_coordinate_system = os.path.join(install_dir, )
    
    # if the state plane feature classes exist, delete them
    if arcpy.Exists(INTERSECT_PATH + nodesFCsp):
        arcpy.Delete_management(INTERSECT_PATH + nodesFCsp)
    if arcpy.Exists(INTERSECT_PATH + linksFCsp):
        arcpy.Delete_management(INTERSECT_PATH + linksFCsp)

    #############################################################################
    # Add additional fields to linksFc before re-projecting and copying to SHP
    #
    #############################################################################
     # add FEET field and assign based on meters
    arcpy.AddField_management(linksFC, "FEET", "DOUBLE")
    arcpy.CalculateField_management(linksFC, "FEET", "!METERS! * (1.0 / 2.54) * (25.0 / 3.0)", "PYTHON")    
    
    arcpy.AddField_management(linksFC, "oneway_recode", "SHORT")
    arcpy.CalculateField_management(linksFC, "oneway_recode", "onewayRecode(!ONEWAY!)", "PYTHON", ONEWAY_RECODE_FUNCTION)
    
    # add ASSIGNABLE field and assign based on whether TeleAtlas FRC (functional road class)
    # "local roads" and "local roads of minor importance" are not assignable
    # Also, links that are closed in both directions are not assignable.
    arcpy.AddField_management(linksFC, "ASSIGNABLE", "SHORT")
    arcpy.CalculateField_management(linksFC, "ASSIGNABLE", "int(!FRC! not in [7] or !ONEWAY! <> 'N')", "PYTHON")
    
    # project nodesFC and linksFC to CA NAD 83 State Plane
    arcpy.Project_management(nodesFC, nodesFCsp, out_coordinate_system, "NAD_1983_To_WGS_1984_1")
    arcpy.Project_management(linksFC, linksFCsp, out_coordinate_system, "NAD_1983_To_WGS_1984_1")
    
    # Create shapefiles for nodes and links
    arcpy.CopyFeatures_management(nodesFCsp, SHAPEFILE_DIR + nodesFCsp)
    arcpy.CopyFeatures_management(linksFCsp, SHAPEFILE_DIR + linksFCsp)


if __name__ == '__main__':
    #pass
    main()

