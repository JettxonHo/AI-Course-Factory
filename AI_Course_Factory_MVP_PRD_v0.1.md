# AI Course Factory MVP PRD v0.1

## Document Information

-   Project: AI Course Factory
-   Version: MVP v0.1
-   Phase: Phase 1.1
-   Document Type: Product Requirement Document
-   Status: Draft

## 1. Product Overview

AI Course Factory is an AI Agent driven knowledge content production
system.

It converts knowledge sources such as: - GitHub Repository - Technical
Documentation - Knowledge Assets

into: - Educational short videos - Teaching content - Social media
content

MVP positioning:

AI Course Factory is not an AI video generator. It is an AI Creator
knowledge content production assistant.

## 2. Product Vision

Long term:

AI Knowledge-to-Content Factory

Evolution:

AI Course Factory -\> ContentOS Core -\> Multiple Content Factories

## 3. Target User

Primary User:

AI Content Creator

Examples: - AI educators - Technical bloggers - Independent developers -
AI content producers

## 4. User Pain Points

1.  High knowledge research cost.

2.  Complex content production workflow: Research -\> Topic -\> Script
    -\> Storyboard -\> Production -\> Editing

3.  Difficulty scaling high-quality content production.

## 5. MVP Goal

Validate:

Knowledge Source -\> AI Understanding -\> Content Planning -\>
Production -\> Video Output

Demo input:

Microsoft AI-For-Beginners GitHub Repository

Demo output:

Episode 01: AI是什么？

Including: - Script - Storyboard - Timeline - Video

## 6. MVP Demo Specification

Theme:

小土豆学 AI

Video: - Aspect ratio: 9:16 - Style: Light educational style -
Background: White - Line style: Black - Character: Potato IP - Accent
color: AI Blue

## 7. User Flow

GitHub Repo Input

↓

Knowledge Analysis

↓

Course Planning

↓

Script Generation

↓

Storyboard Generation

↓

Timeline Generation

↓

Production

↓

Final Review

↓

Export

## 8. Functional Requirements

### FR-001 Knowledge Source Connector

Support GitHub Repository input.

Output: Knowledge Artifact.

### FR-002 Knowledge Agent

Understand source knowledge.

### FR-003 Content Agent

Generate course structure and scripts.

### FR-004 Production Agent

Generate storyboard and timeline.

### FR-005 Renderer

MVP uses Omni Hybrid Renderer.

### FR-006 Voice Generation

Use unified TTS strategy.

### FR-007 Human Review

Required: - Script Review - Final Video Review

Optional: - Storyboard Review

### FR-008 Artifact Version Management

Support versioning.

When upstream artifacts change, downstream artifacts become stale.

## 9. Agent Design

Knowledge Agent: - Knowledge understanding

Content Agent: - Teaching design and scripts

Production Agent: - Media production coordination

Reviewer Agent: - Quality evaluation

## 10. Skill Requirements

Knowledge Skills: - GitHub Parser

Creative Skills: - Storyboard Generator - Character Skill

Production Skills: - Voice Skill - Subtitle Skill - Omni Renderer

Infrastructure: - Artifact Storage - Asset Registry

## 11. Artifact Requirements

Core artifacts:

-   Knowledge Artifact
-   Script Artifact
-   Storyboard Artifact
-   Timeline Artifact
-   Audio Artifact
-   Asset Artifact
-   Video Artifact

Base structure:

``` json
{
  "id": "",
  "version": "",
  "status": "",
  "dependencies": []
}
```

## 12. UI Information Architecture

MVP uses:

Artifact-centric Single Task Workspace

Contains:

Input: - GitHub URL

Workflow: - Agent status

Artifacts: - Knowledge - Script - Storyboard - Timeline - Video

Review: - Approve - Reject - Regenerate

## 13. Non-functional Requirements

-   Checkpoint support
-   Partial execution
-   Renderer replaceability
-   Future knowledge source expansion

## 14. MVP Non-goals

Not included:

-   SaaS account system
-   Multi-user
-   Workspace
-   Automatic publishing
-   Skill Marketplace
-   Multi-renderer management
-   Full ContentOS

## 15. Acceptance Criteria

Input:

One GitHub Repository

Output:

-   Knowledge Artifact
-   Script Artifact
-   Storyboard Artifact
-   Timeline Artifact
-   Video Artifact

User can:

-   Review script
-   Modify artifacts
-   Continue from intermediate checkpoint
-   Preview final video

## 16. Next Stage

PRD

↓

Technical Spec

↓

Implementation Spec

↓

Coding
