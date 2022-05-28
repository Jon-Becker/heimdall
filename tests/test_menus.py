def test_help_menu(virtualenv):
    result = virtualenv.run('heimdall -h', capture=True)

    print('Powerful Ethereum smart contract toolkit for forensics, manipulation, and research.' in result)