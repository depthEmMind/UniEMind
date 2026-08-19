# UniEMind
UniEMind — A Unified Embodied Mind for Robots


UniEMind is an open-source cognitive architecture for embodied robots.

The goal of UniEMind is to build a unified robotic mind that enables robots to **understand the world, understand themselves, understand objects and tasks, reason about what they can do, and act autonomously in the physical world**.

UniEMind aims to bridge the gap between perception, world models, memory, cognition, planning, skills, and robotic execution into a unified closed-loop system.

---

## 🌟 Vision

Today's robotic systems are often built as a collection of independent modules:

```text
Perception
    ↓
Planning
    ↓
Control
```

While this architecture works well for predefined tasks, it is difficult for robots to handle open-ended environments where they need to understand:

* What exists in the world?
* Where am I?
* What can I do?
* What objects are around me?
* What are the properties of these objects?
* How can an object be manipulated?
* What is the current task?
* What should I do next?
* Did my previous action succeed?
* How should my understanding of the world be updated?

UniEMind aims to move toward a more unified cognitive architecture:

```text
                         UniEMind
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
      World Model        Self Model       Object Model
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                         Memory
                            │
                        Cognition
                            │
                        Planning
                            │
                         Skills
                            │
                        Execution
                            │
                       Reflection
                            │
                        Learning
                            │
                            └──────────────→ World
```

The long-term vision is to enable robots to continuously perceive, understand, reason, act, learn, and update their internal models of the world.

---

# 🧠 Core Idea

UniEMind is built around the concept of a **Unified Embodied Mind**.

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

This creates a continuous perception–cognition–action–learning loop.

---

# 🎯 Goals

UniEMind aims to provide a general-purpose foundation for embodied intelligence.

### World Understanding

Enable robots to build and maintain an internal representation of the environment.

```text
Environment
├── Objects
├── Locations
├── Spatial Relationships
├── Semantic Relationships
├── Dynamic States
└── Events
```

### Self Understanding

Enable robots to understand their own state and capabilities.

```text
Self
├── Pose
├── Configuration
├── Capabilities
├── Available Skills
├── Current State
├── Constraints
└── Limitations
```

### Object Understanding

Enable robots to reason about objects beyond simple recognition.

```text
Object
├── Identity
├── Geometry
├── Physical Properties
├── Semantic Properties
├── State
├── Affordances
└── Interaction Methods
```

For example, understanding a cup should not stop at:

```text
"This is a cup."
```

The robot should gradually be able to reason:

```text
Cup
├── Can be grasped
├── Can be lifted
├── Can be moved
├── Can contain liquid
├── Can be placed
└── Can be used for pouring
```

This concept of **affordance-aware understanding** is an important direction of UniEMind.

---

# 🏗️ Architecture

The initial architecture is designed around several major cognitive layers.

```text
┌─────────────────────────────────────────────────────────┐
│                       UniEMind                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Perception                                             │
│  ├── Vision                                             │
│  ├── Depth                                              │
│  ├── LiDAR / Radar                                      │
│  └── Robot State                                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  World Model                                            │
│  ├── Environment                                        │
│  ├── Objects                                            │
│  ├── Relations                                          │
│  ├── Events                                             │
│  └── Dynamic State                                      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Self Model                                             │
│  ├── Robot State                                        │
│  ├── Capabilities                                       │
│  ├── Skills                                             │
│  └── Constraints                                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Memory                                                 │
│  ├── Working Memory                                    │
│  ├── Episodic Memory                                   │
│  ├── Semantic Memory                                   │
│  └── Skill Memory                                      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Cognition                                              │
│  ├── State Understanding                                │
│  ├── Reasoning                                          │
│  ├── Task Understanding                                 │
│  └── Decision Making                                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Planning                                               │
│  ├── Task Planning                                      │
│  ├── Navigation Planning                                │
│  ├── Manipulation Planning                              │
│  └── Recovery Planning                                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Skills                                                 │
│  ├── Navigation                                         │
│  ├── Search                                             │
│  ├── Grasping                                           │
│  ├── Manipulation                                       │
│  └── Tool Use                                           │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Execution                                              │
│  ├── Robot Interface                                    │
│  ├── Simulation                                         │
│  └── Real Robot                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Reflection & Learning                                  │
│  ├── Execution Evaluation                               │
│  ├── Failure Analysis                                   │
│  ├── Skill Improvement                                  │
│  └── World Model Update                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

The architecture is intentionally modular.

Specific technologies such as LLMs, VLMs, ROS 2, simulation engines, graph frameworks, runtime systems, and reinforcement learning algorithms should remain replaceable implementation components rather than defining the identity of UniEMind itself.

---

# 🔄 Cognitive Loop

The long-term execution loop of UniEMind is:

```text
Observe
   ↓
