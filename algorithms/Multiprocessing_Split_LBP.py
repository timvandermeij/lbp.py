import numpy as np
from PIL import Image
from multiprocessing import Process, Queue
from Multiprocessing_LBP import Multiprocessing_LBP

class Multiprocessing_Split_LBP(Multiprocessing_LBP):
    def __init__(self, filename, num_processes):
        Multiprocessing_LBP.__init__(self, filename, num_processes)

    def _process(self, process_id, pixels, queue):
        # Determine the bounds for processing
        left_bound = 0
        if process_id == 0:
            left_bound = 1
        right_bound = pixels.shape[0] - 1
        if process_id == (self.num_processes - 1):
            right_bound -= 1
        
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

        queue.put({
            'process_id': process_id,
            'patterns': patterns
        })

    def _distribute(self):
        pixels = np.array(self.image)
        segment_height = int(np.floor(self.height / self.num_processes))
        processes = []
        queue = Queue()
        for process_id in xrange(self.num_processes):
            # Pass only the part of the image that the process needs to work with.
            # This is done in order to make the processes work independently.
            # Because of the neighborhood, each segment should partially overlap
            # with the next and/or previous segment.
            left_bound = process_id * segment_height
            right_bound = left_bound + segment_height
            if process_id > 0:
                left_bound -= 1
            if process_id == (self.num_processes - 1):
                # The last process should also process any remaining rows
                right_bound = self.height

            # Start the process and pass only the pixels within the bounds
            segment_pixels = pixels[left_bound:right_bound]
            process = Process(target=self._process, args=(process_id, segment_pixels, queue))
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
