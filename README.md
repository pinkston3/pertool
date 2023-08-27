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
        [--mp]
```

The source `tmp` directory is scanned, and `preshape` will determine the
number of pools in the source directory automatically.

If the target `tmp` directory is not empty, the program will report an error.

The `--mp` flag can be used to enable multi-process parallelism, which often
yields a substantial performance improvement.

## Parallel Reshape Operations

[The HDF5 library is not designed to be used in highly concurrent settings.]
(https://portal.hdfgroup.org/display/knowledge/Questions+about+thread-safety+and+concurrent+access)
However, a certain amount of performance improvement is possible through the
use of multi-process programming and the `multiprocessing` Python standard
library.  The `preshape` program supports using `multiprocessing` with the
`--mp` flag, which parallelizes the reshape operation in these ways:

*   The source HDF5 files are scanned in parallel, with one subprocess being
    started for each source file.  This should yield significant performance
    improvement in the typical case, as the source files are completely
    independent.  Since the scan operation will typically be IO-bound, having
    multiple concurrent scans will be a big win.

*   The target HDF5 files are generated in parallel, with one subprocess
    generating each target file.  This step is also likely to yield
    significant performance improvement, but each subprocess must access all
    source HDF5 files, and the HDF5 library may use file locking to ensure
    exclusive access, even in read-only cases.  (See above link for details.)

Testing is necessary to see if the multi-process code will be faster than
serial code, but in the limited tests done on NERSC Perlmutter, an order of
magnitude performance improvement is typical.
