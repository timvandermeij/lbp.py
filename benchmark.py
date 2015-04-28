import sys
import multiprocessing
import subprocess
import json
import numpy as np
import matplotlib.pyplot as plt

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
            'real_time': 0,
            'user_sys_time': 0,
            'memory': 0
        }
        line = output.readline()
        measurements = line.split('-')
        result['real_time'] = float(measurements[0])
        result['user_sys_time'] = float(measurements[1]) + float(measurements[2])
        result['memory'] += (int(measurements[3]) / 4) / 1000 # Convert kB to MB
        return result

class Plot:
    def __init__(self, results):
        self.results = results
        self.bar_width = 0.5

    def _preprocess(self, runs):
        # Preprocess the data for usage with Matplotlib
        real_time = ()
        memory = ()
        for item in runs:
            real_time += (item['real_time'],)
            memory += (item['memory'],)

        return (real_time, memory)

    def create(self):
        for algorithm, runs in self.results.iteritems():
            # Determine the number of groups and create the initial plot
            x_groups = np.arange(len(runs))
            fig, ax = plt.subplots()

            # Create two bars per run
            real_time, memory = self._preprocess(runs)
            ax.bar(x_groups - 0.2, real_time, self.bar_width - 0.1, color='b', alpha=0.5, align='center', label='Real time (seconds)')
            ax.bar(x_groups + 0.2, memory, self.bar_width - 0.1, color='r', alpha=0.5, align='center', label='Peak memory consumption (MB)')

            # Set the plot labels and ticks
            ax.set_xlabel('Processes')
            ax.set_ylabel('Consumption')
            ax.set_title(algorithm)
            ax.set_xticks(x_groups + (self.bar_width / 2.0) - 0.25)
            ax.set_xticklabels(range(1, multiprocessing.cpu_count() + 1))

            # Add a legend
            ax.legend(loc=1, prop={'size':6})

            # Add a grid and save the plot as an EPS file
            plt.grid(True)
            plt.savefig("benchmark_plot_{}.eps".format(algorithm))

def run(algorithm, cores, results):
    process = subprocess.Popen(['/usr/bin/time', '-f', '%e-%S-%U-%M', sys.executable, 'main.py', 'images/1.jpeg', algorithm, str(cores)], stderr=subprocess.PIPE)
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

    print("Writing results JSON...")
    with open('benchmark_results.json', 'w') as output:
        json.dump(results.get(), output, indent=4, separators=(',', ': '))

    print("Writing plot SVGs...")
    plot = Plot(results.get())
    plot.create()

if __name__ == "__main__":
    main(sys.argv[1:])
