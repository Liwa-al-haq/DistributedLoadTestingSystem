# Distributed Load Testing System - Big Data Project 2023, PES University

## Introduction
This project aims to design and build a distributed load-testing system that coordinates multiple driver nodes to execute highly concurrent, high-throughput load tests on web servers. It utilizes Kafka for communication.

## Architecture
- Orchestrator and Driver Nodes as separate processes
- Communication via Kafka
- Scalable with a minimum of 3 and a maximum of 9 nodes
- Detailed architecture diagram: ![Architecture Diagram](https://imgur.com/qIzBdCP.png)  

## Features
- Kafka as a central communication hub
- Unique ID registration for nodes
- Tsunami and Avalanche testing methodologies
- Real-time observability and metrics store

## Installation
1. Clone the repo: `git clone https://github.com/Liwa-al-haq/DistributedLoadTestingSystem`
2. Install dependencies (details here)
3. Configure Kafka and other services (instructions)

## Usage
- Use Kafka IP and Orchestrator IP as command-line arguments
- Run Orchestrator and Driver Nodes (commands and examples)
- Configure test parameters (details)

## Test Types
- **Tsunami Testing**: Set delay intervals between requests
- **Avalanche Testing**: First-come, first-serve request processing

## License
This project is under the [MIT License](LICENSE.md).

## Support
For support and inquiries, [open an issue](https://github.com/Liwa-al-haq/DistributedLoadTestingSystem/issues) in this repository.

---


