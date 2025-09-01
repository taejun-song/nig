# Protein Binder Generation with Reinforcement Learning

A reinforcement learning pipeline for generating protein binders using RFdiffusion and AlphaFold3 evaluation. The system learns optimal RFdiffusion parameters through RL to maximize binding quality as assessed by AlphaFold3 predictions.

## Overview

This project implements an end-to-end RL system that:

1. **Generates** protein binders using RFdiffusion with learned parameters
2. **Evaluates** binding quality using AlphaFold3 complex prediction  
3. **Learns** optimal generation parameters through PPO reinforcement learning
4. **Scales** to HPC environments with SLURM integration

## Architecture

### Core Components

- **RL Environment** (`src/environments/`): Protein binder generation environment
- **Policy Network** (`src/agents/`): Deep RL policy for parameter optimization
- **RFdiffusion Wrapper** (`src/models/rfdiffusion_wrapper.py`): Interface to RFdiffusion
- **AlphaFold3 Wrapper** (`src/models/af3_wrapper.py`): Interface to AlphaFold3
- **Reward Calculator** (`src/models/reward_calculator.py`): Multi-objective reward function
- **Training Loop** (`src/training/`): PPO training implementation

### Workflow

```
Target Protein → RL Agent → RFdiffusion Parameters → Generated Binders → AF3 Evaluation → Reward → Policy Update
```

## Installation

### Prerequisites

- Python 3.10+
- PyTorch 2.0+
- RFdiffusion installation
- AlphaFold3 setup
- SLURM (for HPC deployment)

### Setup

```bash
# Clone repository
git clone <repository-url>
cd protein-binder-rl

# Install with uv
uv sync

# Or install with pip
pip install -e .
```

### Dependencies

Core packages automatically installed:
- `torch` - Deep learning framework
- `gymnasium` - RL environment interface  
- `stable-baselines3` - RL algorithms
- `biopython` - Protein structure handling
- `wandb` - Experiment tracking
- `pyyaml` - Configuration management

## Configuration

### Training Configuration (`config/training_config.yaml`)

```yaml
# Environment setup
environment:
  target_proteins: ["data/targets/target1.pdb", ...]
  rfdiffusion_config:
    rfdiffusion_path: "/path/to/RFdiffusion"
    conda_env: "SE3nv"
  af3_config:
    input_dir: "/extdata3/OHC/alphafold3/af_input"
    output_dir: "/extdata3/OHC/alphafold3/af_output"

# RL training parameters
training:
  learning_rate: 3e-4
  total_steps: 1000000
  steps_per_update: 2048
```

### Action Space

The RL agent controls these RFdiffusion parameters:
- **Contig length**: Binder protein length (50-300 residues)
- **Num designs**: Batch size for generation (10-100)
- **Diffusion steps**: Sampling iterations (25-200) 
- **Sampling temperature**: Generation randomness (0.5-2.0)
- **Guidance scale**: Target conditioning strength (1.0-10.0)

### Reward Function

Multi-objective reward combining:
- **Interface quality** (40%): ipTM and pTM scores
- **Binding affinity** (30%): Interface contact count
- **Structural validity** (20%): Confidence and geometry
- **Diversity bonus** (10%): Novelty vs previous designs

## Usage

### Training

```bash
# Local training
python scripts/train_agent.py --config config/training_config.yaml

# SLURM training
sbatch slurm/train_rl.slurm

# Resume from checkpoint
python scripts/train_agent.py --checkpoint checkpoints/checkpoint_step_100000.pt
```

### Evaluation

```bash
# Standard evaluation
python scripts/evaluate_binders.py checkpoints/final_model.pt

# Target-specific evaluation  
python scripts/evaluate_binders.py checkpoints/final_model.pt \
    --target-specific --targets data/targets/specific_target.pdb

# Policy analysis
python scripts/evaluate_binders.py checkpoints/final_model.pt \
    --analyze-policy --analysis-steps 5000
```

### Binder Generation

```bash
# Generate binders for new target
python scripts/generate_binders.py \
    --model checkpoints/final_model.pt \
    --target data/targets/new_target.pdb \
    --num-designs 50 \
    --output generated_binders/
```

## HPC Integration

### SLURM Setup

The system integrates with SLURM for scalable execution:

1. **RFdiffusion jobs**: GPU nodes for protein generation
2. **AlphaFold3 jobs**: High-memory nodes for complex prediction
3. **Training jobs**: GPU nodes for RL training

### Resource Requirements

- **Training**: 1 GPU, 16 CPUs, 64GB RAM, 24h
- **RFdiffusion**: 1 GPU, 8 CPUs, 32GB RAM, 2h per batch
- **AlphaFold3**: 1 GPU, 16 CPUs, 64GB RAM, 4h per complex

## Results

### Success Metrics

- **Binding success rate**: % episodes with reward > 0.5
- **Interface quality**: Average ipTM scores across designs
- **Generation efficiency**: Successful binders per compute hour

### Expected Performance

After training convergence (~500k steps):
- Success rate: 50-70% depending on target difficulty
- High-quality binders (ipTM > 0.8): 10-20% of successful episodes
- Parameter optimization: 2-3x improvement vs random sampling

## Monitoring

### Weights & Biases Integration

```bash
# Enable logging
export WANDB_PROJECT="protein-binder-rl" 
export WANDB_ENTITY="your-entity"

# Metrics tracked:
# - Episode rewards and success rates
# - Policy loss and entropy
# - Generated binder statistics  
# - Resource utilization
```

### Local Monitoring

Training logs saved to:
- `training.log`: Console output
- `checkpoints/`: Model checkpoints
- `data/training_data/`: Episode statistics

## Customization

### Custom Reward Functions

Extend `RewardCalculator` class:

```python
class CustomRewardCalculator(RewardCalculator):
    def _calculate_custom_reward(self, results):
        # Your custom reward logic
        return reward
```

### Custom Action Spaces

Modify `RFdiffusionActionSpace`:

```python
# Add new parameters
self.new_parameter_options = [val1, val2, val3]

# Update action conversion
def create_parameter_dict(self, action):
    params['new_parameter'] = str(action["new_parameter"])
    return params
```

### Multi-Target Training

Enable in config for better generalization:

```yaml
environment:
  multi_target: true
  target_proteins: [list of diverse targets]
```

## Troubleshooting

### Common Issues

1. **SLURM jobs failing**: Check node availability and resource limits
2. **AF3 timeouts**: Increase timeout or reduce batch sizes
3. **Low success rates**: Adjust reward weights or target difficulty
4. **Memory errors**: Reduce batch size or sequence lengths

### Debug Mode

```bash
python scripts/train_agent.py --config config/training_config.yaml --log-level DEBUG --dry-run
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality  
4. Submit pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Citation

If you use this code in your research, please cite:

```bibtex
@software{protein_binder_rl,
  title={Protein Binder Generation with Reinforcement Learning},
  author={Your Name},
  year={2024},
  url={https://github.com/your-username/protein-binder-rl}
}
```
