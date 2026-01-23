Problem Statement 2
Agentic Honey-Pot for Scam Detection & Intelligence Extraction
1. Introduction
Online scams such as bank fraud, UPI fraud, phishing, and fake offers are becoming increasingly adaptive. Scammers change their tactics based on user responses, making traditional detection systems ineffective.
This challenge requires participants to build an Agentic Honey-Pot — an AI-powered system that detects scam intent and autonomously engages scammers to extract useful intelligence without revealing detection.
2. Objective
Design and deploy an AI-driven honeypot system that can:
Detect scam or fraudulent messages
Activate an autonomous AI Agent
Maintain a believable human-like persona
Handle multi-turn conversations
Extract scam-related intelligence
Return structured results via an API
3. What You Need to Build
Participants must deploy a public REST API that:
Accepts incoming message events
Detects scam intent
Hands control to an AI Agent
Engages scammers autonomously
Extracts actionable intelligence
Returns a structured JSON response
Secures access using an API key

4. API Authentication
x-api-key: YOUR_SECRET_API_KEY
Content-Type: application/json
5. Evaluation Flow
Platform sends a suspected scam message
Your system analyzes the message
If scam intent is detected, the AI Agent is activated
The Agent continues the conversation
Intelligence is extracted and returned
Performance is evaluated
6. API Request Format (Input)
Each API request represents one incoming message in a conversation.
6.1 First Message (Start of Conversation)
This is the initial message sent by a suspected scammer. There is no prior conversation history.
{
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
    "timestamp": "2026-01-21T10:15:30Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
6.2 Second Message (Follow-Up Message)
This request represents a continuation of the same conversation.
Previous messages are now included in conversationHistory.
{
  "message": {
    "sender": "scammer",
    "text": "Share your UPI ID to avoid account suspension.",
    "timestamp": "2026-01-21T10:17:10Z"
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Your bank account will be blocked today. Verify immediately.",
      "timestamp": "2026-01-21T10:15:30Z"
    },
    {
      "sender": "user",
      "text": "Why will my account be blocked?",
      "timestamp": "2026-01-21T10:16:10Z"
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
6.3 Request Body Field Explanation
message (Required)
The latest incoming message in the conversation.
Field
Description
sender
scammer or user
text
Message content
timestamp
ISO-8601 format

conversationHistory (Optional)
All previous messages in the same conversation.
Empty array ([]) for first message
Required for follow-up messages

metadata (Optional but Recommended)
Field
Description
channel
SMS / WhatsApp / Email / Chat
language
Language used
locale
Country or region

7. Agent Behavior Expectations
The AI Agent must:
Handle multi-turn conversations
Adapt responses dynamically
Avoid revealing scam detection
Behave like a real human
Perform self-correction if needed
8. Expected Output Format (Response)
{
  "status": "success",
  "scamDetected": true,
  "engagementMetrics": {
    "engagementDurationSeconds": 420,
    "totalMessagesExchanged": 18
  },
  "extractedIntelligence": {
    "bankAccounts": ["XXXX-XXXX-XXXX"],
    "upiIds": ["scammer@upi"],
    "phishingLinks": ["http://malicious-link.example"]
  },
  "agentNotes": "Scammer used urgency tactics and payment redirection"
}
9. Evaluation Criteria
Scam detection accuracy
Quality of agentic engagement
Intelligence extraction
API stability and response time
Ethical behavior
10. Constraints & Ethics
❌ No impersonation of real individuals
❌ No illegal instructions
❌ No harassment
✅ Responsible data handling
11. One-Line Summary
Build an AI-powered agentic honeypot API that detects scam messages, handles multi-turn conversations, and extracts scam intelligence without exposing detection.
