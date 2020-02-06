'''
Python Script to build a Cube Voyager block script that determines
whether the transit assignment will be run with or without crowding during assignment.

If the program cannot find the key/value pairs in the properties file, the
program will generate a code block with crowding disabled.

Input:

(1): Properties File
(2): Output location for the Cube Voyager Block

Ex. Usage:
transit_assign_set_type.py CTRAMP\runtime\mtctm2.properties CTRAMP\scripts\block\transit_assign_type.block
'''

import ConfigParser
import os
import StringIO
import sys

properties_file = sys.argv[1]
output_file = sys.argv[2]

#Set defaults in case values are not in properties file.
config = ConfigParser.RawConfigParser(defaults= {
    'transit.crowding': 'False',
    'transit.crowding.adjustlink': 'True',
    'transit.crowding.adjustwait': 'False',
    'transit.crowding.advance_support': 'False',
    'transit.crowding.convergence': 0.0001,
    'transit.crowding.linkdf': 0.4,
    'transit.crowding.voldf': 0.4,
    'transit.crowding.waitdf': 0.4,
	'transit.crowding.iterations': 3,
})

# This is a patch (workaround), so Python can read a straight Java properties file.
configIO = StringIO.StringIO()
configIO.write('[defaults]\n')
configIO.write(open(properties_file).read())
configIO.seek(0, os.SEEK_SET)

config.readfp(configIO)

crowding_config = {}

# Read in values
crowding_config['enabled'] = config.getboolean('defaults','transit.crowding')
crowding_config['adjustlink'] = config.getboolean('defaults','transit.crowding.adjustlink')
crowding_config['adjustwait'] = config.getboolean('defaults','transit.crowding.adjustwait')

crowding_config['advanced'] = config.getboolean('defaults','transit.crowding.advance_support')
crowding_config['converge'] = config.getfloat('defaults', 'transit.crowding.convergence')
crowding_config['linkdf'] = config.getfloat('defaults', 'transit.crowding.linkdf')
crowding_config['voldf'] = config.getfloat('defaults', 'transit.crowding.voldf')
crowding_config['waitdf'] = config.getfloat('defaults', 'transit.crowding.waitdf')
crowding_config['iterations'] = config.getint('defaults','transit.crowding.iterations')


crowding_line = 'CROWDMODEL APPLY=T, ADJUSTLINK={}, ADJUSTWAIT={}, ITERATIONS={}, PERIOD=@PERIOD_DURATION@, RDIFF=T, RMSE=T, STOP2STOP=T, SKIMS=F'.format(
        'T' if crowding_config['adjustlink'] else 'F',
        'T' if crowding_config['adjustwait'] else 'F',
		crowding_config['iterations']
)
crowd_convergence = '    LINKDF={linkdf:.5f}, VOLDF={voldf:.5f}, WAITDF={waitdf:.5f}, RMSESTOP=T, RMSECUTOFF={converge:.10f}'.format(**crowding_config)

with open(output_file, 'w') as f:
    if crowding_config['enabled']:
        f.write(crowding_line)
        if crowding_config['advanced']:
            f.write(',\n' + crowd_convergence + '\n')
        else:
		    f.write('\n')
