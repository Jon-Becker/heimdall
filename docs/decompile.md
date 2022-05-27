## Decompile

Author: Jonathan Becker <jonathan@jbecker.dev\>

Version: v1.0.0-alpha

___

### Usage

```
heimdall -m decompile -t TARGET
```

### Optional Arguments

| Argument | Alias      | Required | Variable | Description                           |
| -------- | ---------- | -------- | -------- | ------------------------------------- |
| -t       | --target   | YES      | TARGET   | Target of operation (file or address) |
| -o       | --output   | NO       | PATH     | Custom output path                    |
| -c       | --chain    | NO       | ID       | Chain ID of target (if applicable)    |
| -p       | --provider | NO       | URL      | URL of provider / node. Will default to config value if not present |
| --default | N/A       | NO       | N/A      | Will automatically select default value when prompted during module execution |
| --flush  | --ignore-cache | NO   | N/A      | Won't reuse cached values             |
| --indent  | N/A | NO   | N/A      | Set the desired indent level for the decompiled contract             |

### Postprocessing Values

After decompiling a contract, you might find that you see some weird, non-solidity values within ``decompiled.sol``. These values are values that weren't postprocessed correctly, and will be fixed in the future.

- ``MASK{value & value}`` : A masking, usually a conversion from one type to another.
- ``LOAD{value}`` : Loading a variable from storage

### Known Issues and TODOs

Known issues are present in the issues tab on this repository. They will be marked with a decompiler tag and have other descriptors added.

### Notice

This module is very experimental, and is still being improved and developed. If you find something weird, open an issue. I also haven't had a chance to add comments, so don't flame me for that.