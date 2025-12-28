# palma
<img width="1920" height="1080" alt="palma" src="https://github.com/user-attachments/assets/c0effdfc-5d02-41f4-86f0-59245b58b4c3" />

**Palma.** _Your companion to being a better you. A hackathon project._

## Why PALMA?
Most health apps rely on aggressive metrics, constant reminders, and device-heavy tracking.
This leads to:
- false reporting
- anxiety around food
- user not achieving their goal
- users abandoning the app entirely

_Palma explores a different approach - reflection over enforcement._

## What is PALMA?
PALMA is a web-based wellness application that helps users achieve their dietary goals, reflect on their daily food and habits
using indirect, _healthy,_ non-judgmental prompts.

Instead of punishing calories or constant alerts, PALMA:
- frames food positively.
- nudges gently.
- uses reason instead of just metrics.
- builds honesty & trust over time.

We utilise Foot-in-the-Door technique and consistency bias: The idea being if the user commits to a "truthful persona" through easy, indirect questions, they are more likely to maintain that integrity when things get personal (like what they ate). Thus helping reduce false reporting.


## Core Features
- Calm onboarding with diet preferences and goals.
- Daily reflection flow using _healthy_ questions.
- Designed with emotional UX in mind. (focused on reflection, not judgment)
- A daily Health Score based on consistency, value and balance, not perfection.
- Food logging with positive framing (no red warnings).
- Context-aware AI companion (non-medical use).
- Human-first and privacy-first design.

## Target Users & Use Cases

### Target Users
- Health-conscious individuals who feel overwhelmed by traditional calorie tracking apps.
- Users who value reflection, honesty, and long-term habit formation.
- People _without_ consistent access to wearables or who prefer minimal tracking.

### Use Cases
- Daily food reflection without guilt or calorie pressure.
- Gradual habit improvement through gentle nudges.
- Honest self-reporting enabled by non-judgmental prompts.

  
## Tech Stack
Frontend: HTML, CSS, JavaScript  
Backend: FastAPI  
Database: Supabase (Postgres)
API: Gemini 2.5 Flash API (free tier)

## Why an Agentic System?

PALMA is designed as an agentic system because the problem it addresses is not static.

User behavior, honesty, and motivation evolve over time.
A fixed-rule system or one-off chatbot cannot adapt to:
- changing user consistency
- fluctuating habits
- emotional context

PALMA’s agent observes patterns across reflections, food logs, and user responses,
then plans gentle, context-aware responses rather than issuing direct instructions.

_The agent’s role is not to control the user, but to adapt to them._

## Agent Design

### Reflection Agent
**Goal:**
- Encourage honest self-reflection.
- Craft indirect, emotionally-intelligent questions to collect user data and discourage false reporting. 
- Support gradual, sustainable dietary habits.

**Responsibilities:**
- Analyze user reflections and food logs.
- Detect consistency and balance trends.

**Constraints:**
- No medical diagnosis or treatment advice
- No calorie shaming or fear-based feedback
- No forced notifications or intrusive interventions
- Operates only within user-provided data

**The Correction Loop**
- We start with the Health score with basic 6 questions. Those 6 questions are tied to 6 different weights which play a role in final determination.
- We use calories, outside/inside food ratio and combine it with the above - to derive the health score.
- The health score is then added into the database
- There are various goals which users can choose from, and each health score is basically a difference (or delta) from that goal, and hence we use that to reprompt the questions such that it is psycologically more likely that user moves towards the goal. 

## Demonstration of Agentic Behavior

Example:
- If a user frequently logs high-calorie meals but remains consistent and honest, the agent avoids negative feedback and instead suggests balance over restriction.
  It tries to connect the past responses of the indirect questions to the food habits. Like "consider reducing fats to feel better and lighter during the evenings."

This demonstrates autonomous decision-making under constraints.

## System Architecture & Workflow

1. User completes onboarding and sets preferences.
2. Daily reflection flow collects indirect, low-pressure inputs.
3. Reflection Agent evaluates patterns over time.
4. Agent plans a goal-aligned yet personal response.
5. AI companion communicates context-aware feedback.
6. Health Score is updated based on consistency and balance.

## Running locally
1. Clone the repo
2. Install backend dependencies
3. Run FastAPI server
4. Open frontend in browser

## Limitations & Future Improvements

### Limitations
- Relies on self-reported data.
- Not intended for medical use.
- Prototype-level personalization.

### Future Improvements
- Mobile application.
- More adaptive long-term planning.

## Project Status
Hackathon prototype – **under development.**

## Project by Prajwal .
_(also known as RealJupiter05/ Innovative Challenger)_
