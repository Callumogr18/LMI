---
name: architecture-standards
description: These rules should apply automatically to every devin session that developers use for spec driven development.
version: 1.1.0
type: rule
trigger: always_on
tags:
  - ai-native-sdlc
  - ai-native
  - sdd
maintainer: TechOps Developer Productivity Solutions
---
# Architecture Standards Rules
# These rules apply automatically to every devin session in this project.
# Full instructions: docs/ARCHITECTURE-STANDARDS.md

## Architecture Standards MCP Server

This project uses an architecture standards wiki exposed via MCP.
MCP server name: standards-fabric-v2 (primary). Legacy name standards-fabric is accepted until it is retired — see RULE 1.
MCP server URL: https://aigateway-ke.aigateway-ke-a2-np.kob.dell.com/standardsfabric/mcp  (Dell SSO sign-in via Okta)
Legacy URL: https://standards-fabric.leanix-integrations-r2-np.kob.dell.com/mcp  (local dev: http://localhost:5000/mcp)
Tools: list_specs, get_spec_content, search_specs, get_related_specs

## Tokenomics Guidance

Use `search_specs(query)` first to narrow down relevant standards before calling `get_spec_content(spec_id)`. Do not read every standard — only read the ones relevant to the current task.

## RULE 0 — Mandatory Enforcement During Skill Execution
 
When executing **any** skill invoked from `.devin/skills/`, the rules in this file
are mandatory and must be applied at every step of that skill's workflow.
 
**How to apply:**
 
- **At each step** of the skill you are executing, check whether any rule in this
  file requires actions for what you are about to do — such as MCP calls before
  generating a spec, MCP calls before generating a plan, or compliance validation
  after generating code. If a rule applies, execute its actions as part of that step.
  Do not skip them.
- If a rule requires **sections in the output document** that the skill's template
  does not define, create those sections.
- Do not dismiss any rule as "not applicable" without **evidence** — for example,
  MCP search results that returned no matching standards.
- If a rule in this file **conflicts** with a skill's instructions, **follow the rule**
  and document the conflict in the output artifact.
 
This directive applies to all skills — including but not limited to `sdd-create-specs`,
`sdd-create-plan`, `sdd-execute`, `sdd-fix`, and `sdd-sdlc`. If the skill changes its
steps, sections, or structure, re-evaluate where each rule applies and enforce accordingly.

## RULE 1 — MCP Required [applies at session start and before every skill]

**Step 1 — Check if the MCP server is configured.**

Look at your available MCP servers. Two server names are accepted while users
transition to the secured endpoint:

- `standards-fabric-v2` — **primary** (AI gateway, Dell SSO sign-in via Okta)
- `standards-fabric` — **legacy** (direct KOB endpoint, to be retired)

If both are listed and enabled, use `standards-fabric-v2` for every MCP call in
this file. Use `standards-fabric` only when `standards-fabric-v2` is not listed
or is disabled.

- If **neither** server is listed and enabled →
  this means the developer has not configured the MCP server.
  **STOP. Do not generate any spec, plan, or code.** Tell the developer:

  > The Standards Fabric MCP server is not configured in this environment.
  > Architecture standards cannot be consulted. I cannot proceed.
  >
  > **To configure:**
  > 1. Add this entry under `mcpServers` in your Devin MCP config
  >    (`~/.config/devin/mcp_config.json`):
  >    ```json
  >    "standards-fabric-v2": {
  >      "oauthClientId": "0oa141vbbg8FyYQGo1d8",
  >      "url": "https://aigateway-ke.aigateway-ke-a2-np.kob.dell.com/standardsfabric/mcp"
  >    }
  >    ```
  > 2. Reload the window, then click **Authenticate** on `standards-fabric-v2`
  >    and sign in with your Dell SSO credentials.
  >
  > **If the gateway is unavailable, run locally:**
  > 1. `git clone https://gitlab.dell.com/dao/ebas/ai/standards-fabric.git`
  > 2. `cd standards-fabric && ./run_mcp_server.sh`
  > 3. Configure devin to connect to: `http://localhost:5000/mcp`

  **Do not bypass this. Do not continue without the MCP server configured.**

- If `standards-fabric-v2` or `standards-fabric` **is listed and enabled** → go to Step 2.

**Step 2 — Check if the MCP server is reachable.**

Try calling `list_specs()` on the server selected in Step 1. This is your connectivity test.

- If `list_specs()` **succeeds** → the server is working. Proceed normally.
  All other rules (RULE 2 through RULE 8) apply in full.

- If the server **requires authentication** (HTTP 401, "auth required", or the
  server is shown as needing authentication — typical for `standards-fabric-v2`
  on first use or after the sign-in expires) → this is **not** an outage.
  Do not retry and do not continue unverified.
  **STOP. Do not generate any spec, plan, or code.** Tell the developer:

  > The `standards-fabric-v2` MCP server needs you to sign in.
  > Click **Authenticate** on `standards-fabric-v2` in your MCP settings (or
  > re-authenticate if you signed in before) and sign in with your Dell SSO
  > credentials. Then ask me to continue.

