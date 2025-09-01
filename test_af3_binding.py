#!/usr/bin/env python3
"""
Simple test script to evaluate protein-protein binding using AlphaFold3.
Bottom-up approach - start with basic AF3 functionality.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path


def create_af3_input(target_sequence: str, binder_sequence: str, job_name: str = "test_binding") -> dict:
    """
    Create AlphaFold3 input JSON for two protein sequences.
    
    Args:
        target_sequence: Target protein amino acid sequence
        binder_sequence: Binder protein amino acid sequence  
        job_name: Name for the prediction job
        
    Returns:
        AF3 input dictionary
    """
    
    fold_input = {
        "name": job_name,
        "modelSeeds": [42],  # Reproducible seed
        "sequences": [
            {
                "protein": {
                    "id": "target",
                    "sequence": target_sequence,
                    "modifications": [],
                    "unpairedMsa": None,
                    "pairedMsa": None,
                    "templates": []  # No templates - ab initio prediction
                }
            },
            {
                "protein": {
                    "id": "binder", 
                    "sequence": binder_sequence,
                    "modifications": [],
                    "unpairedMsa": None,
                    "pairedMsa": None,
                    "templates": []  # No templates - ab initio prediction
                }
            }
        ],
        "dialect": "alphafold3",
        "version": 1
    }
    
    return fold_input


def submit_af3_job(input_dict: dict, input_dir: str, output_dir: str, nodelist: str = None) -> str:
    """
    Submit AlphaFold3 job to SLURM.
    
    Args:
        input_dict: AF3 input dictionary
        input_dir: Input directory path
        output_dir: Output directory path
        nodelist: Specific SLURM node (optional)
        
    Returns:
        SLURM job ID
    """
    
    # Create input/output directories
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Write input file
    input_filename = f"fold_input_{input_dict['name']}.json"
    input_path = Path(input_dir) / input_filename
    
    with open(input_path, 'w') as f:
        json.dump(input_dict, f, indent=2)
    
    print(f"Created AF3 input: {input_path}")
    
    # Submit SLURM job
    cmd = [
        "sbatch",
        "run_alphafold3.slurm",  # Your existing AF3 SLURM script
        input_filename,
        input_dir,
        output_dir
    ]
    
    if nodelist:
        cmd.insert(1, f"--nodelist={nodelist}")
    
    print(f"Submitting: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        slurm_job_id = result.stdout.strip().split()[-1]
        print(f"Submitted AF3 job: {slurm_job_id}")
        return slurm_job_id
        
    except subprocess.CalledProcessError as e:
        print(f"SLURM submission failed: {e.stderr}")
        raise


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


def parse_af3_results(output_dir: str, job_name: str) -> dict:
    """
    Parse AlphaFold3 output for binding metrics.
    
    Args:
        output_dir: AF3 output directory
        job_name: Job name used in input
        
    Returns:
        Parsed results dictionary
    """
    
    result_dir = Path(output_dir) / f"fold_{job_name}"
    
    if not result_dir.exists():
        return {"error": f"Result directory not found: {result_dir}"}
    
    results = {
        "job_name": job_name,
        "result_dir": str(result_dir)
    }
    
    # Look for confidence scores
    confidence_file = result_dir / "summary_confidences.json"
    if confidence_file.exists():
        try:
            with open(confidence_file) as f:
                confidences = json.load(f)
            results["confidences"] = confidences
            results["ptm_score"] = confidences.get("confidences", {}).get("ptm", 0.0)
            results["iptm_score"] = confidences.get("confidences", {}).get("iptm", 0.0)
        except Exception as e:
            results["confidence_error"] = str(e)
    
    # Look for structure files
    structure_files = list(result_dir.glob("*_model_*.cif"))
    if structure_files:
        results["structure_file"] = str(structure_files[0])  # Take first model
        results["num_models"] = len(structure_files)
    else:
        results["structure_error"] = "No structure files found"
    
    # Basic binding assessment
    iptm = results.get("iptm_score", 0.0)
    ptm = results.get("ptm_score", 0.0)
    
    results["binding_quality"] = "high" if iptm > 0.8 else "medium" if iptm > 0.5 else "low"
    results["overall_confidence"] = (iptm + ptm) / 2.0
    
    return results


def main():
    """Main test function."""
    
    # Example protein sequences (replace with your own)
    target_seq = "MKQHKAMIVALIVICITAVVAALVTRKDLCEVHIRTGQTEVAVFTAYESE"  # Example target
    binder_seq = "MAEGEITTFTALTEKFNLPPGNYKKPKLLYCSNGGHFLRILPDGTVDGT"    # Example binder
    
    # Configuration (adjust paths for your system)
    input_dir = "/tmp/af3_test_input"
    output_dir = "/tmp/af3_test_output" 
    job_name = "test_binding_001"
    
    print("=== AlphaFold3 Binding Test ===")
    print(f"Target sequence: {target_seq[:30]}...")
    print(f"Binder sequence: {binder_seq[:30]}...")
    print(f"Job name: {job_name}")
    
    try:
        # Step 1: Create AF3 input
        print("\n1. Creating AF3 input...")
        af3_input = create_af3_input(target_seq, binder_seq, job_name)
        print(f"   Created input with {len(af3_input['sequences'])} proteins")
        
        # Step 2: Submit job  
        print("\n2. Submitting to SLURM...")
        job_id = submit_af3_job(af3_input, input_dir, output_dir)
        print(f"   Job ID: {job_id}")
        
        # Step 3: Monitor job (basic check)
        print(f"\n3. Job status check...")
        status = check_job_status(job_id)
        print(f"   Current status: {status}")
        
        if status in ["completed", "failed"]:
            # Step 4: Parse results if completed
            print(f"\n4. Parsing results...")
            results = parse_af3_results(output_dir, job_name)
            
            print(f"   Results: {json.dumps(results, indent=2)}")
            
            if "iptm_score" in results:
                print(f"\n=== BINDING ASSESSMENT ===")
                print(f"ipTM score: {results['iptm_score']:.3f}")
                print(f"pTM score: {results['ptm_score']:.3f}") 
                print(f"Binding quality: {results['binding_quality']}")
                print(f"Overall confidence: {results['overall_confidence']:.3f}")
        else:
            print(f"   Job still {status}. Check later with:")
            print(f"   squeue -j {job_id}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())