Understand
   ↓
Remember
   ↓
Reason
   ↓
Plan
   ↓
Act
   ↓
Verify
   ↓
Reflect
   ↓
Learn
   ↓
Update World Model
   │
   └──────────────→ Observe
```

This closed loop is one of the central principles of UniEMind.

The robot should not treat an action as the end of a task.

Instead:

> **Every action changes the world, and the resulting state should update the robot's internal understanding of the world.**

---

# 🧩 Core Concepts

## World Model

The World Model represents the robot's current understanding of the external environment.

It may include:

* Objects
* Object states
* Spatial relationships
* Semantic relationships
* Environment state
* Dynamic changes
* Events
* Task-relevant information

The World Model should support both:

```text
"What is the world like now?"
```

and eventually:

```text
"What will happen if I perform this action?"
```

---

## Self Model

The Self Model represents the robot itself.

The robot should know:

```text
Where am I?

What is my current state?

What can I do?

Which skills do I have?

What are my limitations?

What is currently being executed?
```

This allows planning to consider the robot's actual capabilities rather than assuming unlimited ability.

---

## Object Model

The Object Model describes objects and their interaction possibilities.

For example:

```text
Object
│
├── Identity
├── Geometry
├── State
├── Physical Properties
├── Semantic Properties
├── Affordances
└── Skills Required for Interaction
```

The long-term goal is to move from:

```text
Object Recognition
```

toward:

```text
Object Understanding
```

and eventually:

```text
Object Interaction Reasoning
```

---

## Memory

UniEMind uses a layered memory architecture.

### Working Memory

Information required for the current task.

### Episodic Memory

Past experiences and completed episodes.

### Semantic Memory

General knowledge about the world.

### Skill Memory

Knowledge about how actions and skills can be performed.

The long-term goal is for memory to support both reasoning and continuous learning.

---

# 🤖 Skills

Skills are reusable capabilities that allow UniEMind to interact with the physical world.

Examples:

```text
Navigation
├── MoveTo
├── Follow
└── AvoidObstacle

Search
├── SearchObject
├── SearchLocation
└── VerifyObject

Manipulation
├── Reach
├── Grasp
├── Lift
├── Move
├── Place
└── Pour
```

A high-level task should be decomposable into reusable skills.

For example:

```text
Task:
"Bring the cup to the sink."

        ↓

NavigateTo(Table)
        ↓
Search(Cup)
        ↓
Grasp(Cup)
        ↓
NavigateTo(Sink)
        ↓
Place(Cup)
        ↓
Verify()
```

This separation between **cognition, planning, and executable skills** is a fundamental design principle.

---

# 🧪 Simulation First

UniEMind is designed to support both simulation and real-world robots.

```text
                    UniEMind
                       │
              ┌────────┴────────┐
              ↓                 ↓
         Simulation         Real Robot
              │                 │
       ┌──────┴──────┐          │
       ↓             ↓          ↓
   Isaac Sim       MuJoCo      ROS 2
