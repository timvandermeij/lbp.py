import sys
import os.path
import numpy as np
from PIL import Image
from multiprocessing import Process, Queue

class LBP:
    def __init__(self, filename, *ignore):
        # Convert the image to grayscale
        self.image = Image.open(filename).convert("L")
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.patterns = []

    def execute(self):
        self._process()
        self._output()

    def _process(self):
        pixels = list(self.image.getdata())
        pixels = [pixels[i * self.width:(i + 1) * self.width] for i in xrange(self.height)]

        # Calculate LBP for each non-edge pixel
        for i in xrange(1, self.height - 1):
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
                self.patterns.append(pattern)

    def _output(self):
        # Write the result to an image file
        result_image = Image.new(self.image.mode, (self.width - 2, self.height - 2))
        result_image.putdata(self.patterns)
        result_image.save("output.png")

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

def main(argv):
    filename = argv[0] if len(argv) > 0 else "input.png"
    algorithm = argv[1] if len(argv) > 1 else "lbp"
    num_processes = int(argv[2]) if len(argv) > 2 else 1

    algorithms = {
        "lbp": LBP,
        "multi-lbp": Multiprocessing_LBP,
        "multi-split-lbp": Multiprocessing_Split_LBP
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
