# Agent OS Framework

> LeaseHawk MVP Project
> Installed: 2025-09-20
> Version: 1.0.0

## Overview

Agent OS is installed and configured for the LeaseHawk MVP project - a GSA prospectus intelligence platform built with FastAPI and vanilla JavaScript.

## Directory Structure

```
.agent-os/
├── README.md                    # This file
├── CLAUDE.md                   # Project context for AI agents
├── config.yaml                 # Agent OS configuration
├── instructions/
│   └── core/
│       └── analyze-product.md  # Product analysis instruction
├── templates/
│   ├── task-template.md        # Task creation template
│   └── roadmap-template.md     # Roadmap planning template
├── specs/                      # Feature specifications (empty)
├── product/                    # Product documentation (empty)
└── data/                       # Project data files (empty)
```

## Quick Start

### Creating a New Spec
```
Create spec for: [feature-name]
Date folder: YYYY-MM-DD-[feature-name]
```

### Task Management
Use the task template in `.agent-os/templates/task-template.md` for consistent task creation and tracking.

### Roadmap Planning
Use the roadmap template in `.agent-os/templates/roadmap-template.md` for quarterly planning cycles.

## Configuration

The Agent OS is configured for:
- **Project Type:** Web Application (Real Estate Technology)
- **Architecture:** FastAPI + Vanilla JavaScript
- **Database:** PostgreSQL
- **Stage:** MVP Development

## Workflows Enabled

- ✅ Spec Creation with auto-task generation
- ✅ Task Tracking with markdown format
- ✅ Roadmap Management with quarterly planning
- ✅ Git Integration (manual commits)
- ✅ Documentation Management

## Agent Capabilities

- Product analysis and planning
- Specification creation and management
- Task tracking and management
- Code review assistance
- Architecture planning support
- Performance optimization guidance

## Usage Guidelines

1. **Specs**: Create date-based folders for all new features
2. **Tasks**: Link all tasks back to their originating specs
3. **Documentation**: Maintain product docs in `.agent-os/product/`
4. **Context**: Update CLAUDE.md when project context changes

## Project Context

LeaseHawk MVP is a GSA prospectus intelligence platform serving commercial real estate professionals. The platform provides automated tracking, analysis, and insights for government leasing opportunities.

**Key Focus Areas:**
- Real-time GSA data processing
- Market intelligence analysis
- User dashboard and reporting
- Scalable architecture design

## Support

For Agent OS framework questions or issues, refer to the core instructions and templates provided in this installation.