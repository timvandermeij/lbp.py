import sys
import os.path
import argparse
from algorithms import *

def main(argv):
    # Argument parsing
    parser = argparse.ArgumentParser(description='Run the local binary patterns algorithm using either a single process or multiple processes.')
    parser.add_argument('--input', dest='input', type=str, default='input.png', help='file name of the input image')
    parser.add_argument('--algorithm', dest='algorithm', type=str, default='lbp', help='algorithm to use: "lbp", "multi-lbp" or "multi-split-lbp"')
    parser.add_argument('--processes', dest='processes', type=int, default=1, help='number of processes to use (only relevant for multiprocessing)')
    arguments = parser.parse_args()

    algorithms = {
        "lbp": LBP.LBP,
        "multi-lbp": Multiprocessing_LBP.Multiprocessing_LBP,
        "multi-split-lbp": Multiprocessing_Split_LBP.Multiprocessing_Split_LBP
    }
    if arguments.algorithm not in algorithms:
        print("Invalid algorithm '{}'".format(arguments.algorithm))
        return

    algorithm_class = algorithms[arguments.algorithm]

    if os.path.isfile(arguments.input):
        run = algorithm_class(arguments.input, arguments.processes)
        run.execute()
    else:
        print("File '{}' does not exist.".format(arguments.input))

if __name__ == "__main__":
    main(sys.argv[1:])
