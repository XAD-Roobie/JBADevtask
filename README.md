Ran with Python 3.10.8

pip(3) install -r requirements.txt

python3 main.py

Supports command line arguments:

python3 main.py <file> <sort type>

examples:

```
    python3 main.py cru-ts-2-10.1991-2000-cutdown.pre 
    or
    python3 main.py cru-ts-2-10.1991-2000-cutdown.pre date|value|xref|yref|none
    or
    python3 main.py date|value|xref|yref|none
```