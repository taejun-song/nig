#!/usr/bin/env python3
"""
Simple test runner for AF3 protein binding evaluation.
Usage: python run_binding_test.py
"""

import sys
import time
from test_af3_binding import create_af3_input, submit_af3_job, check_job_status, parse_af3_results
from test_config import AF3_CONFIG, TEST_SEQUENCES


def main():
    """Run a simple AF3 binding test."""
    
    print("🧬 AlphaFold3 Protein Binding Test")
    print("=" * 50)
    
    # Get sequences
    target_seq = TEST_SEQUENCES["target"]["sequence"]
    binder_seq = TEST_SEQUENCES["binder"]["sequence"]
    
    print(f"Target protein: {target_seq[:50]}...")
    print(f"Binder protein: {binder_seq[:50]}...")
    print(f"Target length: {len(target_seq)} residues")
    print(f"Binder length: {len(binder_seq)} residues")
    
    # Generate job name with timestamp
    job_name = f"binding_test_{int(time.time())}"
    print(f"Job name: {job_name}")
    
    try:
        # Step 1: Create AF3 input
        print("\n📝 Creating AF3 input...")
        af3_input = create_af3_input(target_seq, binder_seq, job_name)
        
        # Step 2: Submit job
        print("🚀 Submitting to SLURM...")
        job_id = submit_af3_job(
            af3_input, 
            AF3_CONFIG["input_dir"],
            AF3_CONFIG["output_dir"],
            AF3_CONFIG.get("nodelist")
        )
        
        print(f"✅ Job submitted: {job_id}")
        print(f"Monitor with: squeue -j {job_id}")
        print(f"Check logs: tail -f /extdata3/OHC/alphafold3/af_output/logs/{job_name}*.out")
        
        # Step 3: Basic status check
        print(f"\n⏳ Checking initial status...")
        status = check_job_status(job_id)
        print(f"Status: {status}")
        
        if status == "pending":
            print("Job is queued. It will run when resources are available.")
        elif status == "running":
            print("Job is running. This may take 2-4 hours.")
        elif status == "completed":
            print("Job completed quickly - checking results...")
            
            results = parse_af3_results(AF3_CONFIG["output_dir"], job_name)
            print_results(results)
        else:
            print(f"Unexpected status: {status}")
            
        print(f"\n📋 Next Steps:")
        print(f"1. Wait for job to complete (check with: squeue -j {job_id})")
        print(f"2. Parse results with: python -c \"")
        print(f"   from test_af3_binding import parse_af3_results")
        print(f"   import json")
        print(f"   r = parse_af3_results('{AF3_CONFIG['output_dir']}', '{job_name}')")
        print(f"   print(json.dumps(r, indent=2))")
        print(f"   \"")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    return 0


def print_results(results):
    """Pretty print AF3 results."""
    print(f"\n🎯 BINDING EVALUATION RESULTS")
    print("=" * 40)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
        
    if "iptm_score" in results:
        iptm = results["iptm_score"]
        ptm = results["ptm_score"]
        quality = results["binding_quality"]
        
        print(f"Interface confidence (ipTM): {iptm:.3f}")
        print(f"Overall confidence (pTM):    {ptm:.3f}")
        print(f"Binding quality:             {quality}")
        
        # Interpretation
        print(f"\n💡 Interpretation:")
        if iptm > 0.8:
            print("🟢 Excellent binding predicted - high confidence interface")
        elif iptm > 0.6:
            print("🟡 Good binding predicted - moderate confidence interface") 
        elif iptm > 0.4:
            print("🟠 Weak binding predicted - low confidence interface")
        else:
            print("🔴 Poor binding predicted - very low confidence")
            
        if "structure_file" in results:
            print(f"\n📁 Structure file: {results['structure_file']}")
            
    else:
        print("⚠️  No confidence scores found in results")
        print(f"Raw results: {results}")


if __name__ == "__main__":
    exit(main())