```

Simulation provides a safe and scalable environment for:

* Algorithm development
* Regression testing
* Skill learning
* Reinforcement learning
* World model evaluation
* Long-horizon task evaluation

The same cognitive architecture should ideally be capable of operating in both simulated and physical environments.

---

# 🚧 Project Status

> **UniEMind is currently in early-stage development.**

The project is being developed as a long-term open-source research and engineering platform.

### Current

* [ ] Project architecture
* [ ] Core runtime
* [ ] State representation
* [ ] Message system
* [ ] Working memory
* [ ] Skill abstraction
* [ ] Simulation interface

### In Progress

* [ ] World Model
* [ ] Self Model
* [ ] Object Model
* [ ] Long-term Memory
* [ ] Task Planning
* [ ] Navigation
* [ ] Manipulation

### Planned

* [ ] Affordance reasoning
* [ ] World model prediction
* [ ] Skill learning
* [ ] Continual learning
* [ ] Reflection and self-improvement
* [ ] Long-horizon task execution
* [ ] Real robot deployment
* [ ] Standardized benchmarks

The roadmap will evolve as the architecture and research directions mature.

---

# 🗺️ Roadmap

## Phase 0 — Foundation

* [ ] Define core architecture
* [ ] Define state and message protocols
* [ ] Establish runtime abstraction
* [ ] Establish skill interface
* [ ] Establish memory interface
* [ ] Establish testing infrastructure

## Phase 1 — Cognitive Core

* [ ] World Model
* [ ] Self Model
* [ ] Object Model
* [ ] Working Memory
* [ ] Episodic Memory
* [ ] Semantic Memory
* [ ] Basic cognition loop

## Phase 2 — Action

* [ ] Task planning
* [ ] Navigation
* [ ] Object search
* [ ] Grasping
* [ ] Manipulation
* [ ] Execution verification
* [ ] Recovery behaviors

## Phase 3 — Learning

* [ ] Experience collection
* [ ] Reflection
* [ ] Skill improvement
* [ ] Skill learning
* [ ] World model learning
* [ ] Simulation-based training

## Phase 4 — Embodied Intelligence

* [ ] Long-horizon tasks
* [ ] Open-world interaction
* [ ] Continual learning
* [ ] Real robot deployment
* [ ] Benchmarking
* [ ] Multi-robot support

---

# 🚀 Quick Start

> Quick Start will be added once the initial runtime API is stable.

The intended usage is:

```bash
git clone https://github.com/depthEmMind/UniEMind.git

cd UniEMind

pip install -e .

python examples/hello_world.py
```

The first examples will focus on demonstrating the complete cognitive loop in simulation before expanding to real robots.

---

# 📁 Repository Structure

The repository is expected to evolve toward the following structure:

```text
UniEMind/
│
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS
│
├── docs/
│   ├── architecture/
│   ├── concepts/
│   ├── getting-started/
│   ├── tutorials/
│   ├── api/
│   └── development/
│
├── src/
│   └── uniemind/
│       ├── core/
│       ├── perception/
│       ├── world_model/
│       ├── self_model/
│       ├── memory/
│       ├── cognition/
│       ├── planning/
│       ├── skills/
│       ├── execution/
│       └── learning/
│
├── examples/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── regression/
│
├── benchmarks/
│
├── scripts/
│
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
└── pyproject.toml
```

The exact structure may change as the project evolves.

---

# 🔬 Research Directions

UniEMind is intended to serve as both an engineering platform and a research platform.

Potential research directions include:

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

* Simulation-to-real learning
* Reinforcement learning
* Continual learning
* Self-improvement
* Experience-driven learning

---

# 📊 Benchmark

A long-term goal of UniEMind is to establish reproducible benchmarks for embodied cognition.

Potential evaluation dimensions include:

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

The goal is not only to demonstrate that a robot can complete a task, but also to measure:

> **How well does the robot understand, plan, act, recover, and learn?**

---

# 🧑‍💻 Development Philosophy

UniEMind follows several long-term engineering principles.

### 1. Modular

Core components should have clear interfaces and replaceable implementations.

### 2. Simulation First

New capabilities should ideally be testable in simulation before deployment to physical robots.

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

Contributions are welcome.

You can contribute through:

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

If you discover a security vulnerability, please do not disclose it publicly through a GitHub issue.

Please follow the security reporting process described in `SECURITY.md`.

---

# 📜 License

UniEMind is intended to be released under the **Apache License 2.0**.

See `LICENSE` for details.

---

# 🌍 Community

UniEMind is intended to become a long-term open-source community for researchers and engineers working on:

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

# ⭐ Vision for the Future

The long-term goal of UniEMind is not simply to make robots execute more complex programs.

The goal is to build robots that can progressively develop an internal understanding of:

```text
        The World
            │
            ↓
       What exists?
            │
            ↓
        Who am I?
            │
            ↓
       What can I do?
            │
            ↓
     What can objects do?
            │
            ↓
       What is my goal?
            │
            ↓
      What should I do?
            │
            ↓
       Did it work?
            │
            ↓
      What did I learn?
            │
            ↓
    How should I update
       my world model?
            │
            └───────────────→ The World
```

UniEMind aims to move toward a future where robots are not merely systems that execute predefined behaviors, but **embodied agents capable of continuously understanding, reasoning, acting, and learning in the real world.**
