# Study Management (shinyTree) - TODO

- [x] Create Git branch `shinytree`
- [x] Add `shinyTree` dependency to `admin-frontend/setup_environment.R`
- [x] Create UI module `admin-frontend/modules/study_tree_ui.R`
- [x] Create server module `admin-frontend/modules/study_tree_server.R`
- [x] Wire module into `admin-frontend/app.R` under Data Management → Study Management
- [x] Implement Add Study flow mirroring Studies module validation
- [x] Implement Add Child with context:
  - [x] Study → Database Release
  - [x] Database Release → Reporting Effort
  - [x] Disabled for Reporting Effort
- [x] Implement Edit for selected node (Study/Release/Effort)
- [x] Implement Delete with child checks mirroring list modules
- [x] Update docs (`admin-frontend/README.md`, `admin-frontend/CLAUDE.md`)
- [x] Extend frontend test plan JSON for Study Management tree scenario
- [ ] Write Playwright test to exercise tree UI end-to-end
  - [ ] Navigate to Study Management
  - [ ] Add Study → Add Release → Add Effort
  - [ ] Verify Add Child disabled on Effort
  - [ ] Edit each node
  - [ ] Attempt blocked delete then sequential deletes
  - [ ] Clean up created entities
- [ ] Run Playwright test and capture results
- [ ] Mark tasks complete upon passing test


