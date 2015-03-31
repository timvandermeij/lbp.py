import sys
import os.path
import numpy as np
from PIL import Image

class LBP:
    def __init__(self, filename):
        self.filename = filename

    def process(self):
        # Open the image and convert to grayscale
        image = Image.open(self.filename).convert('L')

        # Make pixels accessible like a 2D array (list of lists)
        pixels = list(image.getdata())
        width, height = image.size
        pixels = [pixels[i * width:(i + 1) * width] for i in xrange(height)]

        # Calculate LBP for each non-edge pixel
        results = []
        for i in xrange(1, height - 1):
            for j in xrange(1, width - 1):
                pixel = pixels[i][j]

                # Compare this pixel to its neighbors, starting at the top-left
                # pixel and moving clockwise, and use bit operations to quickly
                # update the feature vector
                result = 0
                neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                for index in xrange(len(neighbors)):
                    neighbor = neighbors[index]
                    if pixel > pixels[i + neighbor[0]][j + neighbor[1]]:
                        result = result | (1 << index)

                results.append(result)

        # Write the result to an image file
        result_image = Image.new(image.mode, (width - 2, height - 2))
        result_image.putdata(results)
        result_image.save("output.png")

def main(argv):
    filename = argv[0] if len(argv) > 0 else "input.png"
    verbose = argv[1] if len(argv) > 1 else True
   
    # Make sure NumPy prints full arrays instead of shortened versions
    if verbose:
        np.set_printoptions(threshold=np.nan)
    
    if os.path.isfile(filename):
        lbp = LBP(filename)
        lbp.process()
    else:
        print("The file " + filename + " does not exist.")

if __name__ == "__main__":
    main(sys.argv[1:])
