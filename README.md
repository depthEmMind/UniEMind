# UniEMind
[简体中文说明](readme_zh.md)
UniEMind is an open-source cognitive architecture for embodied robots.

It aims to build a unified robotic mind so that robots can **understand the world, themselves, objects, and tasks**, then reason about how to act autonomously in the physical world.

A robot needs to keep answering:

* What exists in the world?
* Where am I?
* What can I do?
* What objects are around me?
* What properties do these objects have?
* How can an object be manipulated?
* What is the current task?
* What should I do next?
* Did the previous action succeed?
* How should my understanding of the world be updated?



---

# 🌟 Vision

Enable everyone to build safe, stable, and fast-responding intelligent robots on UniEMind.

---

# 🐣 Update

2026/08/20, official release of UniEMind v0.1.

2026/08/19, UniEMind project created.

---

# 🧠 Core Idea

UniEMind is built around a **Unified Embodied Mind**.

It connects perception, world models, memory, cognition, planning, skills, and robot execution into one closed-loop system.

A robot should not only know how to execute an action. It should also understand:

```text
                    ┌───────────────┐
                    │     World     │
                    └───────┬───────┘
                            │
                       Perception
                            ↓
                    ┌───────────────┐
                    │  World Model  │
                    └───────┬───────┘
                            │
          ┌─────────────────┼─────────────────┐
          ↓                 ↓                 ↓
      Self Model       Object Model       Task Model
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ↓
                         Memory
                            ↓
                       Cognition
                            ↓
                        Planning
                            ↓
                         Skills
                            ↓
                       Execution
                            ↓
                       Feedback
                            ↓
                    World Model Update
```

This forms a continuous perception–cognition–action–learning loop.

---

# 🏗️ Architecture

The current architecture is organized around several cognitive layers.

```text
┌─────────────────────────────────────────────────────────┐
│                       UniEMind                          │
├─────────────────────────────────────────────────────────┤
│  Perception                                             │
│  ├── Vision                                             │
│  ├── Depth                                              │
│  ├── LiDAR / Radar                                      │
│  └── Robot State                                        │
├─────────────────────────────────────────────────────────┤
│  World Model                                            │
│  ├── Environment                                        │
│  ├── Objects                                            │
│  ├── Relations                                          │
│  ├── Events                                             │
│  └── Dynamic State                                      │
├─────────────────────────────────────────────────────────┤
│  Self Model                                             │
│  ├── Robot State                                        │
│  ├── Capabilities                                       │
│  ├── Skills                                             │
│  └── Constraints                                        │
├─────────────────────────────────────────────────────────┤
│  Memory                                                 │
│  ├── Working Memory                                     │
│  ├── Episodic Memory                                    │
│  ├── Semantic Memory                                    │
│  └── Skill Memory                                       │
├─────────────────────────────────────────────────────────┤
│  Cognition                                              │
│  ├── State Understanding                                │
│  ├── Reasoning                                          │
│  ├── Task Understanding                                 │
│  └── Decision Making                                    │
├─────────────────────────────────────────────────────────┤
│  Planning                                               │
│  ├── Task Planning                                      │
│  ├── Navigation Planning                                │
│  ├── Manipulation Planning                              │
│  └── Recovery Planning                                  │
├─────────────────────────────────────────────────────────┤
│  Skills                                                 │
│  ├── Navigation                                         │
│  ├── Search                                             │
│  ├── Grasping                                           │
│  ├── Manipulation                                       │
│  └── Tool Use                                           │
├─────────────────────────────────────────────────────────┤
│  Execution                                              │
│  ├── Robot Interface                                    │
│  ├── Simulation                                         │
│  └── Real Robot                                         │
├─────────────────────────────────────────────────────────┤
│  Reflection & Learning                                  │
│  ├── Execution Evaluation                               │
│  ├── Failure Analysis                                   │
│  ├── Skill Improvement                                  │
│  └── World Model Update                                 │
└─────────────────────────────────────────────────────────┘
```

The architecture is intentionally modular.

LLMs, VLMs, ROS 2, simulation engines, graph workflows, runtimes, and reinforcement learning algorithms should remain replaceable implementations. They do not define UniEMind itself.

---

# 🚀 Quick Start

Use the local conda environment `UniEMind`:

