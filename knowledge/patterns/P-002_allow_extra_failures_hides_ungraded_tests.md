# P-002: allow_extra_failures hides ungraded patch tests

**Status:** approved  
**Reusable:** yes

## Pattern

When `allow_extra_failures` is true, only graded `fail_to_pass` / required lists gate reward. Meaningful tests sitting only in `tests.patch` can fail while reward stays 1.0.

## What to do

Promote critical patch tests into `fail_to_pass` or remove untested instruction claims.
