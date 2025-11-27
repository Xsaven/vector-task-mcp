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
<purpose>The InitBrain command automates smart distribution of project-specific configuration across Brain.php, Common.php, and Master.php based on project context discovery.</purpose>
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
<rule id="smart-distribution" severity="critical">
<text>Distribute project-specific rules across THREE files to avoid duplication: .brain/node/Common.php - Shared by Brain AND all Agents .brain/node/Master.php - Shared by ALL Agents only (NOT Brain) .brain/node/Brain.php - Brain-specific only</text>
<why>Prevents duplication across components, ensures single source of truth for each rule type</why>
<on_violation>Rule placed in wrong file causes duplication or missing context</on_violation>
</rule>
<rule id="distribution-categories" severity="critical">
<text>COMMON: Environment (Docker, CI/CD), project tech stack, universal coding standards, shared config MASTER: Agent execution patterns, tool usage constraints, agent-specific guidelines, task handling BRAIN: Orchestration rules, delegation strategies, Brain-specific policies, workflow coordination</text>
<why>Clear categorization ensures each file serves its specific purpose without overlap</why>
<on_violation>Miscategorized rule leads to missing context or unnecessary duplication</on_violation>
</rule>
<rule id="incremental-enhancement" severity="critical">
<text>ALWAYS analyze existing file content BEFORE enhancement If file has rules/guidelines - PRESERVE valuable existing, ADD only missing NEVER blindly overwrite populated files - merge intelligently Compare discovered patterns with existing config to find gaps</text>
<why>Preserves manual customizations and avoids losing valuable existing configuration</why>
<on_violation>Valuable existing configuration lost, manual work discarded</on_violation>
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
<phase name="parallel-discovery-tasks">TASK → [(Task(@agent-explore, 'TASK → [(Check if .docs/ directory exists using Glob + Use Glob("**/.docs/**/*.md") to find documentation files + IF(.docs/ exists) → THEN → [Read all .md files from .docs/ directory → Extract: project goals, requirements, architecture decisions, domain terminology → STORE-AS($DOCS_CONTENT)] → ELSE → [No .docs/ found → STORE-AS($DOCS_CONTENT = \'null\')] → END-IF)] → END-TASK', 'CONTEXT(Documentation discovery for project context)') + Task(@agent-explore, 'TASK → [(Analyze project root structure + Use Glob to find: composer.json, package.json, .env.example, README.md + Read key dependency files + Identify project type (Laravel, Node.js, hybrid, etc.) + Extract technology stack from dependency files + STORE-AS($PROJECT_TYPE) + STORE-AS($TECH_STACK = \'{languages: [...], frameworks: [...], packages: [...], services: [...]}\'))] → END-TASK', 'CONTEXT(Codebase structure and tech stack analysis)') + Task(@agent-explore, 'TASK → [(Scan for architectural patterns + Use Glob to find PHP/JS/TS files in app/ and src/ directories + Analyze code structure and organization + Identify: MVC, DDD, CQRS, microservices, monolith, etc. + Detect design patterns: repositories, services, factories, observers, etc. + Find coding conventions: naming, structure, organization + STORE-AS($ARCHITECTURE_PATTERNS = \'{architecture_style: "...", design_patterns: [...], conventions: [...]}\'))] → END-TASK', 'CONTEXT(Architecture pattern discovery)') + Task(@agent-explore, 'TASK → [(Read(\'.brain/node/Brain.php\') + Read(\'.brain/node/Common.php\') + Read(\'.brain/node/Master.php\') + For EACH file analyze handle() method content: +   - Extract existing $this->rule() definitions (id, severity, text) +   - Extract existing $this->guideline() definitions (id, phases, examples) +   - Identify custom logic and project-specific patterns +   - Mark as POPULATED if handle() has meaningful content beyond skeleton + STORE-AS($CURRENT_BRAIN_CONFIG = \'{includes: [...], rules: [...], guidelines: [...], is_populated: bool}\') + STORE-AS($CURRENT_COMMON_CONFIG = \'{rules: [...], guidelines: [...], is_populated: bool}\') + STORE-AS($CURRENT_MASTER_CONFIG = \'{rules: [...], guidelines: [...], is_populated: bool}\'))] → END-TASK', 'CONTEXT(Existing configuration analysis for incremental enhancement)'))] → END-TASK</phase>
<phase name="2">VERIFY-SUCCESS(All discovery tasks completed)</phase>
<phase name="3">STORE-AS($PROJECT_CONTEXT = 'Merged results from all discovery tasks')</phase>
</example>
</guideline>
<guideline id="phase2-5-environment-discovery">
GOAL(Discover environment configuration, containerization, and infrastructure patterns)
<example>
NOTE(Environment rules go to Common.php - shared by Brain AND all Agents)
<phase name="parallel-environment-tasks">TASK → [(Task(@agent-explore, 'TASK → [(Use Glob to find: Dockerfile*, docker-compose*.yml, .dockerignore + Read Docker configurations if found + Extract: base images, services, ports, volumes, networks + Identify: container orchestration patterns (Docker Compose, K8s, etc.) + STORE-AS($DOCKER_CONFIG = \'{has_docker: bool, services: [...], patterns: [...]}\'))] → END-TASK', 'CONTEXT(Docker and containerization discovery)') + Task(@agent-explore, 'TASK → [(Use Glob to find: .github/workflows/*.yml, .gitlab-ci.yml, Jenkinsfile, bitbucket-pipelines.yml + Read CI/CD configurations if found + Extract: build steps, test runners, deployment targets + Identify: CI/CD platform and workflow patterns + STORE-AS($CICD_CONFIG = \'{platform: "...", workflows: [...], deployment_targets: [...]}\'))] → END-TASK', 'CONTEXT(CI/CD pipeline discovery)') + Task(@agent-explore, 'TASK → [(Use Glob to find: .editorconfig, .prettierrc*, .eslintrc*, phpcs.xml*, phpstan.neon* + Read linter/formatter configurations if found + Extract: code style rules, linting rules, analysis levels + Identify: tooling ecosystem (Prettier, ESLint, PHPStan, etc.) + STORE-AS($DEV_TOOLS_CONFIG = \'{formatters: [...], linters: [...], analyzers: [...]}\'))] → END-TASK', 'CONTEXT(Development tooling discovery)') + Task(@agent-explore, 'TASK → [(Use Glob to find: .env.example, config/*.php, infrastructure/* + Analyze service connections: databases, caches, queues, storage + Identify: external service dependencies (AWS, GCP, Redis, Elasticsearch) + Map infrastructure topology + STORE-AS($INFRASTRUCTURE_CONFIG = \'{services: [...], external_deps: [...], topology: {...}}\'))] → END-TASK', 'CONTEXT(Infrastructure and services discovery)'))] → END-TASK</phase>
<phase name="2">VERIFY-SUCCESS(Environment discovery completed)</phase>
<phase name="3">STORE-AS($ENVIRONMENT_CONTEXT = 'Merged environment configuration')</phase>
</example>
</guideline>
<guideline id="phase3-documentation-analysis">
GOAL(Deep analysis of project documentation to extract requirements and domain knowledge)
<example>
<phase name="1">IF(STORE-GET($DOCS_CONTENT) !== null) → THEN → [Task(@agent-documentation-master, 'INPUT(STORE-GET($DOCS_CONTENT))', 'TASK → [(Analyze all documentation files + Extract: project goals, requirements, constraints, domain concepts + Identify: key workflows, business rules, integration points + Map documentation to Brain configuration needs + Suggest: custom includes, rules, guidelines based on docs)] → END-TASK', 'OUTPUT({goals: [...], requirements: [...], domain_concepts: [...], suggested_config: {...}})') → STORE-AS($DOCS_ANALYSIS)] → ELSE → [No documentation found - will rely on codebase analysis only → STORE-AS($DOCS_ANALYSIS = 'null')] → END-IF</phase>
</example>
</guideline>
<guideline id="phase3-5-vector-memory-mining">

