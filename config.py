"""
System configuration for AF3 testing.
"""

# AlphaFold3 configuration
AF3_CONFIG = {
    "input_dir": "/extdata1/TJ/workspace/alphafold3/af_input",
    "output_dir": "/extdata1/TJ/workspace/alphafold3/af_output", 
    "slurm_script": "run_alphafold3.slurm",
    "nodelist": None,  # Specific node (optional)
}