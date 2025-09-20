# CLAUDE Context File

> Project: LeaseHawk MVP
> Agent OS Version: 1.0.0
> Last Updated: 2025-09-20

## Project Overview

LeaseHawk MVP is a GSA prospectus intelligence platform that provides real estate professionals with comprehensive analysis and insights into government leasing opportunities. The platform helps users track, analyze, and respond to GSA prospectus announcements more effectively.

## Architecture

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **API Design:** RESTful APIs with OpenAPI documentation
- **Authentication:** JWT-based authentication
- **Data Processing:** Automated GSA data ingestion and analysis

### Frontend
- **Framework:** Vanilla JavaScript
- **Architecture:** Single Page Application (SPA)
- **Styling:** CSS3 with modern responsive design
- **Build Process:** Modern JavaScript bundling and optimization

## Key Features

1. **GSA Prospectus Tracking**
   - Real-time prospectus monitoring
   - Automated data collection and parsing
   - Historical prospectus database

2. **Intelligence Analysis**
   - Market trend analysis
   - Competitive landscape insights
   - Opportunity scoring and ranking

3. **User Dashboard**
   - Personalized opportunity tracking
   - Custom alerts and notifications
   - Performance analytics

4. **Reporting & Export**
   - Comprehensive reporting tools
   - Data export capabilities
   - Integration-ready APIs

## Development Workflow

### Agent OS Integration
- Specs managed in `.agent-os/specs/` with date-based folders
- Product documentation in `.agent-os/product/`
- Task tracking via Agent OS templates
- Automated workflow management

### Code Organization
- Backend: `/api/` directory with modular FastAPI structure
- Frontend: `/web/` directory with component-based architecture
- Database: `/migrations/` for schema versioning
- Tests: `/tests/` with comprehensive coverage

### Quality Standards
- Type hints for all Python code
- ESLint for JavaScript code quality
- Comprehensive test coverage (>80%)
- API documentation with OpenAPI/Swagger

## Target Users

1. **Commercial Real Estate Brokers**
   - GSA opportunity identification
   - Market intelligence gathering
   - Competitive analysis

2. **Property Developers**
   - Site selection assistance
   - Market timing insights
   - Investment opportunity evaluation

3. **Government Relations Teams**
   - Prospectus tracking and analysis
   - Compliance monitoring
   - Strategic planning support

## Technical Constraints

- Must handle large datasets (10k+ prospectus records)
- Real-time data processing requirements
- High availability (99.9% uptime target)
- Secure handling of government data
- Scalable architecture for future growth

## Agent OS Usage Patterns

### Spec Creation
Use the analyze-product instruction to understand context before creating new specs. Follow the date-based folder naming convention (YYYY-MM-DD-feature-name).

### Task Management
Leverage task templates for consistent tracking. All tasks should link back to their originating specs and include clear acceptance criteria.

### Roadmap Planning
Use quarterly planning cycles with weekly review checkpoints. Focus on user value delivery and technical debt management.

## Development Priorities

1. **Core MVP Features** - Essential functionality for launch
2. **Data Quality** - Accurate and timely GSA data processing
3. **User Experience** - Intuitive interface and workflows
4. **Performance** - Fast load times and responsive interactions
5. **Scalability** - Architecture ready for growth

## Context for AI Agents

When working on LeaseHawk MVP:
- Always consider the real estate domain expertise required
- Prioritize data accuracy and compliance with government data handling
- Focus on user workflows that save time and provide insights
- Maintain high code quality standards for long-term maintainability
- Consider scalability implications of all architectural decisions

## Project Status

Currently in MVP development phase with focus on core functionality delivery. The platform is being built to validate product-market fit in the government real estate intelligence space.