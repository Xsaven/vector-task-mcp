---
name: init-brain
description: "Comprehensive Brain.php initialization - scans project, analyzes docs/code, generates optimized configuration"
---

<command>
<meta>
<id>init-brain</id>
<description>Comprehensive Brain.php initialization - scans project, analyzes docs/code, generates optimized configuration</description>
</meta>
<purpose>Discovers project context, analyzes docs/code, researches best practices, generates optimized .brain/node/Brain.php with project-specific guidelines, stores insights to vector memory</purpose>
<purpose>The InitBrain command automates the initialization of Brain.php configuration based on project context.</purpose>
<iron_rules>
<rule id="temporal-context-first" severity="critical">
<text>Temporal context MUST be initialized first: Bash('date +"%Y-%m-%d %H:%M:%S %Z"')</text>
<why>Ensures all research and recommendations reflect current year best practices</why>
<on_violation>Missing temporal context leads to outdated recommendations</on_violation>
</rule>
<rule id="parallel-research" severity="critical">
<text>Execute independent research tasks in parallel for efficiency</text>
<why>Maximizes throughput and minimizes total execution time</why>
<on_violation>Sequential execution wastes time on independent tasks</on_violation>
</rule>
<rule id="evidence-based" severity="critical">
<text>All Brain.php guidelines must be backed by discovered project evidence</text>
<why>Prevents generic configurations that do not match project reality</why>
<on_violation>Speculation leads to misaligned Brain behavior</on_violation>
</rule>
<rule id="preserve-existing" severity="critical">
<text>Backup existing .brain/node/Brain.php before modifications</text>
<why>Prevents data loss and enables rollback if needed</why>
<on_violation>Data loss and inability to recover previous configuration</on_violation>
</rule>
<rule id="vector-memory-storage" severity="high">
<text>Store all significant insights to vector memory with semantic tags</text>
<why>Enables future context retrieval and knowledge accumulation</why>
<on_violation>Knowledge loss and inability to leverage past discoveries</on_violation>
</rule>
<rule id="preserve-variation" severity="critical">
<text>NEVER modify or replace existing #[Includes()] attributes on Brain.php Brain already has a Variation (e.g., Scrutinizer) - preserve it Standard includes from vendor/jarvis-brain/core/src/Includes are OFF LIMITS</text>
<why>Variations are pre-configured brain personalities with carefully tuned includes</why>
<on_violation>Modifying Variation breaks brain coherence and predefined behavior</on_violation>
</rule>
<rule id="project-includes-only" severity="critical">
<text>Only analyze and suggest includes from .brain/node/Includes/ FORBIDDEN: vendor/jarvis-brain/core/src/Includes/* modifications FORBIDDEN: Replacing or adding standard includes to Brain.php</text>
<why>Standard includes are managed by Variations, not by init process</why>
<on_violation>Standard includes are bundled with Variation - do not duplicate or override</on_violation>
</rule>
</iron_rules>
<guidelines>
<guideline id="phase1-temporal-context">
GOAL(Initialize temporal awareness for all subsequent operations)
<example>
<phase name="1">Bash(date +"%Y-%m-%d") → [STORE-AS($CURRENT_DATE)] → END-Bash</phase>
<phase name="2">Bash(date +"%Y") → [STORE-AS($CURRENT_YEAR)] → END-Bash</phase>
<phase name="3">Bash(date +"%Y-%m-%d %H:%M:%S %Z") → [STORE-AS($TIMESTAMP)] → END-Bash</phase>
<phase name="4">
VERIFY-SUCCESS(All temporal variables set)
NOTE(This ensures all research queries include current year for up-to-date results)
</phase>
</example>
</guideline>
<guideline id="phase2-project-discovery">
GOAL(Discover project structure, technology stack, and patterns)
<example>
NOTE(Execute all discovery tasks in parallel for efficiency)
<phase name="parallel-discovery-tasks">TASK → [(Task(@agent-explore, 'TASK → [(Check if .docs/ directory exists using Glob + Use Glob("**/.docs/**/*.md") to find documentation files + IF(.docs/ exists) → THEN → [Read all .md files from .docs/ directory → Extract: project goals, requirements, architecture decisions, domain terminology → STORE-AS($DOCS_CONTENT)] → ELSE → [No .docs/ found → STORE-AS($DOCS_CONTENT = \'null\')] → END-IF)] → END-TASK', 'CONTEXT(Documentation discovery for project context)') + Task(@agent-explore, 'TASK → [(Analyze project root structure + Use Glob to find: composer.json, package.json, .env.example, README.md + Read key dependency files + Identify project type (Laravel, Node.js, hybrid, etc.) + Extract technology stack from dependency files + STORE-AS($PROJECT_TYPE) + STORE-AS($TECH_STACK = \'{languages: [...], frameworks: [...], packages: [...], services: [...]}\'))] → END-TASK', 'CONTEXT(Codebase structure and tech stack analysis)') + Task(@agent-explore, 'TASK → [(Scan for architectural patterns + Use Glob to find PHP/JS/TS files in app/ and src/ directories + Analyze code structure and organization + Identify: MVC, DDD, CQRS, microservices, monolith, etc. + Detect design patterns: repositories, services, factories, observers, etc. + Find coding conventions: naming, structure, organization + STORE-AS($ARCHITECTURE_PATTERNS = \'{architecture_style: "...", design_patterns: [...], conventions: [...]}\'))] → END-TASK', 'CONTEXT(Architecture pattern discovery)') + Task(@agent-explore, 'TASK → [(Read(\'.brain/node/Brain.php\') + Extract current includes and configuration + Identify what is already configured + STORE-AS($CURRENT_BRAIN_CONFIG = \'{includes: [...], custom_rules: [...], custom_guidelines: [...]}\'))] → END-TASK', 'CONTEXT(Current Brain configuration analysis)'))] → END-TASK</phase>
<phase name="2">VERIFY-SUCCESS(All discovery tasks completed)</phase>
<phase name="3">STORE-AS($PROJECT_CONTEXT = 'Merged results from all discovery tasks')</phase>
</example>
</guideline>
<guideline id="phase3-documentation-analysis">
GOAL(Deep analysis of project documentation to extract requirements and domain knowledge)
<example>
<phase name="1">IF(STORE-GET($DOCS_CONTENT) !== null) → THEN → [Task(@agent-documentation-master, 'INPUT(STORE-GET($DOCS_CONTENT))', 'TASK → [(Analyze all documentation files + Extract: project goals, requirements, constraints, domain concepts + Identify: key workflows, business rules, integration points + Map documentation to Brain configuration needs + Suggest: custom includes, rules, guidelines based on docs)] → END-TASK', 'OUTPUT({goals: [...], requirements: [...], domain_concepts: [...], suggested_config: {...}})') → STORE-AS($DOCS_ANALYSIS)] → ELSE → [No documentation found - will rely on codebase analysis only → STORE-AS($DOCS_ANALYSIS = 'null')] → END-IF</phase>
</example>
</guideline>
<guideline id="phase4-best-practices-research">
GOAL(Research current best practices for discovered technologies)
<example>
NOTE(Execute research tasks in parallel for each major technology)
<phase name="1">FOREACH(STORE-GET($TECH_STACK.frameworks)) → [Task(@agent-web-research-master, 'INPUT(STORE-GET($CURRENT_YEAR))', 'TASK → [(WebSearch({framework} best practices {current_year}) + WebSearch({framework} architectural patterns {current_year}) + WebSearch({framework} code organization {current_year}) + Extract: recommended patterns, conventions, anti-patterns + Identify: framework-specific Brain configuration needs)] → END-TASK', 'OUTPUT({framework: "...", best_practices: [...], recommendations: [...]})')] → END-FOREACH</phase>
<phase name="2">STORE-AS($BEST_PRACTICES = 'Collected results from all research tasks')</phase>
</example>
</guideline>
<guideline id="phase5-project-includes">

