from heimdall.__main__ import main

def test_help_menu(capsys):
    main(['-h'])
    
    captured = capsys.readouterr()
    
    assert 'Powerful Ethereum smart contract toolkit for forensics, manipulation, and research.' in captured.out