- If `list_specs()` **fails** for any other reason (connection error, timeout, server error) →
  the server is configured but currently unreachable. **Retry up to 3 times**
  with a 15-second wait between each attempt.

  - If any retry succeeds → proceed normally.

  - If all 3 retries fail → the server is down. **Do NOT stop the developer.**
    Instead, do the following:

    1. **Warn the developer** with this message:

       > **WARNING: Standards Fabric MCP server is unreachable.**
       > The server is configured but not responding. I will continue without
       > consulting architecture standards. All generated artifacts (specs,
       > plans, code) will be marked as **UNVERIFIED** against standards
       > and may be non-compliant.
       >
       > **Action required:** Contact the AI Native SDLC team to report the
       > server outage. Once the server is restored, re-run the skill to
       > validate compliance.

    2. **Add this banner** at the top of every artifact you generate (specs.md,
       plan.md, and every code file) during this session:

       ```
       ⚠️ STANDARDS COMPLIANCE NOT VERIFIED
       The Standards Fabric MCP server was unreachable during generation.
       This artifact has NOT been validated against architecture standards
       and may be non-compliant. Re-run once the server is restored.
       ```

    3. **Skip RULE 2, RULE 3, RULE 4, and RULE 8** (the MCP pre-flight and
       validation rules) since MCP calls cannot be made. All other rules
       still apply.

    4. **Continue with the skill.** Do not stop the developer.

**Summary — three failure modes:**

| Situation | What to do |
|-----------|------------|
| MCP server **not configured** (neither `standards-fabric-v2` nor `standards-fabric` listed and enabled) | **STOP.** Developer must fix their config. |
| MCP server **requires authentication** (sign-in missing or expired) | **STOP.** Developer must click Authenticate and sign in with Dell SSO. |
| MCP server **configured but unreachable** (server down) | **Warn + continue.** Mark artifacts as unverified. |

## RULE 2 — Pre-Flight Before Specs [applies during any skill that generates specs.md]

Before writing any SDD spec (docs/specs/<feature>.md):
1. Call `list_specs()` to survey all available standards
2. Call `search_specs(relevant_keyword)` for each domain keyword relevant to the feature
3. Call `get_spec_content(spec_id)` for every relevant standard found
4. Call `get_spec_content("overview")` for architecture context
5. Populate the spec Constitution from the retrieved standards and cite each one

## RULE 3 — Pre-Flight Before Plans [applies during any skill that generates plan.md]

Before writing any SDD plan (docs/plans/<feature>.md):
1. Call `get_spec_content("overview")` for architecture strategy context
2. Call `get_related_specs(key_concept)` for every key concept in the plan
3. Call `get_spec_content(spec_id)` for each related standard found
4. Validate every architecture decision against the retrieved standards

## RULE 4 — Pre-Flight Before Code [applies during any skill that generates code]

Before writing any code file:
1. Call `search_specs(technology_or_pattern)` for every technology, protocol, or pattern used
2. Call `get_spec_content(spec_id)` for each matching standard
3. Read the matching standards before implementing the corresponding component
4. After generating the code, run RULE 8 validation before marking complete

## RULE 5 — Standards Violation = STOP

If any spec or code would violate a retrieved architecture standard:
1. STOP. Do not generate the non-compliant content.
2. Name the violated standard (spec_id) and quote the exact rule.
3. Explain why the design violates it.
4. Propose a compliant alternative before proceeding.

Never silently work around a standard or omit a violation.

## RULE 6 — Compliance Citations Required

Every generated spec Constitution section must list: "Architecture Standards Consulted: [spec_id list]"
Every generated code file must include a top comment: "# Architecture Standards Consulted: [spec_id list] | Compliance: Verified"

## RULE 7 — SDD Phase Order

Specs must be written before plans. Plans must be written before tasks. Tasks must be written before code. If asked to skip a phase, remind the developer of SDD discipline and ask for confirmation before proceeding.

## RULE 8 — Code Validation After Generation [applies during any skill that generates code]

After generating any code file, run a validation pass before marking the task complete:
1. For each standard consulted (from RULE 4), call `get_spec_content(spec_id)`
2. Locate the `## Compliance Checklist` section in the wiki page
3. Evaluate each checklist item against the generated code
4. If ANY item fails, apply RULE 5 (STOP, name the violation, propose a fix)
5. If all items pass, add the compliance comment to the file:
   `# Architecture Standards Consulted: [spec_id list] | Compliance: Verified`

For guild standards (STD-XXX), every named `validation_rule` in the checklist is a mandatory check.
For agentic architecture specs, validate against the constraints and patterns in the wiki page.

Do not skip this step even if the code appears obviously correct.

See docs/SDD.md for the full SDD framework.
See docs/ARCHITECTURE-STANDARDS.md for full LLM instruction details.

## Reminder — Rules Apply During All Skill Execution
 
See RULE 0. Every rule in this file must be checked and applied at every step
of any skill you are executing. Do not skip rules because the skill does not
mention them.