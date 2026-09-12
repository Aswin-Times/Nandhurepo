"""Read-only compact before/after report for a full dataset experiment."""
import json
import sys
from evaluate_submission import read,blast_radius
if __name__=='__main__':
    result=blast_radius(read(sys.argv[1]),read(sys.argv[2]))
    print(json.dumps({k:v for k,v in result.items() if k!='details'},indent=2))
