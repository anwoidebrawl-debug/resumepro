# NeurBot CS 1.6 - Human-Like AI for Counter-Strike 1.6

A powerful, human-like AI bot for Counter-Strike 1.6 that combines classical game integration with modern neural network decision-making.

## Architecture

```
CS 1.6 HLDS Server (ReHLDS + ReGameDLL_CS)
         │
    MetaMod Layer
         │
   NeurBot Plugin (C++)
   ├── Perception Module (game state extraction)
   ├── IPC Layer (shared memory + Unix sockets)  
   └── Action Executor (engine commands)
         │
   Neural Decision Engine (Python/PyTorch)
   ├── Tactical Controller (aim + movement, <1ms per tick)
   ├── Strategic Planner (economy, rotations, site picks)
   └── Humanization Layer (reaction time, aim smoothing, imperfections)
```

## Components

### 1. C++ MetaMod Plugin (`plugin/`)
Server-side bot that hooks into the Half-Life engine via MetaMod API:
- Extracts full game state every server tick (players, weapons, map, economy)
- Communicates with Python engine via shared memory IPC
- Executes actions through engine's `pfnRunPlayerMove`

### 2. Python Neural Engine (`python/neurbot/`)
Neural network-based decision making:
- **Tactical Controller**: MLP/Transformer for real-time aim and movement
- **Strategic Planner**: Transformer for macro decisions (economy, rotation, site selection)
- **Humanization**: Realistic imperfections (Bezier aim, reaction time jitter, spray noise)

### 3. Data Pipeline (`python/neurbot/data/`)
- Demo parser for GoldSrc .dem files
- Inverse dynamics model for action inference
- Dataset construction and preprocessing

### 4. Training (`python/neurbot/training/`)
- Behavioural cloning from human gameplay
- RL fine-tuning with self-play
- Adversarial humanization training

## Performance

Validated benchmarks (CPU, PyTorch 2.x):

| Metric | Value |
|--------|-------|
| MLP Inference Mean | 0.225 ms |
| MLP Inference P99 | 0.306 ms |
| Model Parameters (default MLP) | ~600K |
| Model Parameters (quick-train) | ~97K |
| Target Latency Budget | <15 ms |
| Test Suite | 59 tests, all passing |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ with PyTorch
- CMake 3.16+ and GCC/G++ (for plugin compilation)

### Setup

```bash
# 1. Install Python dependencies
pip install -e python/

# 2. Validate the full pipeline (synthetic data → train → inference → humanize)
python scripts/quick_train.py

# 3. Run tests
PYTHONPATH=python pytest python/tests/ -v

# 4. Start CS 1.6 server (requires HLDS installation)
cd docker && docker-compose up -d

# 5. Build the C++ plugin
cd plugin && mkdir build && cd build
cmake .. && make -j$(nproc)

# 6. Run the neural engine
python -m neurbot.engine --config config.yaml
```

### Training

```bash
# Collect data from demos
python scripts/collect_demos.py --input-dir data/demos/ --output data/datasets/tactical.h5

# Generate synthetic data for testing
python scripts/collect_demos.py --synthetic --n-samples 100000 --output data/datasets/synthetic.h5

# Train tactical controller (behavioural cloning)
python -m neurbot.training.train_tactical --dataset data/datasets/tactical.h5

# Train with synthetic data (quick validation)
python -m neurbot.training.train_tactical --synthetic --epochs 10

# Fine-tune with RL (dry-run without server)
python -m neurbot.training.train_rl --dry-run --total-steps 10000

# Fine-tune with RL (requires running HLDS server)
python -m neurbot.training.train_rl --checkpoint models/tactical_bc_best.pt
```

## Project Structure

```
cs16-ai-bot/
├── plugin/                    # C++ MetaMod plugin
│   ├── src/                   # Plugin source code
│   ├── include/               # Headers
│   ├── metamod/               # MetaMod SDK headers
│   ├── hlsdk/                 # Half-Life SDK headers
│   └── CMakeLists.txt
├── python/                    # Python neural engine
│   └── neurbot/
│       ├── models/            # Neural network architectures
│       ├── training/          # Training scripts
│       ├── data/              # Data pipeline
│       ├── ipc/               # IPC communication
│       ├── humanize/          # Humanization layer
│       └── engine.py          # Main engine entry point
├── docker/                    # Docker setup for HLDS
├── data/                      # Training data
├── scripts/                   # Utility scripts
├── tools/                     # Development tools
└── config.yaml                # Main configuration
```

## References

- [YaPB](https://github.com/yapb/yapb) - Foundation reference for CS 1.6 bot architecture
- [MLMove (Stanford/NVIDIA)](https://arxiv.org/abs/2408.13934) - Transformer-based movement for CS:GO
- [CS:GO Behavioural Cloning](https://arxiv.org/abs/2104.04258) - Large-scale imitation learning
- [Decision Transformer](https://arxiv.org/abs/2106.01345) - RL as sequence modeling
- [ReGameDLL_CS](https://github.com/rehlds/ReGameDLL_CS) - Reverse-engineered CS game DLL

## License

MIT License
