# preshape - Perturbo Pool Data File Reshaper

The `preshape` program provides a helpful operation of reshaping the pool
data files that Perturbo generates under `./tmp` when carrier dynamics or
other transport calculations are to be performed.

To support scaling the calculations, Perturbo is able to generate distinct
pools of k-points and their corresponding q-points and other values, one
pool per MPI task.  The problem is, once these files have been generated for
a given number of pools (i.e. MPI tasks), the files cannot be reused for a
different number of pools.  This can be very frustrating when trying to find
the right number of MPI tasks for a given simulation.  You generate the data
files, and then you try Perturbo but it crashes.  Then you try generating a
different number of data files.

No longer!  The `preshape` utility can take the pool data files and
regenerate them for a different number of pools.  This tends to run much
faster than computing them from scratch.

## Installing `preshape`

Currently the installation process is very basic.  Clone the repository, and
run:

```
pip install -r requirements.txt
```

The `preshape` program has a pretty small number of dependencies:

*   `h5py` for HDF5 access from Python (which has `numpy` as a dependency)
*   `progressbar2` for providing a helpful progress bar at the command prompt

## Running `preshape`

To run `preshape` to regenerate pool data files, run it like this:

```
python preshape.py -f <path to source tmp directory> \
        -t <path to target tmp directory> \
        -p <number of pools to generate>
```

The source `tmp` directory is scanned, and `preshape` will determine the
number of pools in the source directory automatically.

If the target `tmp` directory is not empty, the program will report an error.