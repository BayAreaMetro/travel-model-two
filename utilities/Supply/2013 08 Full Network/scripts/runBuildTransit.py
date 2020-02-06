import PublicTransit

def main():
    s = PublicTransit.PublicTransit()
    s.buildNodesDict()
    s.buildLinksDict()
    s.buildRoutesDict()
    s.buildStopsDict()
    s.buildRouteLinkSequence()
    s.writeRouteSequence()
    s.saveData()
    #s.loadData()
    s.writeRouteSequence()
    s.analyzeStops()
    #s.writeNetwork("nodes.csv","links.csv")
    s.buildTaps()

main()
#if __name__ == 'main':
#    main()