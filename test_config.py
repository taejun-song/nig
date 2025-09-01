"""
Simple configuration for AF3 testing.
Adjust these paths for your system.
"""

# AlphaFold3 configuration
AF3_CONFIG = {
    "input_dir": "/extdata3/OHC/alphafold3/af_input",      # Your AF3 input directory
    "output_dir": "/extdata3/OHC/alphafold3/af_output",    # Your AF3 output directory
    "slurm_script": "run_alphafold3.slurm",               # Your AF3 SLURM script
    "nodelist": None,  # Specific node (optional)
}

# Test protein sequences
TEST_SEQUENCES = {
    "target": {
        "name": "target_protein",
        "sequence": "MKQHKAMIVALIVICITAVVAALVTRKDLCEVHIRTGQTEVAVFTAYESE"  # Replace with your target
    },
    "binder": {
        "name": "binder_protein", 
        "sequence": "MAEGEITTFTALTEKFNLPPGNYKKPKLLYCSNGGHFLRILPDGTVDGT"   # Replace with your binder
    }
}

# Or load from FASTA files
def load_sequence_from_fasta(fasta_path: str) -> str:
    """Load protein sequence from FASTA file."""
    sequence = ""
    with open(fasta_path, 'r') as f:
        for line in f:
            if not line.startswith('>'):
                sequence += line.strip()
    return sequence

# Example usage:
# TEST_SEQUENCES["target"]["sequence"] = load_sequence_from_fasta("target.fasta")
# TEST_SEQUENCES["binder"]["sequence"] = load_sequence_from_fasta("binder.fasta")