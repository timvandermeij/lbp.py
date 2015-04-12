# TODO:
# - Multiprocessing could perhaps be made faster (OpenBLAS?)
# - 5.jpg and 8.jpg have a strange black line at the bottom

import sys
import os.path
import numpy as np
from PIL import Image
from multiprocessing import Process, Manager
import sharedmem

class LBP:
    def __init__(self, filename):
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
        neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
        for i in xrange(1, self.height - 1):
            for j in xrange(1, self.width - 1):
                pixel = pixels[i][j]

                # Compare this pixel to its neighbors, starting at the top-left pixel and moving
                # clockwise, and use bit operations to efficiently update the feature vector
                pattern = 0
                index = 0
                for neighbor in neighbors:
                    if pixel > pixels[i + neighbor[0]][j + neighbor[1]]:
                        pattern = pattern | (1 << index)
                    index += 1

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

    def _process(self, process_id, pixels, return_patterns):
        # Determine the height of the image segment to process
        segment_height = int(np.floor(self.height / self.num_processes))
        last_process_id = self.num_processes - 1
        if process_id == last_process_id:
            segment_height = self.height - (last_process_id * segment_height)

        # Set the left and right bounds of the segment to process
        left_bound = (process_id * segment_height) if process_id != 0 else 1
        right_bound = (process_id * segment_height) + segment_height
        if process_id == last_process_id:
            right_bound = self.height - 1

        # Calculate LBP for each non-edge pixel in the segment
        print("[{}] Started processing pixels {} to {}".format(process_id, left_bound, right_bound))
        neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
        patterns = []
        for i in xrange(left_bound, right_bound):
            for j in xrange(1, self.width - 1):
                pixel = pixels[i][j]

                # Compare this pixel to its neighbors, starting at the top-left pixel and moving
                # clockwise, and use bit operations to efficiently update the feature vector
                pattern = 0
                index = 0
                for neighbor in neighbors:
                    if pixel > pixels[i + neighbor[0]][j + neighbor[1]]:
                        pattern = pattern | (1 << index)
                    index += 1
                
                patterns.append(pattern)

        return_patterns[process_id] = patterns;
        print("[{}] Done".format(process_id))

    def _distribute(self):
        # Collect return values from the processes
        manager = Manager()
        patterns = manager.dict()
        for process_id in xrange(self.num_processes):
            patterns[process_id] = []

        # Put the pixel array in shared memory for all processes
        pixels = sharedmem.copy(np.array(self.image))

        # Spawn the processes
        processes = []
        for process_id in xrange(self.num_processes):
            process = Process(target=self._process, args=(process_id, pixels, patterns))
            processes.append(process)
            process.start()

        # Wait for all processes to finish
        [process.join() for process in processes]

        # Format the pixels correctly for the output function,
        # which expects a linear list of pixel values.
        for process_id in xrange(self.num_processes):
            self.patterns.extend(patterns[process_id])

def main(argv):
    filename = argv[0] if len(argv) > 0 else "input.png"
    num_processes = int(argv[1]) if len(argv) > 1 else 1
   
    if os.path.isfile(filename):
        if num_processes == 1:
            lbp = LBP(filename)
        else:
            lbp = Multiprocessing_LBP(filename, num_processes)

        lbp.execute()
    else:
        print("File '{}' does not exist.".format(filename))

if __name__ == "__main__":
    main(sys.argv[1:])