GOAL(Analyze and suggest PROJECT-SPECIFIC includes only (NOT standard includes))
NOTE(IMPORTANT: Brain already has a Variation with standard includes configured This phase focuses ONLY on .brain/node/Includes/ FORBIDDEN: Suggesting or modifying vendor/jarvis-brain/core/src/Includes/*)

<example>
<phase name="1">Task(@agent-explore, 'TASK → [(Scan .brain/node/Includes/ for existing project includes + Read each include file to understand its purpose + Identify gaps in project-specific configuration)] → END-TASK', 'CONTEXT(Project-specific includes discovery)')</phase>
<phase name="2">STORE-AS($EXISTING_PROJECT_INCLUDES)</phase>
<phase name="3">Task(@agent-agent-master, 'INPUT(STORE-GET($EXISTING_PROJECT_INCLUDES) && STORE-GET($PROJECT_CONTEXT) && STORE-GET($DOCS_ANALYSIS) && STORE-GET($BEST_PRACTICES))', 'TASK → [(Analyze existing project-specific includes in .brain/node/Includes/ + Map project needs to include capabilities + Identify MISSING project-specific includes that should be CREATED + DO NOT suggest standard includes from vendor/jarvis-brain/core/src/Includes + Generate list of new project includes to create via brain make:include)] → END-TASK', 'OUTPUT({existing_project_includes: [...], suggested_new_includes: [...], rationale: {...}})')</phase>
<phase name="4">STORE-AS($PROJECT_INCLUDES_RECOMMENDATION)</phase>
</example>
</guideline>
<guideline id="phase6-custom-guidelines">
GOAL(Generate project-specific custom guidelines for Brain.php using PromptMaster)
<example>
<phase name="1">Task(@agent-prompt-master, 'INPUT(STORE-GET($PROJECT_CONTEXT) && STORE-GET($DOCS_ANALYSIS) && STORE-GET($BEST_PRACTICES) && STORE-GET($ARCHITECTURE_PATTERNS))', 'TASK → [(Identify project-specific patterns requiring custom guidelines + Generate guidelines using Builder API syntax ($this->guideline(), $this->rule()) + Apply prompt engineering: clarity, specificity, brevity, actionability + Focus on: coding standards, architectural rules, domain logic + Ensure guidelines are actionable and verifiable + Format as PHP Builder API code ready for Brain.php handle() method)] → END-TASK', 'OUTPUT({custom_guidelines: [{id: "...", type: "rule|guideline", code: "..."}], rationale: {...}})')</phase>
<phase name="2">STORE-AS($CUSTOM_GUIDELINES)</phase>
</example>
</guideline>
<guideline id="phase7-brain-enhancement">

GOAL(Enhance Brain.php handle() method with project-specific guidelines WHILE PRESERVING existing Variation)
NOTE(CRITICAL: Preserve ALL existing #[Includes()] attributes - they define the Variation ONLY modify the handle() method to add project-specific rules and guidelines DO NOT touch: namespace, class declaration, existing includes, Variation configuration)

<example>
<phase name="1">Backup existing Brain.php</phase>
<phase name="2">Bash(cp .brain/node/Brain.php .brain/node/Brain.php.backup) → [Create backup before modification] → END-Bash</phase>
<phase name="3">Enhance handle() method with project-specific content</phase>
<phase name="4">Task(@agent-prompt-master, 'INPUT(STORE-GET($CURRENT_BRAIN_CONFIG) && STORE-GET($PROJECT_INCLUDES_RECOMMENDATION) && STORE-GET($CUSTOM_GUIDELINES) && STORE-GET($PROJECT_CONTEXT))', 'TASK → [(PRESERVE existing #[Includes()] attributes (Variation) - DO NOT MODIFY + PRESERVE existing class structure and namespace + ADD project-specific rules and guidelines to handle() method + If suggested new project includes exist, add them to #[Includes()] AFTER existing ones + Apply prompt engineering: clarity, brevity, token efficiency + Format: existing includes → new project includes (if any) → rules → guidelines → style → response)] → END-TASK', 'OUTPUT({brain_php_content: "...", preserved_variation: "...", changes_summary: {...}})')</phase>
<phase name="5">Write enhanced Brain.php</phase>
<phase name="6">STORE-AS($ENHANCED_BRAIN_PHP)</phase>
<phase name="7">NOTE(Brain.php enhanced with project-specific configuration while preserving Variation)</phase>
</example>
</guideline>
<guideline id="phase8-compilation">
GOAL(Compile Brain.php and validate output)
<example>
<phase name="1">Bash(brain compile) → [Compile .brain/node/Brain.php to .claude/CLAUDE.md] → END-Bash</phase>
<phase name="2">VERIFY-SUCCESS(Compilation succeeded .claude/CLAUDE.md exists No syntax errors All includes resolved)</phase>
<phase name="3">IF(compilation failed) → THEN → [Restore backup → Bash('mv .brain/node/Brain.php.backup .brain/node/Brain.php') → Report errors → OUTPUT(Compilation failed - backup restored)] → END-IF</phase>
</example>
</guideline>
<guideline id="phase9-knowledge-storage">
GOAL(Store all insights to vector memory for future reference)
<example>
<phase name="1">mcp__vector-memory__store_memory('INPUT(content: "Brain Initialization - Project: {project_type}, Tech Stack: {tech_stack}, Patterns: {architecture_patterns}, Date: {current_date}" && category: "architecture" && tags: ["init-brain", "project-discovery", "configuration"])')</phase>
<phase name="2">mcp__vector-memory__store_memory('INPUT(content: "Best Practices Research - Frameworks: {frameworks}, Recommendations: {best_practices}, Date: {current_date}" && category: "learning" && tags: ["init-brain", "best-practices", "research"])')</phase>
<phase name="3">mcp__vector-memory__store_memory('INPUT(content: "Brain Configuration - Includes: {includes}, Custom Guidelines: {custom_guidelines_count}, Date: {current_date}" && category: "architecture" && tags: ["init-brain", "brain-config", "includes"])')</phase>
</example>
</guideline>
<guideline id="phase10-report">
GOAL(Generate comprehensive initialization report)
<example>
<phase name="1">OUTPUT(Brain Initialization Complete  Variation:   Preserved: {existing_variation_name} (UNCHANGED)   Standard includes: NOT MODIFIED  Project Discovery:   Type: {project_type}   Tech Stack: {tech_stack}   Architecture: {architecture_patterns}  Documentation Analysis:   Files Analyzed: {docs_file_count}   Domain Concepts: {domain_concepts_count}   Requirements: {requirements_count}  Project-Specific Includes:   Existing: {existing_project_includes}   Suggested new: {suggested_new_includes}   Location: .brain/node/Includes/  Custom Guidelines Added:   Rules: {custom_rules_count}   Guidelines: {custom_guidelines_count}  Best Practices:   Frameworks Researched: {frameworks_count}   Recommendations Applied: {recommendations_count}  Output Files:   Source: .brain/node/Brain.php   Compiled: .claude/CLAUDE.md   Backup: .brain/node/Brain.php.backup  Vector Memory:   Insights Stored: {insights_count}   Categories: architecture, learning  Next Steps:   1. Review enhanced Brain.php (Variation preserved)   2. Create suggested project includes: brain make:include {name}   3. Test Brain behavior with sample tasks   4. Adjust custom guidelines in handle() as needed   5. Run: brain compile (after any modifications)   6. Consider running: /init-agents for agent generation)</phase>
</example>
</guideline>
<guideline id="error-recovery">
<text>Comprehensive error handling for all failure scenarios</text>
<example>
<phase name="1">IF(no .docs/ found) → THEN → [Continue with codebase analysis only → Log: Documentation not available] → END-IF</phase>
<phase name="2">IF(tech stack detection fails) → THEN → [Use manual fallback detection → Analyze file extensions and structure] → END-IF</phase>
<phase name="3">IF(web research fails) → THEN → [Use cached knowledge from vector memory → Continue with available information] → END-IF</phase>
<phase name="4">IF(brain list:includes fails) → THEN → [Use hardcoded standard includes list → Log: Include discovery failed] → END-IF</phase>
<phase name="5">IF(Brain.php generation fails) → THEN → [Preserve backup → Report detailed error → Provide manual configuration guidance] → END-IF</phase>
<phase name="6">IF(brain compile fails) → THEN → [Restore backup → Analyze compilation errors → Suggest fixes] → END-IF</phase>
<phase name="7">IF(vector memory storage fails) → THEN → [Continue without storage → Log: Memory storage unavailable] → END-IF</phase>
</example>
</guideline>
<guideline id="quality-gates">
<text>Validation checkpoints throughout initialization</text>
<example>Gate 1: Temporal context initialized (date, year, timestamp)</example>
<example>Gate 2: Project discovery completed with valid tech stack</example>
<example>Gate 3: At least one discovery task succeeded (docs OR codebase)</example>
<example>Gate 4: Includes recommendation generated with rationale</example>
<example>Gate 5: Brain.php backup created successfully</example>
<example>Gate 6: New Brain.php passes syntax validation</example>
<example>Gate 7: Compilation completes without errors</example>
<example>Gate 8: Compiled output exists at .claude/CLAUDE.md</example>
<example>Gate 9: At least one insight stored to vector memory</example>
</guideline>
<guideline id="example-laravel-project">
SCENARIO(Laravel project with Scrutinizer Variation and comprehensive documentation)
<example>
<phase name="1">Variation: Scrutinizer (PRESERVED - not modified)</phase>
<phase name="2">Discovery: Laravel 11, PHP 8.3, MySQL, Redis, Queue, Sanctum</phase>
<phase name="3">Docs: 15 .md files with architecture, requirements, domain logic</phase>
<phase name="4">Research: Laravel 2025 best practices, service container patterns</phase>
<phase name="5">Project Includes: Suggested LaravelDomainRules.php in .brain/node/Includes/</phase>
<phase name="6">Custom Guidelines: Repository pattern rules, service layer conventions added to handle()</phase>
<phase name="7">Result: Enhanced Brain.php with project-specific guidelines, Variation intact</phase>
<phase name="8">Insights: 5 architectural insights stored to vector memory</phase>
</example>
</guideline>
<guideline id="example-node-project">
SCENARIO(Node.js/Express project with Architect Variation)
<example>
<phase name="1">Variation: Architect (PRESERVED - not modified)</phase>
<phase name="2">Discovery: Node.js 20, Express, TypeScript, MongoDB, Docker</phase>
<phase name="3">Docs: None found - codebase analysis only</phase>
<phase name="4">Research: Express 2025 patterns, TypeScript best practices</phase>
<phase name="5">Project Includes: No new project includes needed</phase>
<phase name="6">Custom Guidelines: REST API conventions, middleware patterns added to handle()</phase>
<phase name="7">Result: Enhanced Brain.php with Node.js-aware guidelines, Variation intact</phase>
<phase name="8">Insights: 3 tech stack insights stored</phase>
</example>
</guideline>
<guideline id="example-hybrid-project">
SCENARIO(Hybrid PHP/JavaScript project with Custom Variation)
<example>
<phase name="1">Variation: CustomVariation (PRESERVED - not modified)</phase>
<phase name="2">Discovery: Laravel API + React SPA + Docker + Kafka</phase>
<phase name="3">Docs: Architectural decision records, API specs, deployment docs</phase>
<phase name="4">Research: Microservices patterns, event-driven architecture</phase>
<phase name="5">Project Includes: Suggested MicroserviceBoundaries.php, EventSchemas.php</phase>
<phase name="6">Custom Guidelines: API versioning rules, event contract validation added to handle()</phase>
<phase name="7">Result: Enhanced Brain.php with microservice guidelines, Variation intact</phase>
<phase name="8">Insights: 12 cross-cutting concerns stored</phase>
</example>
</guideline>
<guideline id="performance-optimization">
<text>Optimization strategies for efficient initialization</text>
<example>
<phase name="1">Parallel Execution: All independent tasks run simultaneously</phase>
<phase name="2">Selective Reading: Only read files needed for analysis</phase>
<phase name="3">Incremental Storage: Store insights progressively, not at end</phase>
<phase name="4">Smart Caching: Leverage vector memory for repeated runs</phase>
<phase name="5">Early Validation: Fail fast on critical errors</phase>
<phase name="6">Streaming Output: Report progress as phases complete</phase>
</example>
</guideline>
<guideline id="directive">
<text>Core initialization directive</text>
<example>Discover thoroughly! Research current practices! Configure precisely! Validate rigorously! Store knowledge! Report comprehensively!</example>
</guideline>
</guidelines>
</command>