# ThermalRouter: Enabling Users to Design Thermally-Sound Devices

This is the repository for our CAD plugin, ThermalRouter, presented in our UIST 2023 paper "ThermalRouter: Enabling Users to Design Thermally-Sound Devices." This tool was built at the University of Chicago's Human Computer Integration Lab.

[Paper](https://lab.plopes.org/published/2023-UIST-ThermalRouter.pdf) | [Video](https://www.youtube.com/watch?v=PbasORkPn5w&feature=youtu.be)

## Installating ThermalRouter

To install this plugin, you must have Autodesk Fusion360 installed with add-ins enabled along with Python3. Navigate to Fusion's add-in folder (e.g., C:\Users\...\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns) and drag and drop our "thermalrouter" folder. When you launch Fusion360, navigate to "Utilities --> Add-ins --> My Add-ins" and run "thermalrouter" to launch the tool.

To add the materials used in our paper to your material library (e.g., ICE9 Nylon), please add our library "Thermal Router Material Library.adsklib" by navigating to "Modify --> Manage Materials" to bring up the Material Browser. Now, you can open the library as an existing library. Note: sometimes this must be repeated on startup of Fusion360.

## Contact and reporting bugs

This tool was developed as a research prototype -- as such, there are scenarios in which bugs arise. Please reach out to Alex [alexmazursky@uchicago.edu](alexmazursky@uchicago.edu) and he'll do his best to help!

## Citing

When using or building upon this work in an academic publication, please consider citing as follows:

Alex Mazursky, Borui Li, Shan-Yuan Teng, Daria Shifrina, Joyce E Passananti, Svitlana Midianko, and Pedro Lopes. 2023. ThermalRouter: Enabling Users to Design Thermally-Sound Devices. In Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST '23). Association for Computing Machinery, New York, NY, USA, Article 58, 1–14. https://doi.org/10.1145/3586183.3606747

### File Structure

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

### Description of each file in a nutshell

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

### Code Structure

breathability.py / rigidHeatChannels.py / softHeatChannels.py are all in a similar code structure.

Take rigidHeatChannels.py as an example:

0. When users choose rigid heat channels in the main menu, the program will enter rigidHeatChannels.py, and then call `rigidMainCommandCreatedHandler()` as the start function in this method. 
1. In `rigidMainCommandCreatedHandler()`, it defines all the basic input command and shows up a dialogue.
2. There are three handlers connect to `rigidMainCommandCreatedHandler()`, which are `RigidChannelsCommandInputChangedHandler()` and `RigidChannelsCommandPreviewHandler()`, `setSimulationInfoHandler()`. The first two handlers response to the change of the input commands, to provide an interactive UI and preview. The last handler is the execute handler. Once users click OK, this handler will start running, saving all the input commands for later use.
3. In `setSimulationInfoHandler()`, it saves all the input commands Besides, it also creates a new command `selectOuterBodiesCommandCreatedHandler()`,  which lets users to select outer bodies for the use in the simulation part.
4. In `selectOuterBodiesCommandCreatedHandler()`, there is a handler `selectOuterBodiesCommandExecuteHandler()` connect to it. This handler saves the outer bodies and starts the `simulationCommandCreatedHandler()` handler. 
