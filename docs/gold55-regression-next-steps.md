# Gold 55 regression prerequisites

- Gold dataset: 55 sentences / 56 approved interpretation sets; G046 has two valid interpretations.
- The unified gold and comparator are local artifacts; they are NOT yet committed to this branch.
- A trained `en_core_web_sm` model and an adapter from analyzer output to main-clause S/V/O/C/M character spans are required before accuracy can be measured.
- Compare an entire interpretation variant at once. Never combine labels from two interpretations.
- G051 uses discontiguous verb spans (`did ... realize`).
- First test main-clause labels; 45 sentences still lack full subordinate/modifier gold detail.
- Do not alter main or Render production until the test results are reviewed.
