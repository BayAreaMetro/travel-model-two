import os,sys

infile = r'..\logs\TPPL1096.PRN'
line_file = r'..\trn\mtc_transit_lines_AM_LOCAL_BUS_with_transit.lin'
outfile = r'transit_summary.csv'

headways = {}
with open(line_file) as f:
    inside = False
    name = None
    for line in f:
        line = line.strip()
        if len(line) == 0:
            continue
        line = line.split()
        if line[0] == 'LINE':
            inside = True
        if inside:
            for entry in line:
                if entry.find('NAME=') == 0:
                    name = entry.split('=')[1].replace('"','')
                    headways[name] = ['0','0','0','0','0','0']
                if entry.find('HEADWAY') == 0:
                    ent = 1
                    if entry.find('HEADWAY[') == 0:
                        ent = int(entry[8])
                    headways[name][ent] = entry.split('=')[1]
                if entry.find('N=') == 0:
                    inside = False
                    name = None

counter = 0
with open(outfile,'wb') as of:
    of.write(','.join(['Name','Mode','Op','Stp','Cr','Distance','Time','Pass','PassDist','PassHr','GenMode','TrueGenMode','TimePeriod','Headway']) + os.linesep)
    with open(infile) as f:
        ind = -1
        last_mode = None
        for line in f:
            line = line.strip()
            if (ind == -1) and (line.find('REPORT LINES ') == 0):
                ind = 1
                mode = line.replace('REPORT LINES  UserClass=','')
                if mode != last_mode:
                    counter += 1
                last_mode = mode
            elif (ind == 1) and (line[0] == '-'):
                ind = 2
            elif (ind == 2):
                if line.find('-') == 0:
                    ind = -1
                    continue
                if line.find('Page ') > -1:
                    line = line.split('Page ')[0]
                    ind = -1
                line = line.replace(',','').replace('--','-').replace('-','0').split()
                tp = 0
                if counter % 4 == 0:
                    tp = counter / 4
                    tgm = 'PREMIUM'
                elif counter % 2 == 0:
                    tp = (counter + 2) / 4
                    tgm = 'LOCAL'
                else:
                    tp = 0
                    tgm = 'NA'
                if tp == 0:
                    tpn = 'NA'
                    tp = 1
                elif tp == 1:
                    tpn = 'EA'
                elif tp == 2:
                    tpn = 'AM'
                elif tp == 3:
                    tpn = 'MD'
                elif tp == 4:
                    tpn = 'PM'
                elif tp == 5:
                    tpn = 'EV'
                of.write(','.join(line + [mode,tgm,tpn,headways[line[0]][tp]]) + os.linesep)
