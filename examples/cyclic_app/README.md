# Cyclic app — intermediate

This project contains two intentionally circular groups:

```text
Two-module cycle:
cyclic_app.direct.mod_a → cyclic_app.direct.mod_b
cyclic_app.direct.mod_b → cyclic_app.direct.mod_a

Three-module cycle:
cyclic_app.long_cycle.mod_x → cyclic_app.long_cycle.mod_y
cyclic_app.long_cycle.mod_y → cyclic_app.long_cycle.mod_z
cyclic_app.long_cycle.mod_z → cyclic_app.long_cycle.mod_x
```

These files are graph-analysis fixtures. Their imports deliberately model undesirable coupling; do not use this design as an application architecture example.

Run:

```bash
depcycle inspect examples/cyclic_app --cycles
depcycle analyze examples/cyclic_app --fail-on-cycles --format dot -o cycles.dot
```
