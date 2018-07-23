import datetime,os,pandas,sys
import partridge
import Wrangler

USAGE = """

Script to check if transit lines go through maz/taz centroids

"""

USERNAME     = os.environ["USERNAME"]
LOG_FILENAME = "addLinkTime_info.log"
TM2_INPUTS   = os.path.join(r"C:\\Users", USERNAME, "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs")
TRN_NETFILE  = os.path.join(TM2_INPUTS,"2015","trn","transit_lines")

# read the PT transit network line file
trn_net = Wrangler.TransitNetwork(champVersion=4.3, basenetworkpath=TRN_NETFILE, isTiered=True, networkName="transitLines")

# output a csv file
fileObj = open("check_for_maztaz_centroids.csv", "w")
fileObj.write("Operator, Line_name, Node_number, Maz/taz centroids" + "\n")

count_badnode = 0

for line in trn_net:
    for node_idx in range(len(line.n)):

        badnode = 0

        # Centroid numbering convention: http://bayareametro.github.io/travel-model-two/input/#county-node-numbering-system
        # node_number = abs(int(line.n[node_idx].num))

        # San Francisco
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 1 and abs(int(line.n[node_idx].num)) <= 9999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 10001 and abs(int(line.n[node_idx].num)) <= 89999:
            badnode = 1

        # San Mateo
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 100001 and abs(int(line.n[node_idx].num)) <= 109999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 110001 and abs(int(line.n[node_idx].num)) <= 189999:
            badnode = 1

        # Santa Clara
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 200001 and abs(int(line.n[node_idx].num)) <= 209999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 210001 and abs(int(line.n[node_idx].num)) <= 289999:
            badnode = 1

        # Alameda
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 300001 and abs(int(line.n[node_idx].num)) <= 309999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 310001 and abs(int(line.n[node_idx].num)) <= 389999:
            badnode = 1

        # Contra Costa
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 400001 and abs(int(line.n[node_idx].num)) <= 409999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 410001 and abs(int(line.n[node_idx].num)) <= 489999:
            badnode = 1

        # Solano
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 500001 and abs(int(line.n[node_idx].num)) <= 509999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 510001 and abs(int(line.n[node_idx].num)) <= 589999:
            badnode = 1

        # Napa
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 600001 and abs(int(line.n[node_idx].num)) <= 609999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 610001 and abs(int(line.n[node_idx].num)) <= 689999:
            badnode = 1

        # Sonoma
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 700001 and abs(int(line.n[node_idx].num)) <= 709999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 710001 and abs(int(line.n[node_idx].num)) <= 789999:
            badnode = 1

        # Marin
        # TAZs
        if abs(int(line.n[node_idx].num)) >= 800001 and abs(int(line.n[node_idx].num)) <= 809999:
            badnode = 1
        # MAZs
        if abs(int(line.n[node_idx].num)) >= 810001 and abs(int(line.n[node_idx].num)) <= 889999:
            badnode = 1

        # External
        if abs(int(line.n[node_idx].num)) >= 900001 and abs(int(line.n[node_idx].num)) <= 999999:
            badnode = 1

        count_badnode = count_badnode + badnode

        fileObj.write(line['USERA1'] + "," + line.name + ", " + line.n[node_idx].num + ", " + str(badnode) + "\n")

fileObj.close()

print "number of bad nodes: " + str(count_badnode)
print "see output file: check_for_maztaz_centroids.csv"
