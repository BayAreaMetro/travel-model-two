import datetime,os,pandas,sys
import partridge
import Wrangler

USAGE = """

Script to write vehicle type (transit capacity) information from an excel file to the transit line file

"""

USERNAME     = os.environ["USERNAME"]
LOG_FILENAME = "modify_transit_capacity.log"
TM2_INPUTS   = os.path.join(r"C:\\Users", USERNAME, "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs")
TRN_NETFILE  = os.path.join(TM2_INPUTS,"2015","trn","transit_lines")

# read the PT transit network line file
trn_net = Wrangler.TransitNetwork(champVersion=4.3, basenetworkpath=TRN_NETFILE, isTiered=True, networkName="transitLines")


# read the excel file with vehicle type information
VehicleType_df = pandas.read_excel(r"M:\\Development\\Travel Model Two\\Supply\\Transit\\Network_QA\\Line and vehicle type_be.xlsx", sheet_name='transit_input_summary')


for line in trn_net:
    for i in VehicleType_df.index:

        line_name_excel = str(VehicleType_df['Line_name'][i])
        line_name_linefile = str(line.name)

        print("Processing:", i, "Line name excel ", line_name_excel, "Line name in line file ", line_name_linefile)

        if line_name_linefile == line_name_excel:

	    # if the vehicle type is blank, then assume it is a standard bus
            if  str(VehicleType_df['Vehicle Type'][i]) =="nan":

                line['VEHICLETYPE'] = 1

            else:

                line['VEHICLETYPE'] = int(VehicleType_df['Vehicle Type'][i])

        
            print("Changed:",i, "Line name excel-", line.name, "Line name in line file-", VehicleType_df['Line_name'][i], "Vehicle type-", line['VEHICLETYPE'])
            break


        else:

            continue


trn_net.write(path=".", name="transitLines", writeEmptyFiles=False, suppressValidation=True)
