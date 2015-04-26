import sys
import os.path
from algorithms import *

def main(argv):
    filename = argv[0] if len(argv) > 0 else "input.png"
    algorithm = argv[1] if len(argv) > 1 else "lbp"
    num_processes = int(argv[2]) if len(argv) > 2 else 1

    algorithms = {
        "lbp": LBP.LBP,
        "multi-lbp": Multiprocessing_LBP.Multiprocessing_LBP,
        "multi-split-lbp": Multiprocessing_Split_LBP.Multiprocessing_Split_LBP
    }
    if algorithm not in algorithms:
        print("Invalid algorithm '{}'".format(algorithm))
        return

    algorithm_class = algorithms[algorithm]

    if os.path.isfile(filename):
        run = algorithm_class(filename, num_processes)
        run.execute()
    else:
        print("File '{}' does not exist.".format(filename))

if __name__ == "__main__":
    main(sys.argv[1:])
