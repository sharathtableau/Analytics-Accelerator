# Demo FAQ: how the persona ideas work (27 Oct 2026)

**How are the ideas generated?**
At run time, in three steps, all inside the client's Snowflake account:
1. **Code finds what moved.** For the chosen persona (e.g. Chief Credit Officer) the app takes that role's metrics and compares the last 13 weeks with the same weeks last year, by segment or product, using governed `SEMANTIC_VIEW()` queries. For example: "Delinquency Rate by segment: Near-Prime Revolver worst at +2.7 pts".
2. **Cortex writes the ideas.** One `AI_COMPLETE` call (Claude Sonnet 4.5 on Snowflake Cortex, with fallbacks) gets the persona's role, what that role watches, its metrics, the available governed data and those movements, and proposes about 6 dashboard ideas.
3. **Code checks them.** Only real metrics from the semantic view, mostly the persona's own (one supporting metric allowed), no duplicates, nothing the data doesn't have. The "Why this idea" box shows the SQL result itself, not the AI's wording.

Ideas are saved for each persona and refreshed automatically when a new week of data arrives; "New ideas" asks for a fresh set at any time.

**Are we training a model?**
No. Nothing is trained or fine-tuned. Cortex uses a pre-trained model as it is, and we give it the context in the prompt each time (the persona, its guidance and the movements). Customer data stays in the account; Snowflake's Cortex terms say customer data isn't used to train the models (worth confirming the current wording with the Snowflake team).

**Is there a separate agent for each domain?**
Two different things:
- **Ideas are not an agent.** They are one Cortex call per persona per data week, checked by code.
- **Questions are answered by an agent, one per domain.** Each workspace (Retail, Finance, CPG) has its own Cortex Agent, built on that domain's semantic view (Cortex Analyst), its documents and ontology (Cortex Search), and a `log_decision` tool. That's what answers "Ask Cortex Agent" on a dashboard.

**Where does the persona come from?**
The built-in personas come from each domain's business ontology. What each role watches is stored as data in the app (reviewed; editable in the app, no code change). Anyone can add their own role with "+ Your role": Cortex drafts the persona from the workspace's metrics and it stays marked "not reviewed" until approved.

**Can it make up numbers?**
No. Every number on a tile or in "Why this idea" comes from governed SQL or Snowflake ML. Cortex only proposes; the validator checks every proposal, and dashboards are re-verified against the base tables before publishing.

**What does it cost?**
One AI_COMPLETE call plus a few small queries per persona per data week; viewing saved ideas costs nothing extra. Every Cortex call is logged with its tokens in the AI ledger (Governance & AI quality).

**Did you train the agent to pick charts and layouts?**
No, nothing is trained or fine-tuned. Chart and layout choices come from rules in code built from BI research (which chart suits which metric and audience, which layout each persona reads), plus a Cortex prompt that fills the layout with the right metrics. The validator checks every proposal against the semantic view. Say "guided by research-based rules", not "trained".

**Isn't Streamlit not enterprise grade?**
Streamlit is only the container that runs inside Snowflake (governance, sign-in, no data leaving the account). Everything you see is a React interface. If a client wants a React-only deployment, the same interface can be delivered that way.

**Is the semantic layer preloaded or generated?**
Both paths exist: the app uses an existing semantic view, or Cortex drafts one from the tables you pick (with the documentation as context) for a person to review. The metric definitions stay governed in the semantic view, so every dashboard uses the same numbers.
