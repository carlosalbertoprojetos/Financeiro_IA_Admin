# Timeline Validation — Real Board

**Date:** 2026-06-20  
**Board:** Original (`66c6308377ff5ddcb67c7fb9`)  
**Snapshot:** `docs/_validation_snapshot.json`

---

## Data Imported

| Entity | Count |
|--------|-------|
| Lists | 8 |
| Cards | 352 |
| Members | 2 |
| Trello actions | 7194 |
| Timeline events | 7194 |

**Date range:** 2024-08-21 → 2026-06-20 (nearly 2 years of history)

---

## Validation Checks

| Check | Result | Notes |
|-------|--------|-------|
| Events generated | PASS | 1:1 with actions persisted |
| Temporal ordering | PASS | `from` < `to` verified |
| Cards with events | PASS | 353 card references |
| Move detection | PASS | `CARD_MOVED` events present |
| Action mapping completeness | **PARTIAL** | High volume of `UNKNOWN` event types |

---

## Findings

### Positive

- Timeline engine correctly persists events from Trello actions.
- Historical depth supports risk scoring, bottleneck detection, and audit.
- Sync + timeline pipeline completes without errors on real production-scale board.

### Gap — UNKNOWN events

Many actions map to `TimelineEventType.UNKNOWN` because Trello action types are not fully mapped in `TRELLO_ACTION_MAP`. This does not block functionality but reduces semantic precision for:

- Comment events
- Label changes
- Custom power-up actions

**Recommendation:** Extend `TRELLO_ACTION_MAP` for `commentCard`, `addLabelToCard`, `removeLabelFromCard`, `updateCheckItemStateOnCard` variants.

---

## Conclusion

Timeline engine is **operational and temporally accurate** on real data. Mapping coverage should be improved to reduce UNKNOWN ratio below 30%.
