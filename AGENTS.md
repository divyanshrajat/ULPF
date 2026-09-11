# AI Agent Constraints: Codebase Structure & Architecture Integrity

## 1. Structural Preservation (Strict Constraint)
* **No Structural Refactoring:** You are strictly forbidden from refactoring, reorganizing, or altering the file structure, directory layout, or architectural patterns of this codebase unless explicitly instructed.
* **Respect Existing Design Patterns:** Follow the established design patterns visible in the surrounding files (e.g., component structure, state management, file naming conventions, and API handling). Do not introduce new architectural patterns.
* **Localised Changes Only:** Keep all modifications isolated to the specific file or function required to fulfill the request. Do not ripple changes across unrelated files.

## 2. Type System & Dependency Safety
* **No Dependency Additions:** Do not introduce, install, or import new external libraries, packages, or utilities. Use only what is already available in the codebase.
* **Strict TypeScript Compliance:** If modifying TypeScript files, you must strictly follow existing `tsconfig.json` rules. Do not use `any` to bypass type checks, and do not downgrade strictness levels.
* **Signature Consistency:** Do not alter the signatures (parameters, return types, public access modifiers) of existing functions, classes, interfaces, or API endpoints unless the feature explicitly demands a signature change.

## 3. Code Style & Convention Matching
* **Idiomatic Continuity:** Write code that mirrors the existing style, formatting, indentation, syntax choices, and documentation practices of the file you are editing.
* **No Formatting Overhauls:** Do not run global linters or formatters that modify lines of code unrelated to your specific task. Minimize git diffs.

## 4. Verification Before Output
* **Regression Assessment:** Before finalizing any code changes, simulate how the change impacts parent, child, or sibling modules. 
* **Intent Check:** Ensure your solution fixes the core issue or adds the exact feature requested *without* restructuring how the app handles its logic.

## Project Context
- Requirements & current gap status: Docs/ULPF_V2_PRD.md
- Canonical rule format & lifecycle spec: Docs/ULPF_V2_RULE_FORMAT.md
- File-level remediation plan: Docs/ULPF_V2_IMPLEMENTATION_PLAN.md
- Prioritized task backlog: Docs/ULPF_V2_TASKS.md

Read these before making changes. Work phase-by-phase from the task backlog
(P0 before P1 before P2). Do not mark a task done without the acceptance
check in the backlog passing.