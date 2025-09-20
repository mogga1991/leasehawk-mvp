# Workflow Management Instruction

> Agent OS Core Instruction
> Created: 2025-09-20
> Version: 1.0.0

## Purpose

This instruction defines the development workflow management patterns for the LeaseHawk MVP project, ensuring consistent processes across spec creation, task management, and delivery cycles.

## Workflow Types

### 1. Spec-Driven Development

**Process Flow:**
1. **Analysis** → Use analyze-product.md to understand context
2. **Specification** → Create comprehensive spec with technical details
3. **Task Breakdown** → Generate actionable tasks from spec requirements
4. **Implementation** → Execute tasks with clear acceptance criteria
5. **Review** → Validate delivery against spec requirements

**Naming Convention:**
- Specs: `YYYY-MM-DD-[feature-name]/`
- Tasks: `[SPEC-ID]-[task-number]-[task-name]`
- Branches: `feature/[spec-id]-[task-name]`

### 2. Sprint Planning

**Cycle:** 2-week sprints with weekly check-ins

**Sprint Structure:**
- **Planning (Day 1):** Spec review, task prioritization, capacity planning
- **Daily Standups:** Progress updates, blocker identification
- **Mid-sprint Review (Day 7):** Progress assessment, scope adjustments
- **Sprint Review (Day 14):** Demo, stakeholder feedback
- **Retrospective (Day 14):** Process improvements, lessons learned

### 3. Quality Gates

**Development Gates:**
- [ ] Code review completed
- [ ] Tests written and passing (>80% coverage)
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Security review passed

**Release Gates:**
- [ ] Feature complete per spec
- [ ] User acceptance testing passed
- [ ] Staging deployment validated
- [ ] Rollback plan documented
- [ ] Monitoring and alerts configured

### 4. Task Lifecycle

**States:**
- **Backlog** → Identified but not yet planned
- **Ready** → Spec complete, ready for implementation
- **In Progress** → Actively being worked on
- **Review** → Code complete, under review
- **Testing** → In QA validation
- **Done** → Deployed and verified

**Transitions:**
- Automatic progression with completion criteria
- Manual override for exception handling
- Clear ownership at each stage

## Integration Patterns

### Git Workflow
```
main (production)
├── develop (integration)
│   ├── feature/2025-01-15-user-auth-login
│   ├── feature/2025-01-15-user-auth-registration
│   └── hotfix/critical-bug-fix
```

### Documentation Updates
- Specs updated when requirements change
- CLAUDE.md updated when project context evolves
- Task templates updated based on retrospective feedback

### Continuous Integration
- Automated testing on all pull requests
- Code quality checks and linting
- Security scanning for dependencies
- Performance regression testing

## Metrics and Tracking

### Velocity Metrics
- Story points completed per sprint
- Task completion rate
- Bug discovery rate
- Technical debt accumulation

### Quality Metrics
- Code coverage percentage
- Bug escape rate
- Performance benchmarks
- User satisfaction scores

### Process Metrics
- Sprint goal achievement rate
- Spec accuracy (requirements churn)
- Time from spec to delivery
- Retrospective action item completion

## Escalation Procedures

### Technical Blockers
1. **Developer Level:** Immediate team discussion
2. **Team Level:** Technical lead consultation
3. **Project Level:** Architecture review session
4. **Organizational Level:** External expertise engagement

### Scope Changes
1. **Minor Changes:** Update spec and communicate
2. **Moderate Changes:** Stakeholder review and approval
3. **Major Changes:** Full spec revision and re-planning
4. **Scope Creep:** Formal change control process

## Tool Integration

### Project Management
- Task tracking via Agent OS templates
- Roadmap management with quarterly reviews
- Progress visualization and reporting

### Development Tools
- Code repository integration
- Automated testing and deployment
- Performance monitoring and alerting

### Communication
- Regular stakeholder updates
- Team collaboration platforms
- Documentation and knowledge sharing

## Best Practices

1. **Spec First:** Always start with clear requirements
2. **Small Batches:** Break work into manageable pieces
3. **Continuous Feedback:** Regular stakeholder engagement
4. **Quality Focus:** Don't compromise on testing and review
5. **Documentation:** Keep context and decisions recorded
6. **Automation:** Reduce manual overhead where possible
7. **Retrospection:** Continuously improve processes