GOAL(Extract CRITICAL accumulated knowledge from vector memory that MUST be in instructions)
NOTE(Vector memory may contain crucial insights discovered over time NOT everything - only HIGH-VALUE knowledge that cannot be found via normal search Focus: architectural decisions, gotchas, patterns that prevent repeated mistakes)

<example>
<phase name="parallel-vector-mining">TASK → [(mcp__vector-memory__search_memories('INPUT(query: "architecture decision critical constraint must always never" && category: "architecture" && limit: 10)') + STORE-AS($ARCH_DECISIONS) + mcp__vector-memory__search_memories('INPUT(query: "critical bug gotcha always remember never forget important" && category: "bug-fix" && limit: 10)') + STORE-AS($CRITICAL_GOTCHAS) + mcp__vector-memory__search_memories('INPUT(query: "project pattern convention always use must follow" && category: "code-solution" && limit: 10)') + STORE-AS($PROJECT_PATTERNS) + mcp__vector-memory__search_memories('INPUT(query: "lesson learned important insight discovery realization" && category: "learning" && limit: 10)') + STORE-AS($LESSONS_LEARNED))] → END-TASK</phase>
<phase name="2">Task(@agent-agent-master, 'INPUT(STORE-GET($ARCH_DECISIONS) && STORE-GET($CRITICAL_GOTCHAS) && STORE-GET($PROJECT_PATTERNS) && STORE-GET($LESSONS_LEARNED))', 'TASK → [(Analyze ALL mined vector memory insights + FILTER: Keep ONLY insights meeting CRITICAL criteria: +   - Would cause significant issues if forgotten +   - Cannot be easily discovered via normal search +   - Represents hard-won knowledge or painful lessons +   - Applies broadly across multiple tasks/agents +  + EXCLUDE: +   - Generic information easily searchable +   - One-time fixes without broader applicability +   - Outdated or superseded knowledge +   - Already covered by standard includes +  + CATEGORIZE filtered insights for distribution: +   - COMMON: Universal constraints (all components need) +   - MASTER: Agent execution patterns (agents need) +   - BRAIN: Orchestration insights (Brain needs) +  + Generate concise rule/guideline code for each critical insight)] → END-TASK', 'OUTPUT({critical_common: [...], critical_master: [...], critical_brain: [...], filtered_count: N, reason: {...}})')</phase>
<phase name="3">STORE-AS($VECTOR_CRITICAL_INSIGHTS)</phase>
<phase name="4">NOTE(Critical vector insights will be merged into DISTRIBUTED_GUIDELINES in Phase 6)</phase>
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
<guideline id="phase6-smart-distribution">

