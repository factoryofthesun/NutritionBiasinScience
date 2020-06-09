#!/bin/bash
#-----------------------------------------------
# Account Information
#SBATCH --account=pi-arao0         # basic (default), staff, phd, faculty

#---------------------------------------------------------------------------------
# Resources requested

#SBATCH --partition=gpu       # standard (default), long, gpu, mpi, highmem
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=1          # number of CPUs requested (for parallel tasks)
#SBATCH --time=0-24:00:00          # wall clock limit (d-hh:mm:ss)
#SBATCH --mem-per-cpu=8G
#---------------------------------------------------------------------------------
# Job specific name (helps organize and track progress of jobs)

#SBATCH --job-name=xlnet_ensemble    # user-defined job name
#SBATCH --output=Outputs/slurm_xlnet_ensemble.out

#---------------------------------------------------------------------------------
# Print some useful variables

echo "Job ID: $SLURM_JOB_ID"
echo "Job User: $SLURM_JOB_USER"
echo "Num Cores: $SLURM_JOB_CPUS_PER_NODE"

#---------------------------------------------------------------------------------
# Load necessary modules for the job
module load python/booth/3.6/3.6.3
source ~/venv/torch/bin/activate
#---------------------------------------------------------------------------------
# Execute
srun python xlnet_ensemble.py > Outputs/xlnet_ensemble.out
