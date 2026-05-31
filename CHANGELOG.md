# CHANGELOG

<!-- version list -->

## v1.5.1 (2026-05-31)

### Bug Fixes

- **config**: Divide keys and settings so that a user can share their .config safely
  ([`dde2155`](https://github.com/nachollorca/lmti/commit/dde21551166cbf2095f7ee98632ef642640a2a02))

### Documentation

- Document the stream rendering problem
  ([`7532f2b`](https://github.com/nachollorca/lmti/commit/7532f2b4bf76e4d6d450a3e29a27b858dab0fb03))


## v1.5.0 (2026-05-01)

### Continuous Integration

- Remove duplicated arguments from prek in ci
  ([`15ac121`](https://github.com/nachollorca/lmti/commit/15ac121aef1e31906fdbe7026a420a43dd74343b))

- Upgrade template to mold
  ([`90e2ac0`](https://github.com/nachollorca/lmti/commit/90e2ac0a53257ca39298accb6f612b3953eac0a0))

### Documentation

- Add demo gif
  ([`1971063`](https://github.com/nachollorca/lmti/commit/1971063f65f748aaead807482a59bf91bab48ea1))

- Be consistent with sections in readme
  ([`7a98f0e`](https://github.com/nachollorca/lmti/commit/7a98f0e65591ea1d5363959587e648063a964677))

- Put some dashes in the FAQ because it was making me nervous
  ([`4d75bac`](https://github.com/nachollorca/lmti/commit/4d75bac7fd93976b9c79eb1469b411d9c218f1db))

- Revise README content and fix typos
  ([`559e280`](https://github.com/nachollorca/lmti/commit/559e280014377f52adff7d8cc77d5edf88a0d99a))

### Features

- **config**: Make custom models introduced by the user persistent
  ([`256f5b9`](https://github.com/nachollorca/lmti/commit/256f5b93df290eac599a2f26cf95e88fdfb02432))

### Testing

- Add tests scaffolding with shared console and prompt fixtures
  ([`b3512dd`](https://github.com/nachollorca/lmti/commit/b3512ddc8236db74a8c44139effd908ecd12062f))

- Cover cli entry point and repl loop
  ([`8ea080b`](https://github.com/nachollorca/lmti/commit/8ea080b1286508b50842652bf25de72f600990f8))

- Cover command registry and dispatch
  ([`723dd6a`](https://github.com/nachollorca/lmti/commit/723dd6a554a5f45bf6f50aed79f2677e55b1a033))

- Cover config and history modules
  ([`291f686`](https://github.com/nachollorca/lmti/commit/291f686c1db5238e2b178aa985eb1f75f2dc8bae))

- Cover slash command handlers (undo, copy, model, history)
  ([`a29973f`](https://github.com/nachollorca/lmti/commit/a29973f7513d494cfcbda3cbdf5dcb37394f80af))

- Cover ui rendering helpers and error handlers
  ([`521bd86`](https://github.com/nachollorca/lmti/commit/521bd86cbbe25281a8c5e6d9b9f6d641eaf706e1))


## v1.4.0 (2026-04-05)

### Chores

- Remove residual TODO.md
  ([`83ed85f`](https://github.com/nachollorca/lmti/commit/83ed85fa3dee389ec0bec12bb1c4f5314f6d9c34))

### Documentation

- Updste structure
  ([`78de811`](https://github.com/nachollorca/lmti/commit/78de811194ebc5f00c5b1083d9424321ffd3b5b4))

### Features

- Add /undo command
  ([`be789d5`](https://github.com/nachollorca/lmti/commit/be789d586c3124b6ec36f04c8c21c8bebcbbdb7b))

- Implement /history , persist conversations
  ([`c19f87b`](https://github.com/nachollorca/lmti/commit/c19f87b8c255977dcd8787c9486208ab66b46752))


## v1.3.0 (2026-04-05)

### Chores

- Change some bindings
  ([`fe0f415`](https://github.com/nachollorca/lmti/commit/fe0f41533b288fddf1c85715fe954d681ca3c3c3))

- Remove wrong f string
  ([`2d2b074`](https://github.com/nachollorca/lmti/commit/2d2b07427475a03d72a0b9369a1fa82b0f30ea74))

### Features

- Gracefully exit on keyboard interrupt, improve key binding behavior
  ([`0e09c5d`](https://github.com/nachollorca/lmti/commit/0e09c5dd04d8efb837baee8fc8cdd1e363a32bae))

### Refactoring

- Make things better hjahajahaha
  ([`8484637`](https://github.com/nachollorca/lmti/commit/84846377833e17a7aa0dbaa914a34a7b162c118d))

- Solve questions
  ([`e4d452f`](https://github.com/nachollorca/lmti/commit/e4d452f23a0330eb228e78d90faea3492874ca44))

- Split tui into ui / commands / errors.
  ([`74e3bc2`](https://github.com/nachollorca/lmti/commit/74e3bc2b621fc339a09f9f39c0107003a2575ccf))

- Use the prompt_selection for models too, add an option for manual input (others)
  ([`6ab3eca`](https://github.com/nachollorca/lmti/commit/6ab3eca2258721dafa07c2ce692887a35032f413))


## v1.2.0 (2026-04-02)

### Chores

- Add anthropic models now that they are supported in lmdk
  ([`795e2f9`](https://github.com/nachollorca/lmti/commit/795e2f9c67ccae6a8fa012ecfefda5c633a4d8df))

### Documentation

- Remove expander in readme, add placeholder for commands help
  ([`f0b1b9b`](https://github.com/nachollorca/lmti/commit/f0b1b9b48b121a0cb4cf53c12bbfa84825d35074))

### Features

- Add /copy command
  ([`133b79a`](https://github.com/nachollorca/lmti/commit/133b79a917f585bbeb94385e15b88c27377d9ad2))


## v1.1.0 (2026-03-27)

### Bug Fixes

- Ensure we can render weird chars
  ([`522503a`](https://github.com/nachollorca/lmti/commit/522503aa7d4fecea6bbbf257d3d3fee9089c1344))

### Chores

- Add more models to list
  ([`f25ecce`](https://github.com/nachollorca/lmti/commit/f25ecce8af02620601d4c8cb32c9850b7d931fc5))

### Continuous Integration

- Use public lmdk in ci/cd
  ([`f08e181`](https://github.com/nachollorca/lmti/commit/f08e181a90d9af44683d5cc3b6583479686fe844))

### Documentation

- Add a cool readme
  ([`44b5743`](https://github.com/nachollorca/lmti/commit/44b5743451c41cfb2522466d4b56f00155a0a19a))

### Features

- Add system instruction
  ([`8b42a28`](https://github.com/nachollorca/lmti/commit/8b42a28d2c0cf77e83550ae12724ac6ca7145567))

- Update models with new updates
  ([`2078869`](https://github.com/nachollorca/lmti/commit/20788694df9860c95af7b70c7221847b84d82ef8))


## v1.0.1 (2026-03-25)

### Bug Fixes

- Trigger release lol
  ([`cded674`](https://github.com/nachollorca/lmti/commit/cded674f25039253e5a68fa3d5691a79e2473f44))


## v1.0.0 (2026-03-24)

- Initial Release
