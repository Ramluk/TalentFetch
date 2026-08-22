# TalentFetch build plan

## Milestone 1 — working addon shell

- [x] Retail addon skeleton
- [x] Current class/spec detection
- [x] Build list UI
- [x] Blizzard import integration point
- [x] No protected Apply action automation

## Milestone 2 — Wowhead data

- [ ] Identify Wowhead's current recommended-build endpoints/pages for Retail
- [ ] Resolve all class/spec/hero-spec build records
- [ ] Store Blizzard-compatible import strings
- [ ] Generate `TalentFetch_Data.lua`
- [ ] Add scheduled GitHub Action to refresh data

## Milestone 3 — polished UX

- [ ] Integrate into Blizzard talent/loadout UI instead of standalone `/tf` window
- [ ] Role/content tabs: Mythic+, Raid, PvP, Delves
- [ ] Current-build highlighting
- [ ] Last-updated timestamp
- [ ] Build search
- [ ] Import error explanations
- [ ] Tree-hash/serialization mismatch warnings

## Milestone 4 — quality

- [ ] Unit tests for data generation
- [ ] Test every Retail class/spec
- [ ] Patch-version CI validation
- [ ] CurseForge/Wago packaging
- [ ] Optional companion updater if we want near-real-time data without waiting for addon-manager distribution
