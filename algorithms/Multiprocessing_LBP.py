import numpy as np
from PIL import Image
from multiprocessing import Process, Queue
from LBP import LBP

class Multiprocessing_LBP(LBP):
    def __init__(self, filename, num_processes):
        LBP.__init__(self, filename)
        self.num_processes = num_processes

    def execute(self):
        self._distribute()
        self._output()

    def _process(self, process_id, pixels, queue):
        # Set the left and right bounds of the segment to process
        segment_height = int(np.floor(self.height / self.num_processes))
        left_bound = (process_id * segment_height) if process_id != 0 else 1
        right_bound = (process_id * segment_height) + segment_height
        if process_id == (self.num_processes - 1):
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
                pattern = pattern | (1 << 0) if pixel > previous_row[j-1] else pattern
                pattern = pattern | (1 << 1) if pixel > previous_row[j] else pattern
                pattern = pattern | (1 << 2) if pixel > previous_row[j+1] else pattern
                pattern = pattern | (1 << 3) if pixel > current_row[j+1] else pattern
                pattern = pattern | (1 << 4) if pixel > next_row[j+1] else pattern
                pattern = pattern | (1 << 5) if pixel > next_row[j] else pattern
                pattern = pattern | (1 << 6) if pixel > next_row[j-1] else pattern
                pattern = pattern | (1 << 7) if pixel > current_row[j-1] else pattern
                patterns.append(pattern)
                
        queue.put({
            'process_id': process_id,
            'patterns': patterns
        })

    def _distribute(self):
        pixels = np.array(self.image)

        # Spawn the processes
        processes = []
        queue = Queue()
        for process_id in xrange(self.num_processes):
            process = Process(target=self._process, args=(process_id, pixels, queue))
            process.start()
            processes.append(process)

        # Wait for all processes to finish
        results = [queue.get() for process in processes]
        [process.join() for process in processes]

        # Format the pixels correctly for the output function,
        # which expects a linear list of pixel values.
        results = sorted(results, key=lambda k: k['process_id']) 
        for result in results:
            self.patterns.extend(result['patterns'])
