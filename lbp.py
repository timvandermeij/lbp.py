import sys
import os.path
import numpy as np
from PIL import Image

class LBP:
    def __init__(self, filename):
        self.image = Image.open(filename)
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.pixels = list(self.image.getdata())
        self.patterns = []

    def execute(self):
        self._preprocess()
        self._process()
        self._output()

    def _preprocess(self):
        # Convert the image to grayscale
        self.image = self.image.convert('L')

        # Make pixels accessible like a 2D array (list of lists)
        self.pixels = [self.pixels[i * self.width:(i + 1) * self.width] for i in xrange(self.height)]

    def _process(self):
        # Calculate LBP for each non-edge pixel
        neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
        for i in xrange(1, self.height - 1):
            for j in xrange(1, self.width - 1):
                pixel = self.pixels[i][j]

                # Compare this pixel to its neighbors, starting at the top-left
                # pixel and moving clockwise, and use bit operations to quickly
                # update the feature vector
                pattern = 0
                for index in xrange(len(neighbors)):
                    neighbor = neighbors[index]
                    if pixel > self.pixels[i + neighbor[0]][j + neighbor[1]]:
                        pattern = pattern | (1 << index)

                self.patterns.append(pattern)

    def _output(self):
        # Write the result to an image file
        result_image = Image.new(self.image.mode, (self.width - 2, self.height - 2))
        result_image.putdata(self.patterns)
        result_image.save("output.png")

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
        print("File " + filename + " does not exist.")

if __name__ == "__main__":
    main(sys.argv[1:])
