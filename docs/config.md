## Decompile

Author: Jonathan Becker <jonathan@jbecker.dev\>

Version: v1.0.0

___

### Usage

```
heimdall -m config
```

### Optional Arguments

| Argument | Alias      | Required | Variable | Description                           |
| -------- | ---------- | -------- | -------- | ------------------------------------- |
| -open    | --edit     | NO       | N/A      | Edit the config file from the command line |

### Postprocessing Values

After decompiling a contract, you might find that you see some weird, non-solidity values within ``decompiled.sol``. These values are values that weren't postprocessed correctly, and will be fixed in the future.

- ``MASK{value & value}`` : A masking, usually a conversion from one type to another.
- ``LOAD{value}`` : Loading a variable from storage

### Known Issues and TODOs

Known issues are present in the issues tab on this repository. They will be marked with a decompiler tag and have other descriptors added.

### Notice

This module is very experimental, and is still being improved and developed. If you find something weird, open an issue. I also haven't had a chance to add comments, so don't flame me for that.