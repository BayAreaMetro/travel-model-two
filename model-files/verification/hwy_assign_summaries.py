import os,sys

period_token = '@@PERIOD@@'
infile = r'assignet' + period_token + '.csv'
periods = ['EA','AM','MD','PM','EV']
outfile = r'hwy_assign_summary.csv'

zero_counts = {}
vmt = {}
for period in periods:
    zero_counts[period] = {}
    vmt[period] = {}
    with open(infile.replace(period_token,period)) as f:
        for line in f:
            #A,B,CNTYPE,FT,FEET,V_1
            line = line.strip().split(',')
            a = int(line[0])
            b = int(line[1])
            if a >= 1000000:
                c = a
            elif b >= 1000000:
                c = b
            else:
                print 'oops'
                continue
            if c < 1500000:
                county = 'San Francisco'
            elif c < 2000000:
                county = 'San Mateo'
            elif c < 2500000:
                county = 'Santa Clara'
            elif c < 3000000:
                county = 'Alameda'
            elif c < 3500000:
                county = 'Contra Costa'
            elif c < 4000000:
                county = 'Solano'
            elif c < 4500000:
                county = 'Napa'
            elif c < 5000000:
                county = 'Sonoma'
            elif c < 5500000:
                county = 'Marin'
            elif c < 6000000:
                county = 'San Francisco'
            elif c < 6500000:
                county = 'San Mateo'
            elif c < 7000000:
                county = 'Santa Clara'
            elif c < 7500000:
                county = 'Alameda'
            elif c < 8000000:
                county = 'Contra Costa'
            elif c < 8500000:
                county = 'Solano'
            elif c < 9000000:
                county = 'Napa'
            elif c < 9500000:
                county = 'Sonoma'
            elif c < 10000000:
                county = 'Marin'
            else:
                print 'double oops'
                continue
            ft = int(line[3])
            miles = float(line[4]) / 5280
            vol = float(line[5])
            
            if not county in zero_counts[period]:
                zero_counts[period][county] = {}
            if not ft in zero_counts[period][county]:
                zero_counts[period][county][ft] = [0,0]
            if vol == 0:
                zero_counts[period][county][ft][0] += 1
            zero_counts[period][county][ft][1] += 1
            
            if not county in vmt[period]:
                vmt[period][county] = 0
            vmt[period][county] += vol * miles
            

with open(outfile,'wb') as f:
    f.write('period,county,ft,zero_count,total_count' + os.linesep)
    for period in periods:
        counties = zero_counts[period].keys()
        counties.sort()
        for county in counties:
            fts = zero_counts[period][county].keys()
            fts.sort()
            for ft in fts:
                f.write(','.join(map(str,[period,county,ft,zero_counts[period][county][ft][0],zero_counts[period][county][ft][1]])) + os.linesep)
    f.write(os.linesep)
    f.write('period,county,vmt' + os.linesep)
    for period in periods:
        counties = vmt[period].keys()
        counties.sort()
        for county in counties:
            f.write(','.join(map(str,[period,county,vmt[period][county]])) + os.linesep)
