#!/usr/bin/env python3
"""
Integrated workflow: Generate protein binders with RFdiffusion and evaluate with AF3.
"""

import sys
import argparse
from pathlib import Path

from config import RFDIFFUSION_CONFIG, AF3_CONFIG
from input_loader import load_test_inputs
from test_rfdiffusion import submit_rfdiffusion_job, check_job_status, check_rfdiffusion_output
from test_af3_binding import create_af3_input, submit_af3_job, parse_af3_results


def main():
    """Run integrated binder generation and evaluation workflow."""
    
    parser = argparse.ArgumentParser(description='Generate and evaluate protein binders')
    parser.add_argument('input_file', nargs='?', 
                       default='test_data/example_input.txt',
                       help='Input configuration file')
    parser.add_argument('--contig-length', type=int, default=100,
                       help='Length of binder to generate')
    parser.add_argument('--num-designs', type=int, default=10,
                       help='Number of binder designs')
    parser.add_argument('--guide-scale', type=float, default=2.0,
                       help='RFdiffusion guidance scale')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without submitting jobs')
    
    args = parser.parse_args()
    
    print("🧬 Protein Binder Generation Workflow")
    print("=" * 50)
    
    try:
        # Step 1: Load target protein
        print(f"📂 Loading target from: {args.input_file}")
        inputs = load_test_inputs(args.input_file)
        target = inputs['target']
        
        print(f"\n🎯 Target: {target['name']}")
        print(f"   Source: {target['source']}")
        print(f"   Length: {target['length']} residues")
        print(f"   Sequence: {target['sequence'][:50]}...")
        
        job_name = f"binder_gen_{inputs['job_name']}"
        
        # RFdiffusion parameters
        rf_params = {
            'contig_length': args.contig_length,
            'num_designs': args.num_designs,
            'guide_scale': args.guide_scale
        }
        
        print(f"\n🔧 RFdiffusion Parameters:")
        for key, value in rf_params.items():
            print(f"   {key}: {value}")
        
        if args.dry_run:
            print("\n✅ Dry run completed - would generate binders and evaluate with AF3")
            return 0
        
        # Step 2: Generate binders with RFdiffusion
        print(f"\n🚀 Step 1: Generating binders with RFdiffusion...")
        
        # For this workflow, we need a target PDB file
        # If we only have sequence, we'd need structure prediction first
        target_pdb = "target_structure.pdb"  # This should be provided or predicted
        
        rf_job_id = submit_rfdiffusion_job(
            rfdiffusion_path=RFDIFFUSION_CONFIG["rfdiffusion_path"],
            conda_env=RFDIFFUSION_CONFIG["conda_env"],
            target_pdb=target_pdb,
            output_dir=RFDIFFUSION_CONFIG["output_dir"],
            job_name=job_name,
            slurm_config=RFDIFFUSION_CONFIG["slurm_config"],
            **rf_params
        )
        
        print(f"✅ RFdiffusion job submitted: {rf_job_id}")
        
        # Step 3: Monitor RFdiffusion job
        print(f"\n⏳ Monitoring RFdiffusion job...")
        rf_status = check_job_status(rf_job_id)
        print(f"   Status: {rf_status}")
        
        if rf_status == "completed":
            # Step 4: Check for generated binders
            print(f"\n📁 Checking for generated binders...")
            binder_files = check_rfdiffusion_output(
                RFDIFFUSION_CONFIG["output_dir"], 
                job_name
            )
            
            if not binder_files:
                print("❌ No binder files found")
                return 1
                
            print(f"✅ Found {len(binder_files)} generated binders")
            for i, binder_file in enumerate(binder_files[:3], 1):  # Show first 3
                print(f"   {i}. {binder_file.name}")
            
            # Step 5: Evaluate binders with AF3
            print(f"\n🔬 Step 2: Evaluating binders with AlphaFold3...")
            
            # For each binder, create AF3 complex evaluation
            af3_jobs = []
            for i, binder_file in enumerate(binder_files):
                # Extract binder sequence from PDB (simplified)
                binder_seq = extract_sequence_from_pdb(binder_file)
                
                # Create AF3 input for target-binder complex
                af3_input = create_af3_input(
                    target['sequence'],
                    binder_seq,
                    f"{job_name}_eval_{i}"
                )
                
                # Submit AF3 evaluation
                af3_job_id = submit_af3_job(
                    AF3_CONFIG["af3_path"],
                    AF3_CONFIG["input_dir"],
                    AF3_CONFIG["output_dir"],
                    af3_input,
                    AF3_CONFIG.get("nodelist")
                )
                
                af3_jobs.append({
                    'job_id': af3_job_id,
                    'binder_file': binder_file,
                    'eval_name': f"{job_name}_eval_{i}"
                })
                
            print(f"✅ Submitted {len(af3_jobs)} AF3 evaluation jobs")
            for job in af3_jobs:
                print(f"   {job['job_id']}: {job['binder_file'].name}")
        
        # Step 6: Provide monitoring commands
        print(f"\n📋 Monitoring Commands:")
        print(f"   RFdiffusion: squeue -j {rf_job_id}")
        if rf_status == "completed" and 'af3_jobs' in locals():
            for job in af3_jobs:
                print(f"   AF3 eval: squeue -j {job['job_id']}")
        
        print(f"\n🔍 Check results when complete:")
        print(f"   RFdiffusion output: {RFDIFFUSION_CONFIG['output_dir']}/binders_{job_name}_*.pdb")
        if rf_status == "completed" and 'af3_jobs' in locals():
            for job in af3_jobs:
                eval_name = job['eval_name']
                print(f"   AF3 results: python -c \"")
                print(f"from test_af3_binding import parse_af3_results")
                print(f"import json")
                print(f"r = parse_af3_results('{AF3_CONFIG['af3_path'] / AF3_CONFIG['output_dir']}', '{eval_name}')")
                print(f"print(json.dumps(r, indent=2))\"")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print(f"💡 Make sure target PDB file exists or provide structure prediction")
        return 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def extract_sequence_from_pdb(pdb_file: Path) -> str:
    """
    Extract amino acid sequence from PDB file.
    Simplified version - in practice would use BioPython.
    """
    # This is a placeholder - would need proper PDB parsing
    # For now, return a dummy sequence
    return "MKQHKAMIVALIVICITAVVAALVTRKDLCEVHIRTGQTEVAVFTAYESE"


if __name__ == "__main__":
    exit(main())