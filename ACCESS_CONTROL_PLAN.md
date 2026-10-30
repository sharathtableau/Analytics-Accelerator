# Access control: who sees which dashboard (PARKED 29 Oct 2026, high priority)

Roadmap row **4 / D3** in `ENTERPRISE_TRACKER.md`. Parked by Sharath on 29 Oct 2026 as one of the next priorities, to be picked up after the changes he is about to list. **Nothing here is built yet. Plan with Sharath before building; decisions below are still open.**

## The question (Sharath, 28 Oct)
"How would we know if a manager or an executive is logging in, so they see only their dashboards? Consider BI-tool behaviour."

## How it works today (from the code, 28 Oct)
- **Who is signed in:** the app knows the Snowflake **user name** (`st.user`, `viewer_ids()`), not the user's roles. Streamlit in Snowflake runs with the owner's rights, so `CURRENT_ROLE()` is the app owner's role.
- **Portal Share panel** (`portal_view._share_panel`, `app.save_sharing`):
  - **Roles:** only grants the role USAGE on the Portal app. It does **not** hide the dashboard from other roles.
  - **Only these users:** the only real filter (`app.visible_published`): when set, only those users (and the publisher) see the dashboard.
- **Executive / Manager / Operations** in the Portal are section headings from the dashboard's layout audience, not permissions.
- **Workspaces in the Portal:** the picker lists only domains that have dashboards visible to the viewer; the choice is remembered per viewer (`domain:<viewer>` in AA_APP_SETTINGS).
- **Result:** anyone who can open the Portal sees every published dashboard unless the publisher typed a user list.

## How BI tools do it
| | Tableau / Power BI | Accelerator today |
|---|---|---|
| Identity | Sign-in → user | Snowflake user (`st.user`) ✅ |
| Groups | Users in groups (Executives, Credit Managers…), synced from AD/Entra or managed in the tool | ❌ missing |
| Content permission | Project / app audience → allowed groups | Only a user list |
| What you see | Home shows only content your groups may open | Partly (user list only) |
| Row-level security | Same dashboard, a regional manager sees only their region | ❌ missing |

## Proposed plan
1. **Groups, managed in the app (admin-free).**
   - New "Access" page in the builder app: create groups (e.g. Executives, Credit Managers, Store Ops) and add Snowflake users. New table `AA_GROUPS` (group, members, workspace, default persona).
   - Each group maps to a workspace and a default persona (e.g. Credit Managers → Finance → Chief Credit Officer).
   - Later, when an admin is available: sync groups from Snowflake roles (needs IMPORTED PRIVILEGES on SNOWFLAKE; already on the "Needs an admin" list).
2. **Publish to groups.** At publish, choose audience groups, pre-filled from the persona the dashboard was built for. "Only these users" stays as it is.
3. **Portal shows only what your groups may open.**
   - Workspace picker lists only your domains.
   - Landing: "For you: <group>", with Executive / Manager / Operations sections only for dashboards you are entitled to.
   - A user in no group sees "No dashboards shared with you yet".
4. **Row rules (second step).** e.g. Region Managers see `region = <their region>`; the filter is added to every query; the agent is switched off for row-limited users so it cannot reveal totals; cache kept per rule.

**Nothing existing is removed:** "Only these users", Share links, direct dashboard links and builder behaviour stay. Guard tests for these before building.

## Open decisions (ask Sharath)
1. Who manages groups: only the app owner, or any builder?
2. Dashboards published before groups exist: visible to everyone (as today) until groups are assigned (suggested, nothing disappears), or hidden until assigned?
3. Scope of the first drop: groups + publish-to-groups + filtered Portal first, row rules after (suggested)?

## Before building
- Before/after mockup of the Portal landing and the Access page.
- List of affected features + guard tests (sharing panel, direct links, workspace picker, brief / snapshot in Portal).
- Tested locally with fake Snowflake + Playwright; then Sharath deploys:
  - `cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && deploy_enterprise.cmd`
  - `cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && deploy_portal.cmd`
