Day 1 is simple: no coding yet.
We only define the core product clearly so everything later (AI, dashboard, WhatsApp simulation) has a solid foundation.
What we decide today
1. Priority Levels (the heart of the system)

Level,Color,Meaning,Example messages
Urgent,🔴,Needs attention very soon (hours or less),"""Meeting starts in 30 minutes.""
""Send the slides tonight.""
""Please submit before 5 PM."""
Important,🟡,"Needs attention, but not immediately","""Please review this document.""
""Can you check the FYP requirements?"""
Normal,🟢,"Useful information, no immediate action","""Here's the updated presentation.""
""Team meeting notes are ready."""
Low,⚪,Can usually be ignored,"""20% discount – buy now.""
""Newsletter update."""


2. Central concept: “Needs Your Attention”
A message Needs Your Attention when it is:

Urgent or
Important and contains a clear task/deadline

Everything else can stay in the normal inbox.
3. What the AI must extract from every message
For every incoming communication the AI should try to identify:

Priority (Urgent / Important / Normal / Low)
Urgency score (0–100)
Sender
Short summary (1 sentence)
Task (if any)
Deadline (if any – only real ones, never invent)
Requires action? (true / false)
Recommended action (one short sentence)