GOAL(Categorize discovered rules/guidelines into Common, Master, or Brain files)
NOTE(CRITICAL: Each rule MUST go to exactly ONE file to avoid duplication .brain/node/Common.php - Shared by Brain AND all Agents .brain/node/Master.php - Shared by ALL Agents only .brain/node/Brain.php - Brain-specific only)

<example>
<phase name="1">Task(@agent-agent-master, 'INPUT(STORE-GET($PROJECT_CONTEXT) && STORE-GET($ENVIRONMENT_CONTEXT) && STORE-GET($DOCS_ANALYSIS) && STORE-GET($BEST_PRACTICES) && STORE-GET($ARCHITECTURE_PATTERNS) && STORE-GET($VECTOR_CRITICAL_INSIGHTS))', 'TASK → [(Analyze ALL discovered project patterns, rules, AND critical vector insights + MERGE VECTOR_CRITICAL_INSIGHTS into distribution (already categorized) + CATEGORIZE remaining rules into exactly ONE target file: +  + COMMON.PHP (Brain + ALL Agents): +   - Docker/container environment rules (ports, services, networks) +   - CI/CD pipeline awareness (test commands, build steps) +   - Project tech stack rules (PHP version, Node version, database type) +   - Universal coding standards (naming conventions, file structure) +   - Shared configuration (env vars, paths, external services) +   - Development tooling rules (linters, formatters, analyzers) +  + MASTER.PHP (ALL Agents only, NOT Brain): +   - Agent execution patterns (how agents should approach tasks) +   - Tool usage constraints (when to use which tools) +   - Task handling guidelines (decomposition, estimation, status flow) +   - Code generation patterns (templates, scaffolding) +   - Test writing conventions (test structure, coverage expectations) +   - Agent-specific quality gates (validation before completion) +  + BRAIN.PHP (Brain-specific only): +   - Orchestration rules (delegation strategies, agent selection) +   - Brain-specific policies (approval chains, escalation) +   - Workflow coordination (multi-agent orchestration) +   - Response synthesis (how to merge agent results) +   - Brain-level validation (response quality gates) +  + Generate PHP Builder API code for each category + Use $this->rule() for constraints, $this->guideline() for patterns)] → END-TASK', 'OUTPUT({common: [{id, type, code}], master: [{id, type, code}], brain: [{id, type, code}], rationale: {...}})')</phase>
<phase name="2">STORE-AS($DISTRIBUTED_GUIDELINES)</phase>
</example>
</guideline>
<guideline id="phase6a-common-enhancement">

