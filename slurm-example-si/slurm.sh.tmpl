#!/bin/bash

#SBATCH -q regular
#SBATCH -t 6:00:00

# Add _g for GPU nodes.
#SBATCH -A m2626_g

# "cpu" for CPU nodes, "gpu" for GPU nodes
#SBATCH -C gpu

#SBATCH -N {{nodes}}
#SBATCH -n {{mpi_tasks}}

# 32 cores for GPU nodes, 64 cores for CPU nodes
#SBATCH --cpus-per-task=32

# Bind each MPI task to 1 close GPU.
#SBATCH --gpus-per-task=1
#SBATCH --gpu-bind=single:1

#SBATCH --mail-type=begin,end,fail
#SBATCH --mail-user=donnie@cms.caltech.edu

#SBATCH -J ref-{{gridsize}}-gpu-{{mpi_tasks}}t.x

#-------------------------------------------------------------

echo Job starts at `date`
echo Submit dir: $SLURM_SUBMIT_DIR

#-------------------------------------------------------------
# Perturbo essential configuration

# Need the NVIDIA runtime
module load nvhpc/22.7
module load cray-hdf5

PERTURBO_BIN=/global/homes/d/donniep3/testbins/perturbo-hybrid-rev-acc-arred-8b.x
PERT_IN={{pert_in}}

#-------------------------------------------------------------
# Compute the MPI/OpenMP values

mpi_tasks_per_node=4

cpus_per_node=$SLURM_CPUS_ON_NODE
total_nodes=$SLURM_NNODES

total_mpi_tasks=`expr $mpi_tasks_per_node \* $total_nodes`
cpus_per_task=`expr $cpus_per_node / $mpi_tasks_per_node`

#-------------------------------------------------------------
# Set up the environment and run Perturbo

#OpenMP settings:  32 for GPU nodes, 64 for CPU nodes
export OMP_NUM_THREADS=$cpus_per_task
export OMP_PLACES=threads
export OMP_PROC_BIND=true

# Print our environment, for debugging
env

# Run Perturbo
srun -N $total_nodes -n $total_mpi_tasks -c $cpus_per_task \
        --cpu_bind=cores --gpus-per-task=1 --gpu-bind=single:1 \
        $PERTURBO_BIN -npools $total_mpi_tasks -i $PERT_IN

#-------------------------------------------------------------

echo Job ends at `date`
