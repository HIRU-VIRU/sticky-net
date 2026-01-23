Problem Description

Participants are required to build an AI-powered Agentic Honey-Pot system that detects scam messages and autonomously engages scammers to extract actionable intelligence such as bank account details, UPI IDs, and phishing links through multi-turn conversations.

Problem, Input & Output Guidelines

Participants must strictly adhere to the official problem definition, API input format, and response structure.

Interaction Source: Scam conversations will be simulated using a Mock Scammer API, which sends message events to the participant’s API.

Submission Requirement: Participants must deploy a public API endpoint secured with a user-provided API key.

Agent Handoff: Once scam intent is detected, the system must hand over the interaction to an autonomous AI Agent capable of continuing the conversation independently.

Reference Documentation:

    ./DOCUMENTATION.md

Objective

Analyze incoming messages to detect scam intent and activate an autonomous AI agent that maintains a believable human persona, engages scammers strategically, and extracts high-value scam intelligence for evaluation and reporting.

Processing Expectations

    Accept incoming scam messages via API requests
    Support multi-turn conversations using conversation history
    Detect scam intent without false exposure
    Engage scammers autonomously after detection
    Extract and return structured intelligence
    Ensure stable responses and low latency

Agent Responsibilities

    Maintain realistic and adaptive conversation flow
    Use reasoning, memory, and self-correction
    Avoid revealing scam detection
    Extract bank account numbers, UPI IDs, and phishing URLs

Evaluation & Metrics

Each submission will be evaluated using measurable metrics generated through the Mock Scammer API, including:

    Accuracy of scam detection
    Engagement duration
    Number of conversation turns
    Quality and completeness of extracted intelligence

Expected Output Structure

The API response must return a structured JSON output containing scam detection status, engagement metrics, and extracted intelligence in the defined format.
