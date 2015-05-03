import time
import numpy as np
from PIL import Image
from LBP import LBP
from mpi4py import MPI

class Multiprocessing_LBP_MPI(LBP):
    def __init__(self, input, num_processes, output):
        LBP.__init__(self, input, num_processes, output)
        self.communicator = MPI.COMM_WORLD
        self.process_id = self.communicator.rank
        self.num_processes = self.communicator.size

    def execute(self):
        if self.process_id == 0:
            self._run_master()
            if self.output:
                self._output()
        else:
            pixels = np.array(self.image)
            self._run_slave(pixels)

    def _run_master(self):
        # Collect results of the slave processes
        results = []
        for process_id in range(1, self.num_processes):
            while not self.communicator.Iprobe(source=process_id, tag=MPI.ANY_TAG):
                time.sleep(1)

            results.append({
                'process_id': process_id,
                'patterns': self.communicator.recv(source=process_id, tag=MPI.ANY_TAG)
            })

        # Format the pixels correctly for the output function,
        # which expects a linear list of pixel values.
        results = sorted(results, key=lambda k: k['process_id']) 
        for result in results:
            self.patterns.extend(result['patterns'])

    def _run_slave(self, pixels):
        # Exclude the master process from the LBP work
        num_processes = self.num_processes - 1
        process_id = self.process_id - 1

        # Set the left and right bounds of the segment to process
        segment_height = int(np.floor(self.height / num_processes))
        left_bound = (process_id * segment_height) if process_id != 0 else 1
        right_bound = (process_id * segment_height) + segment_height
        if process_id == num_processes - 1:
            # The last process should also process any remaining rows
            right_bound = self.height - 1

        # Calculate LBP for each non-edge pixel in the segment
        patterns = []
        for i in xrange(left_bound, right_bound):
            # Cache only the rows we need (within the neighborhood)
            previous_row = pixels[i - 1]
            current_row = pixels[i]
            next_row = pixels[i + 1]

            for j in xrange(1, self.width - 1):
                # Compare this pixel to its neighbors, starting at the top-left pixel and moving
                # clockwise, and use bit operations to efficiently update the feature vector
                pixel = current_row[j]
                pattern = 0
                pattern = pattern | (1 << 0) if pixel < previous_row[j-1] else pattern
                pattern = pattern | (1 << 1) if pixel < previous_row[j] else pattern
                pattern = pattern | (1 << 2) if pixel < previous_row[j+1] else pattern
                pattern = pattern | (1 << 3) if pixel < current_row[j+1] else pattern
                pattern = pattern | (1 << 4) if pixel < next_row[j+1] else pattern
                pattern = pattern | (1 << 5) if pixel < next_row[j] else pattern
                pattern = pattern | (1 << 6) if pixel < next_row[j-1] else pattern
                pattern = pattern | (1 << 7) if pixel < current_row[j-1] else pattern
                patterns.append(pattern)
                
        # Send the results to the master process and stop this slave process
        self.communicator.send(patterns, dest=0, tag=0)