GOAL(Enhance Common.php with shared project rules for Brain AND all Agents)
NOTE(Common.php is included by BOTH BrainIncludesTrait AND AgentIncludesTrait Rules here apply universally - avoid agent-specific or brain-specific content Focus: environment, tech stack, coding standards, shared configuration)

<example>
<phase name="1">Backup existing Common.php</phase>
<phase name="2">Bash(cp .brain/node/Common.php .brain/node/Common.php.backup) → [Create backup before modification] → END-Bash</phase>
<phase name="3">Read('.brain/node/Common.php')</phase>
<phase name="4">STORE-AS($CURRENT_COMMON_CONFIG)</phase>
<phase name="5">Task(@agent-prompt-master, 'INPUT(STORE-GET($CURRENT_COMMON_CONFIG) && STORE-GET($DISTRIBUTED_GUIDELINES.common) && STORE-GET($ENVIRONMENT_CONTEXT))', 'TASK → [(PRESERVE existing class structure, namespace, and extends IncludeArchetype + IF(CURRENT_COMMON_CONFIG.is_populated) → THEN → [MERGE MODE: File has existing content →   - KEEP all existing rules/guidelines that are still relevant →   - UPDATE rules if new discovery provides better info (same id, improved text) →   - ADD only NEW rules/guidelines not already present →   - REMOVE nothing unless explicitly obsolete →   - Compare rule IDs to avoid duplicates] → ELSE → [FRESH MODE: File is empty/skeleton - add all discovered rules] → END-IF + Focus on environment and universal rules: +   - Docker/container configuration awareness +   - Tech stack version constraints +   - Universal coding conventions +   - Shared infrastructure knowledge + Apply prompt engineering: clarity, brevity, token efficiency)] → END-TASK', 'OUTPUT({common_php_content: "...", rules_kept: [...], rules_added: [...], rules_updated: [...]})')</phase>
<phase name="6">Write enhanced Common.php</phase>
<phase name="7">STORE-AS($ENHANCED_COMMON_PHP)</phase>
<phase name="8">NOTE(Common.php enhanced with shared project configuration)</phase>
</example>
</guideline>
<guideline id="phase6b-master-enhancement">

GOAL(Enhance Master.php with agent-specific rules shared by ALL Agents)
NOTE(Master.php is included by AgentIncludesTrait only (NOT Brain) Rules here apply to all agents but NOT to Brain orchestration Focus: execution patterns, tool usage, task handling, code generation)

<example>
<phase name="1">Backup existing Master.php</phase>
<phase name="2">Bash(cp .brain/node/Master.php .brain/node/Master.php.backup) → [Create backup before modification] → END-Bash</phase>
<phase name="3">Read('.brain/node/Master.php')</phase>
<phase name="4">STORE-AS($CURRENT_MASTER_CONFIG)</phase>
<phase name="5">Task(@agent-prompt-master, 'INPUT(STORE-GET($CURRENT_MASTER_CONFIG) && STORE-GET($DISTRIBUTED_GUIDELINES.master) && STORE-GET($ARCHITECTURE_PATTERNS))', 'TASK → [(PRESERVE existing class structure, namespace, and extends IncludeArchetype + IF(CURRENT_MASTER_CONFIG.is_populated) → THEN → [MERGE MODE: File has existing content →   - KEEP all existing rules/guidelines that are still relevant →   - UPDATE rules if new discovery provides better info (same id, improved text) →   - ADD only NEW rules/guidelines not already present →   - REMOVE nothing unless explicitly obsolete →   - Compare rule IDs to avoid duplicates] → ELSE → [FRESH MODE: File is empty/skeleton - add all discovered rules] → END-IF + Focus on agent execution patterns: +   - How agents should approach project tasks +   - Tool usage patterns for this project +   - Code generation conventions +   - Test writing patterns +   - Quality gates before task completion + Apply prompt engineering: clarity, brevity, token efficiency)] → END-TASK', 'OUTPUT({master_php_content: "...", rules_kept: [...], rules_added: [...], rules_updated: [...]})')</phase>
<phase name="6">Write enhanced Master.php</phase>
<phase name="7">STORE-AS($ENHANCED_MASTER_PHP)</phase>
<phase name="8">NOTE(Master.php enhanced with agent-specific project configuration)</phase>
</example>
</guideline>
<guideline id="phase7-brain-enhancement">

