
import sys

USAGE = "\n\tUsage: python3 utils.py [process-online] [<optional input>]\n"


# Where the DF properties begin (assumes it's DF until the end)
PROPERTIES_START_IDX = 16


def process_online(line):

    # Extract the data
    data = line.strip().split('\t')

    # Get the header of data.csv
    with open("data.csv", "r") as f:
        header = f.readline().strip().split(",")
    
    data_properties = [p[5:] for p in header[PROPERTIES_START_IDX:]]

    csv = ''

    # Slug
    csv += f'{data[1]}'

    # Name
    csv += f',{data[2]}'

    # Title
    csv += f',{data[3]}'

    # URL
    csv += f',{data[4]}'

    # Year
    csv += f',{data[5]}'

    # Issue #
    csv += f',{data[6]}'

    # Implemented
    csv += ',1' if data[7] == 'Yes' else ',0'

    # Agent Rationality
    if data[8] == "Doesn't matter":
        csv += ',0,0'
    elif data[8] == "Optimal":
        csv += ',0,1'
    else:
        csv += ',1,0'
    
    # Model determinism
    if data[9] == "Deterministic":
        csv += ',1,0,0'
    elif data[9] == "Probabilistic":
        csv += ',0,0,1'
    else:
        csv += ',0,1,0'

    # Action Parameters
    if data[10] == "None":
        csv += ',0,0'
    elif data[10] == "Untyped":
        csv += ',1,0'
    else:
        csv += ',1,1'
    
    # Predicate Parameters
    if data[11] == "None":
        csv += ',0,0'
    elif data[11] == "Untyped":
        csv += ',1,0'
    else:
        csv += ',1,1'
    
    # Trace data properities
    selected = set([p.strip() for p in data[12].split(',')])
    for p in selected:
        assert p in data_properties
    
    for p in data_properties:
        if p in selected:
            csv += ',1'
        else:
            csv += ',0'

    print(csv)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit()

    if sys.argv[1] == "process-online":
        process_online(sys.argv[2])
    