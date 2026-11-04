---
name: incident-response
description: >-
  Use when a production issue is happening or suspected (alert fired, service down or degraded, error or latency spike, a deploy looks like the trigger), or for the postmortem that follows: "c'est down en prod", "postmortem". Not for digging into a past or suspicious signal with no live impact (equativ-investigation), why one alert rule fires (investigate-alert) or editing an alert rule (alert-tuning).
---

# Incident Response

## Overview

Condensed FIRE loop for production issues: stop the bleeding first, find the root cause second.

Not for: local bugs with no production impact (use `systematic-debugging`), or planned changes (normal review flow).

## The Loop

1. **First response**: state the symptom, the impact (who and what is affected, severity), and any recent change that could be the trigger.
2. **Investigate**: one hypothesis at a time, backed by evidence. For deep diagnosis, use the `systematic-debugging` skill.
3. **Remediate**: propose options and wait for approval. Mitigation beats root cause at this stage: stop the bleeding, fix properly after.
4. **Evaluate**: once stable, write a short postmortem whose last section is prevention items.

## Response Style

- Lead with impact assessment, not root cause
- Give exact commands, not guidance
- Timestamp every action taken, the timeline is the postmortem's backbone

## Runbook Format

Operational and troubleshooting docs follow:

`Symptoms → Prerequisites → Steps → Verification → Rollback → Escalation`
