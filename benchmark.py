# TODO:
# - Round long numbers to two decimals
# - Investigate how to interpret time
# - SVG plot
# - Possibility to run other images

import sys
import multiprocessing
import subprocess
import json

class Results:
    def __init__(self):
        self.results = {
            'lbp': [],
            'multi-lbp': [],
            'multi-split-lbp': []
        }

    def get(self):
        return self.results

    def append(self, category, cores, output):
        result = self._parse(output, cores)
        self.results[category].append(result)

    def _parse(self, output, cores):
        result = {
            'cores': cores,
            'time': 0,
            'memory': 0
        }
        while True:
            line = output.readline()
            if line == "":
                break
            if line.find('User time (seconds)') != -1:
                result['time'] += float(line.split(':')[1])
            if line.find('System time (seconds)') != -1:
                result['time'] += float(line.split(':')[1])
            if line.find('Maximum resident set size (kbytes)') != -1:
                # Measured in kB, but we want MB
                result['memory'] += (int(line.split(':')[1]) / 4) / 1000

        return result

def run(algorithm, cores, results):
    process = subprocess.Popen(['/usr/bin/time', '-v', 'python2', 'main.py', 'images/1.jpeg', algorithm, str(cores)], stderr=subprocess.PIPE)
    results.append(algorithm, cores, process.stderr)

def main(argv):
    results = Results()
    
    cpu_count = multiprocessing.cpu_count()
    for cores in range(1, cpu_count + 1):
        # LBP
        if cores == 1:
            print("Benchmarking LBP...")
            run("lbp", cores, results)

        # Multiprocessing LBP
        print("Benchmarking multiprocessing LBP with {} cores...".format(cores))
        run("multi-lbp", cores, results)

        # Multiprocessing LBP
        print("Benchmarking multiprocessing split LBP with {} cores...".format(cores))
        run("multi-split-lbp", cores, results)

    print("Writing results to benchmark_data.json...")
    with open('benchmark_data.json', 'w') as output:
        json.dump(results.get(), output, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    main(sys.argv[1:])
