
#Convert OSM to Cube network
#Based off of SFCTA and DVRPC code
#Requires 64 bit Python
#Ben Stabler, stabler@pbworld.com, 04/04/13

#Download SF area OSM file
#1) Go to http://metro.teczno.com
#2) Download sf-bay-area bzipped file OSM file

#"C:\Python26\P64\python.exe" osm_mtc.py

from xml.etree.ElementTree import ElementTree
import os

class Network():
    
    def __init__(self, OSM_INPUT_FILE):
        self.writeType = ["highway","railway","parking", "pedestrian", "bicycle"]
        tree = ElementTree()
        tree.parse(OSM_INPUT_FILE)
        self.old2newNodes={}
        self.nextNewNode = 1
        self.nodes = []
        for n in tree.findall("node"):
            node = Node(n)
            if self.old2newNodes.has_key(node.id):
                pass
            else:
                self.old2newNodes[node.id]=str(self.nextNewNode)
                self.nextNewNode += 1
            self.nodes.append(node)
        self.ways = []
        for w in tree.findall("way"):
            way = Way(w)
            self.ways.append(way)
        
            
    def asCube(self, CUBE_OUTPUT_FILE_NODE, CUBE_OUTPUT_FILE_LINK, sep = ","):
        f_link = open(CUBE_OUTPUT_FILE_LINK, "w")
        f_link.write(sep.join(["A", "B", "Type", "ID", "HighwayT", "RailwayT", "BikewayT", "CyclewayT", "PedestrianT","ParkingT\n"]) )
        for w in self.ways:             
            if w.type in self.writeType:
                f_link.write(w.asCube(sep, self.old2newNodes))
        f_link.close()
        print "Finished writing nodes to: ",CUBE_OUTPUT_FILE_NODE
        
        f_node = open(CUBE_OUTPUT_FILE_NODE, "w")
        f_node.write(sep.join(["N","X","Y","Type","ID\n"]) )
        for n in self.nodes:             
            f_node.write(n.asCube(sep, self.old2newNodes))
        f_node.close()
        print "Finished writing links to: ",CUBE_OUTPUT_FILE_LINK
        
        
class Node():
    def __init__(self, nTree):
        for att, val in nTree.attrib.iteritems():
            self.__dict__[att] = val
            self.type= None
    
    def asCube(self,sep, old2newNodes):
        if old2newNodes.has_key(self.id):
          strep = "%s%s %14.4f%s %14.4f\n" % (old2newNodes[self.id], sep, float(self.lon), sep, float(self.lat))
          return strep
        else:
          print "key missing %s" % (self.id)
          return ''
    
class Way():
    def __init__(self, wTree):
        for att, val in wTree.attrib.iteritems():
            self.__dict__[att] = val
        self.tags      = {}
        self.waypoints = []
        self.links     = []
        self.type      = None
        
        for tag in wTree.getiterator("tag"):
            self.tags[tag.attrib["k"]] = tag.attrib["v"]
        
        for wp in wTree.getiterator("nd"):
            self.waypoints.append(wp.attrib["ref"])
        
        self.highway = ''
        self.bicycle = ''
        self.cycleway = ''
        self.building = ''
        self.railway = ''
        self.pedestrian = ''
        self.parking = ''
        
        if self.tags.has_key("highway"):
            self.highway = self.tags["highway"] 
            self.type = "highway"
        
        if self.tags.has_key("bicycle"):
            self.bicycle = self.tags["bicycle"] 
            self.type = "bicycle"
        
        if self.tags.has_key("cycleway"):
            self.cycleway = self.tags["cycleway"] 
            self.type = "bicycle"
        
        if self.tags.has_key("railway"):
            self.railway = self.tags["railway"] 
            self.Type = "railway"
        
        if self.tags.has_key("building"):
            self.building = self.tags["building"]
            self.type = "building"
        
        if self.tags.has_key("amenity"):
            if self.tags["amenity"] == "parking":
                if self.tags.has_key("parking"):
                    self.parking = self.tags["parking"]
                else:
                    self.parking = "yes"
                self.type = "parking"
                
        self.area = False
        if self.tags.has_key("area"):
            self.area = True
        
        self.oneway = False
        if self.tags.has_key("oneway"):
            if self.tags["oneway"] == "yes":
                self.oneway = True
        
        self.name = ""
        if self.tags.has_key("name"):
            self.name = self.tags["name"]
            
        # create links
        previousWP = ''
        for wp in self.waypoints:
            if previousWP:
                link = Link(previousWP, wp, self.type, self.name, self.id)
                self.links.append(link)
                if self.oneway == False:
                    link = Link(wp, previousWP, self.type, self.name, self.id)
                self.links.append(link)
            previousWP = wp
        
       
    def asCube(self, sep, old2newNodes):
        LastNode = 0
        ThisNode = 0
        strep=''
        for l in self.links:
            strep = strep + l.asCube(sep, old2newNodes,self.highway, self.railway, self.bicycle, self.cycleway, self.pedestrian, self.parking)
        return strep

class Link():
    def __init__(self, fromNode, toNode, type, name, id):
        self.a = fromNode
        self.b = toNode
        self.type = type
        self.name = name
        self.id   = id

    def asCube(self, sep, old2newNodes, highwayT, railwayT, bikingT, cyclewayT, pedestrianT, parkingT):
    
        if old2newNodes.has_key(self.a) and old2newNodes.has_key(self.b):
          strep = sep.join([old2newNodes[self.a], old2newNodes[self.b], self.type, self.id, highwayT, railwayT, bikingT, cyclewayT, pedestrianT, parkingT]) + "\n"
          return strep
        else:
          print "key missing %s or %s" % (self.a, self.b)
          return ''

if __name__ == "__main__":

    OSM_INPUT_FILE = "sf-bay-area.osm"
    #OSM_INPUT_FILE = "bierman_park.osm"
    cube_out_node = "cube_node.csv"
    cube_out_link = "cube_link.csv"
    
    osm_network = Network(OSM_INPUT_FILE)
    osm_network.asCube(cube_out_node, cube_out_link)
