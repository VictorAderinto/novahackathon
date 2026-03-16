# 🎬 Demo Script & Storyboard

**Goal:** Demonstrate the **Self-Healing Agentic Power Grid**.
**Theme:** "The Future of Grid Management is Proactive, not Reactive."

---

## 1. Intro: The Problem (0:00 - 1:00)
**🗣️ Say:**
> "Power grids are becoming increasingly complex with renewable energy and EV loads. When a line fails today, operators often rely on static tools and manual calculations, leading to cascading blackouts.
>
> We built a system that uses **Amazon Nova** to not just *monitor* the grid, but to *understand* it. Let me show you how our multi-agent system manages an IEEE 57-bus network."

---

## 2. Feature: Contextual Awareness (1:00 - 2:00)
**👉 Action:** Open the Dashboard.
**🗣️ Say:**
> "Here is our live dashboard. We have a 57-bus system running in real-time. Instead of querying SQL databases, I can just ask the system."

**⌨️ Type Prompt:**
```text
Summarize the current state of the grid.
```

**🗣️ Say (while waiting):**
> "The Orchestrator agent is now querying the network state. It doesn't just look up a value; it interprets the physical data."

**👀 Observation:**
> Point out the response. It should be accurate and data-backed (e.g., "Total load is ~1250 MW, no lines overloaded").

---

## 3. Feature: The "What-If" Simulation (2:00 - 4:00)
**🗣️ Say:**
> "This is where it gets interesting. Real-world operators need to know: 'What happens if a storm takes out a major transmission line?' Let's test that."

**👉 Action:** Type the following complex command.
**⌨️ Type Prompt:**
```text
Simulate an outage on Line 4 (connecting Bus 2 and 3). specificly, disconnect it and tell me the impact on system stability.
```

**🗣️ Say (while waiting):**
> "Behind the scenes, the **Scenario Builder** is creating a copy of the network. It's physically disconnecting that line in the simulation engine (Pandapower) and running a full AC power flow analysis. The Agents then inspect the *new* state."

**👀 Observation:**
> The system should report back. It might say "No violations" or "Overload detected on Line X".
> *If no violations:* "Great, the grid is N-1 secure."
> *If violations:* "See? It instantly identified a vulnerability."

---

## 4. Feature: Self-Healing / Mitigation (4:00 - 5:00)
**🗣️ Say:**
> "Now, I'll ask the agents to collaborate and fix the problem."

**⌨️ Type Prompt:**
```text
The system is under heavy load. Increase generation at Bus 12 by 50 MW and check if that relieves strain on neighboring lines.
```

**🗣️ Say:**
> "The **Region Agent** responsible for Bus 12 is evaluating this request against its local constraints. It's a Map-Reduce architecture: local agents solve local problems, and the Orchestrator ensures global stability."

---

## 5. Conclusion (5:00+)
**🗣️ Say:**
> "What you just saw wasn't a hardcoded demo. It was a probabilistic LLM reasoning about grid physics in real-time. This reduces operator response time from minutes to seconds."

---

## 🧪 Cheat Sheet: Copy-Paste Prompts

**1. Status Check (Easy)**
> `Summarize the current generation mix and tell me the highest voltage bus.`

**2. Line Outage (Medium)**
> `Simulate a disconnection of Line 10. Does this cause any voltage drops below 0.9 p.u.?`

**3. Complex Mitigation (Hard)**
> `I need to take Bus 3 out for maintenance. Can the system support the load without it? Propose a generation redispatch if needed.`

**4. Fun/Creative**
> `Explain the current state of the grid like a sci-fi ship captain.`
