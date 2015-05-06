`lbp.py` is a Python implementation of the local binary patterns (LBP) algorithm for texture classification.

Prerequisites
=============

The versions indicated below have been verified. Other versions are also likely to work, but that has not been verified.

* Git 2.3.\* or 2.4.\*
* Python 2.7.9 with the following packages:
  * NumPy 1.9.2
  * Pillow 2.7.0
  * BeautifulSoup 3.2.1
  * Matplotlib 1.4.3
  * mpi4py 1.3.1
* OpenMPI 1.8.4

Cloning the repository
======================

The first step is to clone the repository to obtain a local copy of the code. Open a terminal and run the following commands.

    $ git clone https://github.com/timvandermeij/lbp.py.git
    $ cd lbp.py

Running the code
================

The first step is to obtain images to run `lbp.py` on. We have implemented a scraper to get large, high resolution images from [Unsplash](https://unsplash.com), which
provides free images under a [Creative Commons Zero](https://unsplash.com/license) license. Execute the following command in a terminal:

    $ python scraper.py

The scraper will then download the first 10 images from the Unsplash website. To create a larger dataset, one can simply increase the limit using the `--limit` parameter.
The downloaded images will be stored in the `images` folder in the `lbp.py` root directory. Optionally there is the `--target` parameter to `scraper.py` that
allows one to change this default target folder name.

Now that we have a dataset, we can run the local binary patterns algorithm. There are four variants:

* Regular LBP: the local binary patterns algorithm with neighborhood radius 1
* Multiprocessing LBP: divides the work of regular LBP over multiple processes and passes the entire image to each process
* Multiprocessing split LBP: divides the work of regular LBP over multiple processes and passes only the working range to each process
* Multiprocessing LBP (MPI): equal to multiprocessing LBP, but uses OpenMPI instead of Python's multiprocessing package

`lbp.py` is used to research the impact of multiprocessing on the regular LBP algorithm. All variants have been optimized to make the execution time as low
as possible. We refer the reader to the commit history for the exact optimizations that have been applied to the initial naive implementations. The regular
LBP algorithm is essentially a baseline for research. One can run the regular LBP variant on `images/1.jpg` and obtain output as follows:

    $ python main.py --input images/1.jpg --algorithm lbp --output

The multiprocessing LBP variant works by dividing the input image into _p_ horizontal slices and spawning _p_ processes. Each process gets as input the
entire image and the bounds of the slice that it should work on. The process applies the regular LBP algorithm on only the assigned slice and returns the
LBP descriptors. The main process collects the LBP descriptors from each process and merges them to create the final output. One can run the multiprocessing
LBP variant on `images/1.jpg` with 8 processes and obtain output as follows:

    $ python main.py --input images/1.jpg --algorithm multi-lbp --processes 8 --output

The multiprocessing split LBP variant works the same as the multiprocessing LBP variant with the exception that it does not pass the entire image as input
for the processes, but rather the exact slice that each process must work on. The idea is to reduce image passing overhead. One can run the multiprocessing
split LBP variant on `images/1.jpg` with 8 processes and obtain output as follows:

    $ python main.py --input images/1.jpg --algorithm multi-split-lbp --processes 8 --output

The multiprocessing LBP (MPI) variant works the same as the multiprocessing LBP variant with the exception that is uses OpenMPI to manage the processes instead
of using Python's multiprocessing package. This has been implemented to check if there is a difference in speed or communication overhead. One can run this
variant on `images/1.jpg` with 8 processes and obtain output as follows (we assume that OpenMPI has been installed):

    $ mpirun -np 9 python main.py --input images/3.png --algorithm multi-lbp-mpi --output

Note that for this algorithm the `--processes` flag is ignored because it is taken care of by OpenMPI. We let OpenMPI create 9 processes instead of 8 because
we want to add one master process that collects the results from the slave processes and that takes care of the final output.

Finally we have implemented a benchmark runner in `benchmark.py` to get time and memory consumption information for all possible combinations of algorithms
and processors. The benchmark runner will export the retrieved data to a JSON file as well as create plots of the data in EPS format. One can start benchmarking
by running:

    $ python benchmark.py

Installation notes for `huisuil01`
==================================

To use `lbp.py` on the `huisuil01` server at Leiden University, one must use a virtual environment as the installed Python version 2.7.3 is lower than required
for `lbp.py`. Follow the steps outlined below to set up a virtual environment with Python 2.7.9 and all required packages.

Python
------

Compile Python (version 2.7.9) from source:

    $ cd /scratch
    $ mkdir {username}
    $ chmod 700 {username}
    $ cd {username}
    $ wget https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
    $ tar xzvf Python-2.7.9.tgz
    $ cd Python-2.7.9
    $ ./configure --prefix=/scratch/{username}/python
    $ make
    $ make install
    $ cd ..
    $ rm Python-2.7.9.tgz
    $ rm -r Python-2.7.9

OpenMPI
-------

Compile OpenMPI from source:

    $ wget http://www.open-mpi.org/software/ompi/v1.8/downloads/openmpi-1.8.4.tar.gz
    $ tar xzvf openmpi-1.8.4.tar.gz
    $ cd openmpi-1.8.4
    $ ./configure --prefix=/scratch/{username}/openmpi
    $ make
    $ make install
    $ cd ..
    $ rm openmpi-1.8.4.tar.gz
    $ rm -r openmpi-1.8.4

Virtualenv
----------

`virtualenv` is already installed on `huisuil01`. Create a new virtual environment with the compiled Python interpreter as default:

    $ virtualenv -p /scratch/{username}/python/bin/python lbp

Update `~/.bashrc`
------------------

Append the following fragment to `~/.bashrc`. Do not forget to replace `{username}`.

    export SCRATCH="/scratch/{username}"
    alias activate="source $SCRATCH/lbp/bin/activate"
    export PATH="$PATH:$SCRATCH/openmpi/bin:$SCRATCH/openmpi/lib"
    export LIBRARY_PATH="$SCRATCH/openmpi/lib"
    export LD_LIBRARY_PATH="$SCRATCH/openmpi/lib"
    export CPATH="$SCRATCH/openmpi/include"
    export PKG_CONFIG_PATH="$SCRATCH/openmpi/lib/pkgconfig"

Python packages
---------------

Activate the virtual environment:

    $ activate

Update `pip` to the most recent version:

    (lbp)$ wget https://bootstrap.pypa.io/get-pip.py
    (lbp)$ python get-pip.py -U -I
    (lbp)$ rm get-pip.py

Then install the following dependencies:

    (lbp)$ pip install numpy
    (lbp)$ pip install pillow
    (lbp)$ pip install beautifulsoup
    (lbp)$ pip install distribute --upgrade
    (lbp)$ pip install matplotlib
    (lbp)$ pip install mpi4py

Now we can run `lbp.py` using the steps described above when we have activated the virtual environment.

License
=======

`lbp.py` is licensed under the permissive MIT license.

Author
======

* Tim van der Meij (Leiden University, @timvandermeij)
