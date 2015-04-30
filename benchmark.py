import sys
import multiprocessing
import subprocess
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
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

    def _create(self, data, algorithm, runs, label, file_name):
        # Create the initial plot
        x_groups = np.arange(len(runs))
        fig, ax = plt.subplots()

        # Add the bars
        ax.bar(x_groups, data, self.bar_width, color='b', alpha=0.5, align='center')

        # Set the labels and ticks
        ax.set_xlabel('Number of processes')
        ax.set_ylabel(label)
        ax.set_title(algorithm)
        ax.set_xticks(x_groups)
        ax.set_xticklabels(range(1, multiprocessing.cpu_count() + 1))
        
        # Add a grid and save the plot
        plt.grid(True)
        plt.savefig(file_name)

    def output(self):
        for algorithm, runs in self.results.iteritems():
            real_time, memory = self._preprocess(runs)
            self._create(real_time, algorithm, runs, 'Real time (seconds)', 'benchmark_plot_{}_real_time.eps'.format(algorithm))
            self._create(memory, algorithm, runs, 'Peak memory usage (MB)', 'benchmark_plot_{}_memory.eps'.format(algorithm))

def run(algorithm, cores, results):
    process = subprocess.Popen(
        [
            '/usr/bin/time',
            '-f', '%e-%S-%U-%M',
            sys.executable, 'main.py', '--input', 'images/1.jpeg', '--algorithm', algorithm, '--processes', str(cores)
        ],
        stderr=subprocess.PIPE
    )
    results.append(algorithm, cores, process.stderr)

def main():
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
    plot.output()

if __name__ == "__main__":
    main()