```bash
git clone https://github.com/depthEmMind/UniEMind.git
cd UniEMind

conda activate UniEMind
python -m pip install -r requirements-dev.txt
python -m pip install -e .

python examples/foundation.py
python examples/mvp_cup.py
python examples/mvp_pour.py
python examples/perception_pipeline.py
pytest
```

Dependencies:

* `requirements.txt`: runtime dependencies
* `requirements-dev.txt`: development and test dependencies (includes runtime dependencies)

The Foundation example loads a hardware-agnostic robot profile and publishes a versioned `RobotState` over the in-process `DataBus`. ROS 2 is kept behind replaceable transport and adapter interfaces.

The MVP examples run the two closed loops from the specification in simulation:

1. Find a cup → approach → grasp → verify
2. Navigate to the lab bench → find the cup → grasp → move to the sink → pour → verify

---

# 🔬 Research Directions

UniEMind is both an engineering platform and a research platform. Possible research directions include:

### World Models

* Structured world representation
* Dynamic world modeling
* Predictive world models
* Action-conditioned world models

### Embodied Cognition

* World understanding
* Self understanding
* Object understanding
* Affordance reasoning

### Memory

* Long-term robot memory
* Episodic memory
* Semantic memory
* Experience retrieval
* Memory consolidation

### Planning

* Long-horizon planning
* Hierarchical planning
* Task decomposition
* Recovery planning

### Skills

* Skill representation
* Skill composition
* Skill learning
* Skill reuse
* Skill transfer

### Learning

* Simulation-to-real (Sim2Real) learning
* Reinforcement learning
* Continual learning
* Self-improvement
* Experience-driven learning

---

# 📊 Evaluation

A long-term goal of UniEMind is to establish reproducible benchmarks for embodied cognition. Possible evaluation dimensions include:

```text
Task Success Rate
Planning Success Rate
Execution Success Rate
Navigation Success Rate
Manipulation Success Rate
Recovery Rate
Task Completion Time
Planning Latency
Skill Reuse
Generalization
Continual Learning
```

The goal is not only to show that a robot can complete a task, but also to measure:

> **How well does the robot understand, plan, act, recover, and learn?**

---

# 🧑‍💻 Development Philosophy

UniEMind follows several long-term engineering principles.

### 1. Modular

Core components should have clear interfaces and replaceable implementations.

### 2. Simulation First

New capabilities should be validated in simulation before deployment to physical robots.

### 3. Hardware Agnostic

The cognitive architecture should not depend on one specific robot platform.

### 4. Framework Agnostic

External frameworks should be replaceable through adapters and interfaces.

### 5. Testable

Important behaviors should have automated tests and regression benchmarks.

### 6. Reproducible

Experiments should be reproducible whenever possible.

### 7. Open

Research, implementation, benchmarks, and documentation should be shared openly whenever licensing and safety considerations allow.

### 8. Long-Term Maintainability

API stability, documentation, testing, code quality, and backward compatibility are first-class concerns.

---

# 🤝 Contributing

Contributions are welcome. You can contribute through:

* Bug reports
* Feature requests
* Documentation
* Tests
* New skills
* Simulation environments
* Robot interfaces
* Research ideas
* Algorithms
* Benchmarks
* Examples

Before submitting a pull request, please read:

* `CONTRIBUTING.md`
* Development documentation
* Existing issues and discussions

All contributions should preserve the modular architecture and long-term maintainability of the project.

---

# 🛡️ Security

If you discover a vulnerability that could affect physical robot safety, please do not disclose it through a public GitHub issue.

Follow the reporting process in `SECURITY.md`. Agent, planner, and LLM paths must not bypass the safety layer.

---

# 📜 License

UniEMind is released under the **Apache License 2.0**.

See `LICENSE` for details.

---

# 🌍 Community

UniEMind aims to become a long-term open-source community for researchers and engineers working on:

* Embodied AI
* Robotics
* World Models
* Robot Cognition
* Robot Learning
* Manipulation
* Navigation
* Autonomous Robots

Contributions, discussions, experiments, and research collaborations are welcome.

---

UniEMind aims for a future where robots are no longer systems that only execute predefined behaviors, but embodied agents that can continuously understand, reason, act, and learn in the real world.
