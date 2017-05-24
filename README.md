# pandapower Graphical User Interface
A Graphical User Interface for the open source [pandapower](https://github.com/lthurner/pandapower) load flow analysis program.

pandapower combines the data analysis library [pandas](http://pandas.pydata.org>) and the power flow solver [PYPOWER](https:/pypi.python.org/pypi/PYPOWER) to create an easy to use network calculation program aimed at automation of analysis and optimization in power systems.

## Installation
* Download this repo and run as below
* Using git clone `git clone https://github.com/Tooblippe/pandapower_gui.git`

## How to run
It is important for now to run using the `python` interpreter.  The GUI embeds an `IPython` console/interpreter, so if you run using the `IPython shell` or from somewhere were the `IPyton Qt Widget` is already running an error will be produced. See this [Multiple incompatible subclass instances of InProcessInteractiveShell](http://stackoverflow.com/questions/20243754/multiple-incompatible-subclass-instances-of-interactiveshellembed-are-being-crea)

```
python pandapower_gui.py
```

running it with 
```
ipython pandapower_gui.py
```

will generate an error as described above

## What is working
* Load and save Excel case files
* Solve case
* Run a technical losses report
* Inspect case elements
* Inspect results elements
* Basic building of elements using dialog boxes
* Embedded IPython interpreter with current net in variable `net`
* Embedded help system

## Embedded IPython Interpreter
The embedded interpreter makes the system pretty usable. The current `net` variable is exported to the interpreter. 


## Screenshot
![](https://cloud.githubusercontent.com/assets/805313/26354423/c31f1d5e-3fc4-11e7-9363-4c5d798caecd.png)

## Developers needed
* If you have PyQt or PySide experience and whant to get involved please let me know. I want to port to PySide but currently just dont have the time. Pyside will make the licensing a bit easier. 


