"""
Input data loader for protein sequences.
Handles FASTA files, PDB files, and direct sequences.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


def load_sequence_from_fasta(fasta_path: str) -> str:
    """Load protein sequence from FASTA file."""
    sequence = ""
    with open(fasta_path, 'r') as f:
        for line in f:
            if not line.startswith('>'):
                sequence += line.strip()
    return sequence


def load_sequence_from_pdb(pdb_path: str, chain_id: str = 'A') -> str:
    """Extract protein sequence from PDB file."""
    try:
        from Bio import PDB
        parser = PDB.PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_path)
        
        # Standard amino acid mapping
        aa_map = {
            'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E', 'PHE': 'F',
            'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LYS': 'K', 'LEU': 'L',
            'MET': 'M', 'ASN': 'N', 'PRO': 'P', 'GLN': 'Q', 'ARG': 'R',
            'SER': 'S', 'THR': 'T', 'VAL': 'V', 'TRP': 'W', 'TYR': 'Y'
        }
        
        sequence = []
        for model in structure:
            if chain_id in model:
                chain = model[chain_id]
                for residue in chain:
                    if residue.get_id()[0] == ' ':  # Standard residue
                        res_name = residue.get_resname()
                        if res_name in aa_map:
                            sequence.append(aa_map[res_name])
                        else:
                            sequence.append('X')  # Unknown residue
                break
                
        return ''.join(sequence)
        
    except ImportError:
        raise ImportError("BioPython required for PDB parsing. Install with: pip install biopython")
    except Exception as e:
        raise ValueError(f"Failed to parse PDB file {pdb_path}: {e}")


def load_protein_data(protein_config: Dict) -> Dict:
    """
    Load protein data from various sources.
    
    Args:
        protein_config: Dictionary with protein specification:
            - name: Protein name
            - sequence: Direct sequence (optional)
            - fasta_path: Path to FASTA file (optional) 
            - pdb_path: Path to PDB file (optional)
            - chain_id: Chain ID for PDB (default 'A')
            
    Returns:
        Dictionary with loaded protein data
    """
    
    result = {
        "name": protein_config.get("name", "unknown"),
        "sequence": None,
        "source": None,
        "length": 0
    }
    
    # Priority: direct sequence > FASTA > PDB
    if "sequence" in protein_config and protein_config["sequence"]:
        result["sequence"] = protein_config["sequence"]
        result["source"] = "direct"
        
    elif "fasta_path" in protein_config:
        fasta_path = protein_config["fasta_path"]
        if os.path.exists(fasta_path):
            result["sequence"] = load_sequence_from_fasta(fasta_path)
            result["source"] = f"fasta:{fasta_path}"
        else:
            raise FileNotFoundError(f"FASTA file not found: {fasta_path}")
            
    elif "pdb_path" in protein_config:
        pdb_path = protein_config["pdb_path"]
        chain_id = protein_config.get("chain_id", "A")
        if os.path.exists(pdb_path):
            result["sequence"] = load_sequence_from_pdb(pdb_path, chain_id)
            result["source"] = f"pdb:{pdb_path}:{chain_id}"
        else:
            raise FileNotFoundError(f"PDB file not found: {pdb_path}")
            
    else:
        raise ValueError("No sequence source specified (sequence, fasta_path, or pdb_path)")
    
    result["length"] = len(result["sequence"])
    
    if result["length"] == 0:
        raise ValueError(f"Empty sequence loaded for {result['name']}")
    
    return result


def load_test_inputs(input_file: str) -> Dict:
    """
    Load test inputs from a simple text file.
    
    Format:
        target_name=MyTarget
        target_fasta=./test_data/target.fasta
        binder_name=MyBinder  
        binder_sequence=MKQHKAMIV...
    """
    
    config = {}
    
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    
    # Parse into protein configs
    target_config = {
        "name": config.get("target_name", "target"),
    }
    binder_config = {
        "name": config.get("binder_name", "binder"),
    }
    
    # Add sequence sources
    if "target_sequence" in config:
        target_config["sequence"] = config["target_sequence"]
    elif "target_fasta" in config:
        target_config["fasta_path"] = config["target_fasta"]
    elif "target_pdb" in config:
        target_config["pdb_path"] = config["target_pdb"]
        target_config["chain_id"] = config.get("target_chain", "A")
        
    if "binder_sequence" in config:
        binder_config["sequence"] = config["binder_sequence"]
    elif "binder_fasta" in config:
        binder_config["fasta_path"] = config["binder_fasta"]
    elif "binder_pdb" in config:
        binder_config["pdb_path"] = config["binder_pdb"]
        binder_config["chain_id"] = config.get("binder_chain", "A")
    
    return {
        "target": load_protein_data(target_config),
        "binder": load_protein_data(binder_config),
        "job_name": config.get("job_name", "binding_test")
    }