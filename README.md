
# Heimdall


![preview](https://github.com/Jon-Becker/heimdall/blob/main/preview.png?raw=true)

Heimdall is an advanced and modular smart-contract toolkit which aims to make dealing with smart contracts on EVM based chains easier. 

## Usage

Heimdall operates off the ``argparse`` library, with modules specifying which operation you with to perform.

```
Usage: heimdall [-m/--module] MODULE [-t/--target] VALUE [-o path] [-n value]
                                     [-p value] [-p value] [--redeploy]
                                     [--beautify] [--version] [--update]
                                     [-v] [-h] [--redeploy] [--beautify]
```

## Modules & Help

You may find the various modules supported by Heimdall by using the -h option, which opens the help menu by default.

```
Options:
  -h, --help                          Show the help message and exit
  -hh                                 Show advanced help message and exit
  --version                           Display version information and exit
  --update                            Updates heimdall to the latest release
  -v, --verbose                       Toggle verbose output

  Modules:
    Below is a list of modules currently supported on Heimdall

        #  |       Name  |                                           Description    
           |             |                                                      
        0  |  Decompile  |      Decompile and download the target smart contract

  Parameters:
    -m MODULE, --module MODULE        Operation module, either name or number from list
    -t TARGET, --target TARGET        Target of operation (file, transaction id,
                                        or address)
    -o PATH, --output PATH            Path to write output to
    -c ID, --chain ID                 Chain ID of target
    -p URL, --provider URL            URL of custom Ethereum provider

  Additional:
    --redeploy ID                     Redeploys the contract from -n onto ID
    --beautify                        Attempts to beautify the downloaded contract using
                                        statistical renaming and spacing
    --default                         Always use defaults when prompted for input
    --flush, --ignore-cache           Flushes the cache and rewrites it
```

Please keep in mind as more modules are released, module numbers may change. It's recommended to use the module name instead.

### Module Documentation

Specific module documentation can be found in the ``/docs`` folder, or quickly navigate using the links beow.

| Module Name | Description | Documentation URL |
| ----------- | ----------- | ----------------- |
| Decompile   | Decompiles EVM bytecode > Solidity | [Documentation](https://github.com/Jon-Becker/heimdall/blob/main/docs/decompile.md)

## Configuration

You may save 

## Contributing

If you'd like to contribute to Heimdall or add a module, please open a pull-request with your changes, as well as detailed information on what is changed, added, or improved.

### Modules

To add a module, you must add a ``.py`` file within the ``/lib/modules`` folder. In order for your pull-request to be accepted, your module must begin with a ``meta`` object, which is used when displaying what it does to end-users.

Example meta object:
```
meta = {
  "title": "Decompile",
  "description": "Decompile and download the target smart contract",
  "author": "Jonathan Becker <jonathan@jbecker.dev>",
  "version": "v1.0.0",
}
```

You will also need to add detailed documentation to this readme file in the ``Module Documentation`` section.

#### Troubleshooting

If you encounter an issue, please create one using the link below. You MUST follow the issue format, or it will be marked as invalid.

Issues that remain inactive for 72 hours will be marked inactive and closed. If your issue is accepted by a contributor, they will assign themselves to it and add corresponding tags.

## Credits
This project is coded in its entirety by [Jonathan Becker](https://jbecker.dev). Various contributors can be found in the sidebar.

