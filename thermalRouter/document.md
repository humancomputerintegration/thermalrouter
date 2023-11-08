[TOC]



# TODO

- fix bugs in simulation part

- draw icons for the tool

  - thermalRouter main icon

  - holes

  - rigid body

  - soft body 

    (the last three can use the images in the demo video maybe?)

- keep completing this document



# Document

## File Structure

All the necessary files are listed below, other files in the folder are just .vscode or temporary files.

```js
├── ThermalRouter
|   ├── document.md
|   ├── ThermalRouter.manifest
|   ├── ThermalRouter.py
|   ├── breathability.py
|   ├── rigidHeatChannels.py
|   ├── softHeatChannels.py
|   ├── simUtils.py
|   ├── config.py
|   └── Resources
|       ├── all the icons
|       └── ......
```



## Description of each file in a nutshell

- **ThermalRouter.manifest** 

  ThermalRouter.manifest is a manifest file for Fusion 360, recording the basic information about this add-in, i.e. name, author, version, etc.

- **ThermalRouter.py**

  ThermalRouter.py is the main .py file. Fusion 360 will run this file when we click the icon of this add-in in the panel. This file creates all the handlers used in the add-in, including a main window handler, which allows users to choose one of the three methods in our add-in. Then, it will run the corresponding handler. Finally, The connected function (which is in an other file, e.g. breathability.py) of the handler will be called.

- **breathability.py**

  All the implementation part of breathability method.

- **rigidHeatChannels.py**

  All the implementation part of rigid body method.

- **softHeatChannels.py**

  All the implementation part of soft body method.

- **simUtils.py**

  Simulation tools functions, e.g. `selectBody()`, `setConvection()`, etc. We extract these part from each methods to reduce the codes redundancy among all the codes.

- **config.py**

  To  maintain a global variable `handlers[]` across all the .py files. This is very critical to help fusion 360 work. Without this, the whole program would not work.



## Code Structure

breathability.py / rigidHeatChannels.py / softHeatChannels.py are all in a similar code structure.

Take rigidHeatChannels.py as an example:

0. When users choose rigid heat channels in the main menu, the program will enter rigidHeatChannels.py, and then call `rigidMainCommandCreatedHandler()` as the start function in this method. 
1. In `rigidMainCommandCreatedHandler()`, it defines all the basic input command and shows up a dialogue.
2. There are three handlers connect to `rigidMainCommandCreatedHandler()`, which are `RigidChannelsCommandInputChangedHandler()` and `RigidChannelsCommandPreviewHandler()`, `setSimulationInfoHandler()`. The first two handlers response to the change of the input commands, to provide an interactive UI and preview. The last handler is the execute handler. Once users click OK, this handler will start running, saving all the input commands for later use.
3. In `setSimulationInfoHandler()`, it saves all the input commands Besides, it also creates a new command `selectOuterBodiesCommandCreatedHandler()`,  which lets users to select outer bodies for the use in the simulation part.
4. In `selectOuterBodiesCommandCreatedHandler()`, there is a handler `selectOuterBodiesCommandExecuteHandler()` connect to it. This handler saves the outer bodies and starts the `simulationCommandCreatedHandler()` handler. 