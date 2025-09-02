"""
System configuration for AF3 and RFdiffusion testing.
"""
from pathlib import Path


# AlphaFold3 configuration
AF3_CONFIG = {
    "af3_path": Path("/extdata1/TJ/workspace/alphafold3/"),
    "input_dir": Path("af_input"),
    "output_dir": Path("af_output"), 
    "slurm_script": Path("run_alphafold3.slurm"),
    "nodelist": None,  # Specific node (optional)
}

# RFdiffusion configuration
RFDIFFUSION_CONFIG = {
    "rfdiffusion_path": Path("/extdata3/OHC/protein_design/RFdiffusion/"),
    "conda_env": "SE3nv",
    "output_dir": Path("./rfdiffusion_output"),
    "slurm_config": {
        "partition": "gpu", 
        "nodes": 1,
        "ntasks": 1,
        "cpus-per-task": 8,
        "mem": "32G",
        "time": "02:00:00",
        "gres": "gpu:1"
    }
}