#!/usr/bin/env python3
"""
RFdiffusion test script for protein binder generation.
Bottom-up approach - basic RFdiffusion functionality.
"""

import subprocess
from pathlib import Path


def create_rfdiffusion_command(
    rfdiffusion_path: Path,
    conda_env: str,
    target_pdb: str,
    output_prefix: str,
    contig_length: int = 100,
    num_designs: int = 10,
    guide_scale: float = 2.0
) -> str:
    """
    Create RFdiffusion command for binder generation.
    
    Args:
        rfdiffusion_path: Path to RFdiffusion installation
        conda_env: Conda environment name
        target_pdb: Path to target protein PDB
        output_prefix: Output file prefix
        contig_length: Length of binder to generate
        num_designs: Number of designs to generate
        guide_scale: Guidance scale for conditioning
        
    Returns:
        Complete command string
    """
    
    # Build RFdiffusion command
    cmd_parts = [
        f"cd {rfdiffusion_path}",
        f"conda activate {conda_env}",
        f"./scripts/run_inference.py",
        f"'contigmap.contigs=[{contig_length}-{contig_length}]'",
        f"inference.output_prefix={output_prefix}",
        f"inference.input_pdb={target_pdb}",
        f"inference.num_designs={num_designs}",
        f"'potentials.guiding_potentials=[\"type:substrate_contacts,s:1,subset_atom_indices:\":\"all\",contact_level:atom\"]'",
        f"potentials.guide_scale={guide_scale}",
        f"potentials.guide_decay=\"quadratic\""
    ]
    
    # Join with && for sequential execution
    return " && ".join(cmd_parts[:2]) + " && " + " ".join(cmd_parts[2:])


def create_rfdiffusion_slurm_script(
    command: str,
    job_name: str,
    output_dir: Path,
    slurm_config: dict
) -> Path:
    """
    Create SLURM script for RFdiffusion job.
    
    Args:
        command: RFdiffusion command to execute
        job_name: Job name for SLURM
        output_dir: Output directory
        slurm_config: SLURM configuration dict
        
    Returns:
        Path to created SLURM script
    """
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = output_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create SLURM script content
    script_content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={slurm_config['partition']}
#SBATCH --nodes={slurm_config['nodes']}
#SBATCH --ntasks={slurm_config['ntasks']}
#SBATCH --cpus-per-task={slurm_config['cpus-per-task']}
#SBATCH --mem={slurm_config['mem']}
#SBATCH --time={slurm_config['time']}
#SBATCH --gres={slurm_config['gres']}
#SBATCH --output={log_dir}/{job_name}.out
#SBATCH --error={log_dir}/{job_name}.err

echo "Starting RFdiffusion job: {job_name}"
echo "Command: {command}"

{command}

echo "RFdiffusion job completed: {job_name}"
"""
    
    # Write script file
    script_path = log_dir / f"{job_name}.slurm"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return script_path


def submit_rfdiffusion_job(
    rfdiffusion_path: Path,
    conda_env: str,
    target_pdb: str,
    output_dir: Path,
    job_name: str,
    slurm_config: dict,
    **rfdiffusion_params
) -> str:
    """
    Submit RFdiffusion job to SLURM.
    
    Args:
        rfdiffusion_path: RFdiffusion installation path
        conda_env: Conda environment
        target_pdb: Target protein PDB file
        output_dir: Output directory
        job_name: Job identifier
        slurm_config: SLURM configuration
        **rfdiffusion_params: RFdiffusion parameters
        
    Returns:
        SLURM job ID
    """
    
    # Set default parameters
    params = {
        'contig_length': 100,
        'num_designs': 10,
        'guide_scale': 2.0,
        **rfdiffusion_params
    }
    
    # Create output prefix
    output_prefix = output_dir / f"binders_{job_name}"
    
    # Generate command
    command = create_rfdiffusion_command(
        rfdiffusion_path=rfdiffusion_path,
        conda_env=conda_env,
        target_pdb=target_pdb,
        output_prefix=str(output_prefix),
        **params
    )
    
    print(f"RFdiffusion command: {command}")
    
    # Create SLURM script
    script_path = create_rfdiffusion_slurm_script(
        command=command,
        job_name=job_name,
        output_dir=output_dir,
        slurm_config=slurm_config
    )
    
    print(f"Created SLURM script: {script_path}")
    
    # Submit job
    result = subprocess.run(
        ["sbatch", str(script_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"SLURM submission failed: {result.stderr}")
    
    slurm_job_id = result.stdout.strip().split()[-1]
    print(f"Submitted RFdiffusion job: {slurm_job_id}")
    
    return slurm_job_id


def check_rfdiffusion_output(output_dir: Path, job_name: str) -> list:
    """
    Check for generated binder PDB files.
    
    Args:
        output_dir: RFdiffusion output directory
        job_name: Job identifier
        
    Returns:
        List of generated PDB file paths
    """
    
    # Look for generated PDB files
    pattern = f"binders_{job_name}_*.pdb"
    pdb_files = list(output_dir.glob(pattern))
    
    # Sort by filename (typically includes sequence number)
    pdb_files.sort()
    
    return pdb_files


def check_job_status(slurm_job_id: str) -> str:
    """Check SLURM job status."""
    try:
        result = subprocess.run(
            ["squeue", "-j", slurm_job_id, "-h", "-o", "%T"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            return "completed"  # Not in queue
        else:
            status = result.stdout.strip()
            status_map = {
                'R': 'running',
                'PD': 'pending',
                'CG': 'running', 
                'CD': 'completed',
                'F': 'failed',
                'CA': 'cancelled'
            }
            return status_map.get(status, status.lower())
            
    except Exception as e:
        print(f"Error checking job status: {e}")
        return "unknown"