GOAL(Enhance Brain.php with Brain-specific orchestration rules ONLY)
NOTE(CRITICAL: Preserve ALL existing #[Includes()] attributes - they define the Variation ONLY add Brain-specific rules (orchestration, delegation, synthesis) Common rules go to Common.php, agent rules go to Master.php)

<example>
<phase name="1">Backup existing Brain.php</phase>
<phase name="2">Bash(cp .brain/node/Brain.php .brain/node/Brain.php.backup) → [Create backup before modification] → END-Bash</phase>
<phase name="3">Enhance handle() method with Brain-specific content only</phase>
<phase name="4">Task(@agent-prompt-master, 'INPUT(STORE-GET($CURRENT_BRAIN_CONFIG) && STORE-GET($PROJECT_INCLUDES_RECOMMENDATION) && STORE-GET($DISTRIBUTED_GUIDELINES.brain) && STORE-GET($PROJECT_CONTEXT))', 'TASK → [(PRESERVE existing #[Includes()] attributes (Variation) - DO NOT MODIFY + PRESERVE existing class structure and namespace + IF(CURRENT_BRAIN_CONFIG.is_populated) → THEN → [MERGE MODE: File has existing handle() content →   - KEEP all existing rules/guidelines in handle() that are still relevant →   - UPDATE rules if new discovery provides better info (same id, improved text) →   - ADD only NEW Brain-specific rules not already present →   - REMOVE nothing unless explicitly obsolete →   - Compare rule IDs to avoid duplicates] → ELSE → [FRESH MODE: handle() is empty/skeleton - add all Brain-specific rules] → END-IF + Focus on Brain-specific rules only (Common/Master rules already distributed): +   - Orchestration and delegation strategies +   - Agent selection criteria for this project +   - Response synthesis patterns +   - Brain-level validation gates + If suggested new project includes, add to #[Includes()] AFTER existing + Apply prompt engineering: clarity, brevity, token efficiency)] → END-TASK', 'OUTPUT({brain_php_content: "...", preserved_variation: "...", rules_kept: [...], rules_added: [...], rules_updated: [...]})')</phase>
<phase name="5">Write enhanced Brain.php</phase>
<phase name="6">STORE-AS($ENHANCED_BRAIN_PHP)</phase>
<phase name="7">NOTE(Brain.php enhanced with Brain-specific configuration while preserving Variation)</phase>
</example>
</guideline>
<guideline id="phase7-5-env-configuration">

GOAL(Extract configurable settings to .brain/.env for easy tuning)
NOTE(Centralizes all adjustable parameters in one place Uses $this->var() in PHP code to read ENV values Comments document each setting with variants and combinations Prevents duplication - single source of truth for configurable values)

<example>
<phase name="1">Read existing .env if present</phase>
<phase name="2">IF(.brain/.env exists) → THEN → [Read('.brain/.env') → STORE-AS($EXISTING_ENV)] → ELSE → [STORE-AS($EXISTING_ENV = 'null')] → END-IF</phase>
<phase name="3">Task(@agent-agent-master, 'INPUT(STORE-GET($EXISTING_ENV) && STORE-GET($PROJECT_CONTEXT) && STORE-GET($TECH_STACK) && STORE-GET($ENVIRONMENT_CONTEXT) && STORE-GET($ARCHITECTURE_PATTERNS) && STORE-GET($VECTOR_CRITICAL_INSIGHTS))', 'TASK → [(Analyze ALL discovered project settings and identify CONFIGURABLE values +  + EXTRACT settings that: +   - May need adjustment per environment/project +   - Control behavior that users might want to tweak +   - Represent thresholds, limits, or toggles +   - Are referenced in multiple places (DRY) +  + CATEGORIES to consider: +   - Model settings: DEFAULT_MODEL, FALLBACK_MODEL +   - Limits: MAX_TOKENS, MAX_RETRIES, TIMEOUT_SECONDS +   - Toggles: ENABLE_VECTOR_MEMORY, ENABLE_WEB_RESEARCH +   - Paths: DOCS_DIRECTORY, OUTPUT_DIRECTORY +   - Project-specific: PHP_VERSION, NODE_VERSION, DATABASE_TYPE +   - Quality gates: MIN_COVERAGE, PHPSTAN_LEVEL +   - Agent behavior: AGENT_VERBOSITY, PARALLEL_AGENTS +  + FOR EACH setting generate: +   - UPPER_SNAKE_CASE name +   - Default value (from project discovery) +   - Comment with description (1 line) +   - Comment with variants/options if applicable +  + MERGE with EXISTING_ENV: +   - PRESERVE user-modified values +   - ADD new settings not present +   - UPDATE comments if improved +   - KEEP user comments intact)] → END-TASK', 'OUTPUT({env_content: "...", settings_kept: [...], settings_added: [...], settings_updated: [...]})')</phase>
<phase name="4">STORE-AS($ENV_CONFIGURATION)</phase>
<phase name="5">Generate .env file content with structured comments</phase>
<phase name="6">Task(@agent-prompt-master, 'INPUT(STORE-GET($ENV_CONFIGURATION) && STORE-GET($EXISTING_ENV))', 'TASK → [(Generate well-structured .env file content +  + FORMAT RULES: +   - Group settings by category with section headers +   - Each setting: # description\\n# variants: opt1 | opt2 | opt3\\nKEY=value +   - Empty line between groups +   - No quotes around simple values +   - Quotes for values with spaces +  + SECTION ORDER: +   1. # ═══ BRAIN CORE ═══ +   2. # ═══ MODELS ═══ +   3. # ═══ LIMITS & THRESHOLDS ═══ +   4. # ═══ FEATURES ═══ +   5. # ═══ PROJECT ═══ +   6. # ═══ QUALITY GATES ═══ +   7. # ═══ PATHS ═══ +  + EXAMPLE FORMAT: + # ═══ MODELS ═══ +  + # Default model for Brain orchestration + # variants: sonnet | opus | haiku + DEFAULT_MODEL=sonnet +  + # Fallback model when primary unavailable + # variants: haiku | sonnet + FALLBACK_MODEL=haiku)] → END-TASK', 'OUTPUT({formatted_env: "..."})')</phase>
<phase name="7">STORE-AS($FORMATTED_ENV)</phase>
<phase name="8">Backup existing .env and write new</phase>
<phase name="9">IF(EXISTING_ENV !== null) → THEN → [Bash(cp .brain/.env .brain/.env.backup) → [Backup existing .env] → END-Bash] → END-IF</phase>
<phase name="10">Write .brain/.env</phase>
<phase name="11">NOTE(.env generated with configurable settings - use $this->var(\"KEY\") in PHP)</phase>
</example>
</guideline>
<guideline id="phase8-compilation">
GOAL(Validate syntax and compile all enhanced files)
<example>
<phase name="1">Validate PHP syntax for all modified files</phase>
<phase name="2">TASK → [(Bash(php -l .brain/node/Common.php) → [Validate Common.php syntax] → END-Bash + Bash(php -l .brain/node/Master.php) → [Validate Master.php syntax] → END-Bash + Bash(php -l .brain/node/Brain.php) → [Validate Brain.php syntax] → END-Bash)] → END-TASK</phase>
<phase name="3">IF(any syntax validation failed) → THEN → [Restore all backups → Bash('mv .brain/node/Common.php.backup .brain/node/Common.php') → Bash('mv .brain/node/Master.php.backup .brain/node/Master.php') → Bash('mv .brain/node/Brain.php.backup .brain/node/Brain.php') → Report syntax errors → OUTPUT(Syntax validation failed - all backups restored)] → END-IF</phase>
<phase name="4">Compile Brain ecosystem</phase>
<phase name="5">Bash(brain compile) → [Compile .brain/node/Brain.php with includes to .claude/CLAUDE.md] → END-Bash</phase>
<phase name="6">VERIFY-SUCCESS(Compilation succeeded .claude/CLAUDE.md exists No compilation errors Common.php included via BrainIncludesTrait Master.php available for AgentIncludesTrait)</phase>
<phase name="7">IF(compilation failed) → THEN → [Restore all backups → Bash('mv .brain/node/Common.php.backup .brain/node/Common.php') → Bash('mv .brain/node/Master.php.backup .brain/node/Master.php') → Bash('mv .brain/node/Brain.php.backup .brain/node/Brain.php') → Report compilation errors → OUTPUT(Compilation failed - all backups restored)] → END-IF</phase>
</example>
</guideline>
<guideline id="phase9-knowledge-storage">
GOAL(Store all insights to vector memory for future reference)
<example>
<phase name="1">mcp__vector-memory__store_memory('INPUT(content: "Brain Initialization - Project: {project_type}, Tech Stack: {tech_stack}, Patterns: {architecture_patterns}, Date: {current_date}" && category: "architecture" && tags: ["init-brain", "project-discovery", "configuration"])')</phase>
<phase name="2">mcp__vector-memory__store_memory('INPUT(content: "Environment Discovery - Docker: {has_docker}, CI/CD: {cicd_platform}, Dev Tools: {dev_tools}, Date: {current_date}" && category: "architecture" && tags: ["init-brain", "environment", "infrastructure"])')</phase>
<phase name="3">mcp__vector-memory__store_memory('INPUT(content: "Smart Distribution - Common: {common_rules_count} rules, Master: {master_rules_count} rules, Brain: {brain_rules_count} rules, Date: {current_date}" && category: "architecture" && tags: ["init-brain", "distribution", "configuration"])')</phase>
<phase name="4">mcp__vector-memory__store_memory('INPUT(content: "Best Practices Research - Frameworks: {frameworks}, Recommendations: {best_practices}, Date: {current_date}" && category: "learning" && tags: ["init-brain", "best-practices", "research"])')</phase>
</example>
</guideline>
<guideline id="phase10-report">
GOAL(Generate comprehensive initialization report with smart distribution summary)
<example>
<phase name="1">OUTPUT(Brain Ecosystem Initialization Complete  ═══════════════════════════════════════════════════════ SMART DISTRIBUTION SUMMARY ═══════════════════════════════════════════════════════  .brain/node/Common.php (Brain + ALL Agents):   Mode: {common_mode}   Kept: {common_rules_kept} | Added: {common_rules_added} | Updated: {common_rules_updated}   Backup: .brain/node/Common.php.backup  .brain/node/Master.php (ALL Agents only):   Mode: {master_mode}   Kept: {master_rules_kept} | Added: {master_rules_added} | Updated: {master_rules_updated}   Backup: .brain/node/Master.php.backup  .brain/node/Brain.php (Brain only):   Variation: {existing_variation_name} (PRESERVED)   Mode: {brain_mode}   Kept: {brain_rules_kept} | Added: {brain_rules_added} | Updated: {brain_rules_updated}   Backup: .brain/node/Brain.php.backup  ═══════════════════════════════════════════════════════ DISCOVERY RESULTS ═══════════════════════════════════════════════════════  Project:   Type: {project_type}   Tech Stack: {tech_stack}   Architecture: {architecture_patterns}  Environment:   Docker: {has_docker}   CI/CD Platform: {cicd_platform}   Dev Tools: {dev_tools}   Infrastructure: {infrastructure_services}  Documentation:   Files Analyzed: {docs_file_count}   Domain Concepts: {domain_concepts_count}   Requirements: {requirements_count}  Vector Memory Mining:   Total Mined: {vector_total_mined}   Critical Filtered: {vector_critical_count}   Added to Common: {vector_common_count}   Added to Master: {vector_master_count}   Added to Brain: {vector_brain_count}  ═══════════════════════════════════════════════════════ OUTPUT FILES ═══════════════════════════════════════════════════════  Source Files:   .brain/node/Brain.php   .brain/node/Common.php   .brain/node/Master.php  Compiled Output:   .claude/CLAUDE.md  Configuration:   .brain/.env   Settings: {env_settings_count} ({env_kept} kept, {env_added} added)  Backups:   .brain/node/*.backup   .brain/.env.backup (if existed)  ═══════════════════════════════════════════════════════ VECTOR MEMORY ═══════════════════════════════════════════════════════    Insights Stored: {insights_count}   Categories: architecture, learning   Tags: init-brain, project-discovery, distribution  ═══════════════════════════════════════════════════════ NEXT STEPS ═══════════════════════════════════════════════════════    1. Review enhanced files:      - Common.php: shared environment/coding rules      - Master.php: agent execution patterns      - Brain.php: orchestration rules (Variation preserved)    2. If project includes suggested:      brain make:include {name}    3. Test Brain behavior with sample tasks    4. After any modifications:      brain compile    5. Consider running:      /init-agents for agent generation      /init-vector for vector memory population)</phase>
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
<example>Gate 3: Environment discovery completed (Docker, CI/CD, Dev Tools)</example>
<example>Gate 4: At least one discovery task succeeded (docs OR codebase)</example>
<example>Gate 5: Smart distribution categorization completed (Common/Master/Brain)</example>
<example>Gate 6: All backups created (Common.php.backup, Master.php.backup, Brain.php.backup)</example>
<example>Gate 7: All enhanced files pass PHP syntax validation</example>
<example>Gate 8: Compilation completes without errors</example>
<example>Gate 9: Compiled output exists at .claude/CLAUDE.md</example>
<example>Gate 10: At least one insight stored to vector memory</example>
</guideline>
<guideline id="example-laravel-docker-project">
SCENARIO(Laravel project with Docker, Sail, and comprehensive documentation)
<example>
<phase name="1">Discovery: Laravel 11, PHP 8.3, MySQL, Redis, Queue, Sanctum</phase>
<phase name="2">Environment: Docker (Sail), GitHub Actions CI/CD, PHPStan L8</phase>
<phase name="3">Docs: 15 .md files with architecture, requirements, domain logic</phase>
<phase name="4">Research: Laravel 2025 best practices, service container patterns</phase>
<phase name="5">
</phase>
<phase name="6">SMART DISTRIBUTION:</phase>
<phase name="7">  Common.php: Docker/Sail environment rules, PHP 8.3 type constraints, MySQL conventions</phase>
<phase name="8">  Master.php: Service class patterns, repository usage, Pest test conventions</phase>
<phase name="9">  Brain.php: Agent delegation for Laravel domains (Auth, Queue, Cache)</phase>
<phase name="10">
</phase>
<phase name="11">Result: All three files enhanced, Scrutinizer Variation preserved</phase>
<phase name="12">Insights: 8 architectural insights stored to vector memory</phase>
</example>
</guideline>
<guideline id="example-node-docker-project">
SCENARIO(Node.js/Express project with Docker and TypeScript)
<example>
<phase name="1">Discovery: Node.js 20, Express, TypeScript, MongoDB</phase>
<phase name="2">Environment: Docker Compose, GitLab CI, ESLint + Prettier</phase>
<phase name="3">Docs: None found - codebase analysis only</phase>
<phase name="4">Research: Express 2025 patterns, TypeScript best practices</phase>
<phase name="5">
</phase>
<phase name="6">SMART DISTRIBUTION:</phase>
<phase name="7">  Common.php: Docker network rules, Node 20 constraints, ESLint compliance</phase>
<phase name="8">  Master.php: TypeScript type generation, async/await patterns, Jest test structure</phase>
<phase name="9">  Brain.php: API route delegation strategy</phase>
<phase name="10">
</phase>
<phase name="11">Result: All three files enhanced, Architect Variation preserved</phase>
<phase name="12">Insights: 5 tech stack insights stored</phase>
</example>
</guideline>
<guideline id="example-hybrid-microservices">
SCENARIO(Hybrid PHP/JavaScript microservices with Kubernetes)
<example>
<phase name="1">Discovery: Laravel API + React SPA + Docker + Kafka</phase>
<phase name="2">Environment: Kubernetes, GitHub Actions, PHPStan + ESLint</phase>
<phase name="3">Docs: ADRs, API specs, deployment docs, domain model</phase>
<phase name="4">Research: Microservices patterns, event-driven architecture</phase>
<phase name="5">
</phase>
<phase name="6">SMART DISTRIBUTION:</phase>
<phase name="7">  Common.php: K8s service discovery, cross-service authentication, Kafka topic naming</phase>
<phase name="8">  Master.php: Event schema validation, API contract testing, service boundary respect</phase>
<phase name="9">  Brain.php: Multi-service orchestration, cross-domain delegation, event saga coordination</phase>
<phase name="10">
</phase>
<phase name="11">Project Includes: Suggested MicroserviceBoundaries.php, EventSchemas.php</phase>
<phase name="12">Result: All three files enhanced with microservice awareness</phase>
<phase name="13">Insights: 12 cross-cutting concerns stored</phase>
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