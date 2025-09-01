"""
System configuration for AF3 testing.
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