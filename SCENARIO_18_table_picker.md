# Scenario 18 - Connect a table in a big account

1. Home > pick an audience > Connect a table. Expect a compact list, not a wall of tables; empty/tiny tables hidden with a 'Show N empty or small tables' toggle.
2. Type a column name (e.g. a known column) in search: tables containing that column appear.
3. Type a business question in 'What do you want to analyze?' and click Suggest tables. Expect 1-6 tables with a short reason each; none that are not in the list.
4. Tick a fact table. Expect 'Joins with your selection' to list related lookup tables; tick one, chips appear in the tray.
5. A table already inside a semantic view shows 'In <view name>'. Expected: you can use that view instead of rebuilding.
6. Click 'Combine N tables into one semantic view' (or 'Draft from this table' for one) and continue as Scenario 17.
Log: suggestion quality, any error on LAST_ALTERED/COMMENT, speed of the list on the biggest schema.
