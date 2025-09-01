#!/usr/bin/env python3
"""
AF3 binding test with separated config and input data.
Usage: python run_binding_test.py [input_file]
"""

import sys
import argparse

from test_af3_binding import create_af3_input, submit_af3_job, check_job_status, parse_af3_results
from config import AF3_CONFIG
from input_loader import load_test_inputs


def main():
    """Run AF3 binding test with flexible input loading."""
    
    parser = argparse.ArgumentParser(description='Run AF3 protein binding test')
    parser.add_argument('input_file', nargs='?', 
                       default='test_data/example_input.txt',
                       help='Input configuration file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Parse inputs without submitting job')
    
    args = parser.parse_args()
    
    print("🧬 AlphaFold3 Protein Binding Test (v2)")
    print("=" * 50)
    
    try:
        # Load input data
        print(f"📂 Loading inputs from: {args.input_file}")
        inputs = load_test_inputs(args.input_file)
        
        target = inputs['target']
        binder = inputs['binder']
        job_name = inputs['job_name']
        
        # Display loaded data
        print(f"\n🎯 Target: {target['name']}")
        print(f"   Source: {target['source']}")
        print(f"   Length: {target['length']} residues")
        print(f"   Sequence: {target['sequence'][:50]}...")
        
        print(f"\n🔗 Binder: {binder['name']}")
        print(f"   Source: {binder['source']}")
        print(f"   Length: {binder['length']} residues") 
        print(f"   Sequence: {binder['sequence'][:50]}...")
        
        print(f"\n🏷️  Job: {job_name}")
        
        if args.dry_run:
            print("\n✅ Dry run completed - inputs loaded successfully")
            return 0
        
        # Create AF3 input
        print(f"\n📝 Creating AF3 input...")
        af3_input = create_af3_input(
            target['sequence'], 
            binder['sequence'], 
            job_name
        )
        
        # Submit job
        print(f"🚀 Submitting to SLURM...")
        job_id = submit_af3_job(
            AF3_CONFIG["af3_path"]
            AF3_CONFIG["input_dir"],
            AF3_CONFIG["output_dir"],
            af3_input,
            AF3_CONFIG.get("nodelist")
        )
        
        print(f"✅ Job submitted: {job_id}")
        
        # Quick status check
        status = check_job_status(job_id)
        print(f"📊 Status: {status}")
        
        # Provide next steps
        print(f"\n📋 Monitoring:")
        print(f"   Job status: squeue -j {job_id}")
        print(f"   Cancel job: scancel {job_id}")
        print(f"   View logs: tail -f {AF3_CONFIG['output_dir']}/logs/{job_name}*.out")
        
        print(f"\n🔍 Parse results when complete:")
        print(f"   python -c \"")
        print(f"from test_af3_binding import parse_af3_results")
        print(f"import json")
        print(f"r = parse_af3_results('{AF3_CONFIG['output_dir']}', '{job_name}')")
        print(f"print(json.dumps(r, indent=2))\"")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print(f"💡 Create your input file based on: test_data/example_input.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())