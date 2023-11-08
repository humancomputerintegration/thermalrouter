#Author-Borui Li
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback
from . import rigidHeatChannels, softHeatChannels, breathability
from . import config

cmdDefsIdList = []
handlers = config.handlers

class thermalRouterMainCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            inputs = args.command.commandInputs

            selectedMethodName = inputs.itemById('radioMainButtonGroup').selectedItem.name
            
            if selectedMethodName == "Rigid heat channels":
                ui.commandDefinitions.itemById('rigidMain').execute()
            elif selectedMethodName == "Soft heat channels":
                ui.commandDefinitions.itemById('softMain').execute()
            elif selectedMethodName == "Breathability":
                ui.commandDefinitions.itemById('holesMain').execute()
            else:
                raise

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            exit()

class thermalRouterMainCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            # Get the command that was created.
            cmd = adsk.core.Command.cast(args.command)
            
            # set the window size
            cmd.setDialogInitialSize(450,250)
            
            # Get the CommandInputs collection associated with the command.
            inputs = cmd.commandInputs

            # Create radio button group input.
            radioButtonGroup = inputs.addRadioButtonGroupCommandInput('radioMainButtonGroup', 'Thermal Router')
            radioButtonItems = radioButtonGroup.listItems
            radioButtonItems.add("Rigid heat channels", True)
            radioButtonItems.add("Soft heat channels", False)
            radioButtonItems.add("Breathability", False)
            radioButtonItems.isFullWidth = False

            cmd.okButtonText = 'Next'

            mainExecute = thermalRouterMainCommandExecuteHandler()
            cmd.execute.add(mainExecute)
            handlers.append(mainExecute)
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            exit()
def run(context):
    ui = None
    try:

        app = adsk.core.Application.get()
        ui  = app.userInterface

        global cmdDefsIdList
        cmdDefsIdList = ['thermalRouterMainWindow',\
                        'rigidMain', 'softMain', 'holesMain',\
                        'rigidSelectOuterBodies', 'rigidSimulationHandler',\
                        'rigidSaveSimResults', 'rigidPickingUpBestConfiguration',\
                        'softSelectOuterBodies', 'softSimulationHandler',\
                        'softSaveSimResults', 'softPickingUpBestConfiguration',\
                        'holesSelectOuterBodies', 'holesSimulationHandler',\
                        'holesSaveSimResults', 'holesPickingUpBestConfiguration']
        
        # delete all commands in case they're already running
        for existingDefId in cmdDefsIdList:
            existingDef = ui.commandDefinitions.itemById(existingDefId)
            if existingDef:
                existingDef.deleteMe()

        # create command and connect to the command created event.
        mainCmdDef = ui.commandDefinitions.addButtonDefinition('thermalRouterMainWindow', 'Thermal Router - Main Menu', 'Choose one method to make your design thermal sounded.', './Resources')
        mainCommandCreated = thermalRouterMainCommandCreatedHandler()
        mainCmdDef.commandCreated.add(mainCommandCreated)
        handlers.append(mainCommandCreated)
        
        # add main command into addin panel
        addinPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        commandControl = addinPanel.controls.addCommand(mainCmdDef)
        commandControl.isPromoted = True
        commandControl.isPromotedByDefault = True
        
        # ----- rigid ----- 
        CmdDef = ui.commandDefinitions.addButtonDefinition('rigidMain', 'Rigid Heat Channels', 'Create Heat Channels on a Rigid Model.')
        CommandCreated = rigidHeatChannels.rigidMainCommandCreatedHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        cmdDef = ui.commandDefinitions.addButtonDefinition('rigidSelectOuterBodies', 'Select Outer Bodies', 'Select Outer Bodies')
        CommandCreated = rigidHeatChannels.selectOuterBodiesCommandCreatedHandler()
        cmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)    

        CmdDef = ui.commandDefinitions.addButtonDefinition('rigidPickingUpBestConfiguration', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = rigidHeatChannels.pickingUpCommandCreatedHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        cmdDef = ui.commandDefinitions.addButtonDefinition('rigidSimulationHandler', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = rigidHeatChannels.simulationCommandCreatedHandler()
        cmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)    

        CmdDef = ui.commandDefinitions.addButtonDefinition('rigidSaveSimResults', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = rigidHeatChannels.saveSimResultsHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        #---- rigid over ----

        #---- soft ----
        CmdDef = ui.commandDefinitions.addButtonDefinition('softMain', 'Soft Heat Channels', 'Create Heat Channels on a Soft Model.')
        CommandCreated = softHeatChannels.softMainCommandCreatedHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        cmdDef = ui.commandDefinitions.addButtonDefinition('softSelectOuterBodies', 'Select Outer Bodies', 'Select Outer Bodies')
        CommandCreated = softHeatChannels.selectOuterBodiesCommandCreatedHandler()
        cmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)    

        CmdDef = ui.commandDefinitions.addButtonDefinition('softPickingUpBestConfiguration', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = softHeatChannels.pickingUpCommandCreatedHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        cmdDef = ui.commandDefinitions.addButtonDefinition('softSimulationHandler', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = softHeatChannels.simulationCommandCreatedHandler()
        cmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)    

        CmdDef = ui.commandDefinitions.addButtonDefinition('softSaveSimResults', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = softHeatChannels.saveSimResultsHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        #---- soft over ----

        #---- holes ----
        CmdDef = ui.commandDefinitions.addButtonDefinition('holesMain', 'Enhance Breathability', 'Create Holes on Model.')
        CommandCreated = breathability.holesMainCommandCreatedHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        cmdDef = ui.commandDefinitions.addButtonDefinition('holesSelectOuterBodies', 'Select Outer Bodies', 'Select Outer Bodies')
        CommandCreated = breathability.selectOuterBodiesCommandCreatedHandler()
        cmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)    

        CmdDef = ui.commandDefinitions.addButtonDefinition('holesPickingUpBestConfiguration', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = breathability.pickingUpCommandCreatedHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        cmdDef = ui.commandDefinitions.addButtonDefinition('holesSimulationHandler', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = breathability.simulationCommandCreatedHandler()
        cmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)    

        CmdDef = ui.commandDefinitions.addButtonDefinition('holesSaveSimResults', 'Simulation Handler', 'Simulation Handler')
        CommandCreated = breathability.saveSimResultsHandler()
        CmdDef.commandCreated.add(CommandCreated)
        handlers.append(CommandCreated)

        #---- holes over ----

        # _handlers.append(onCommandCreated)

        # Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        global cmdDefsIdList

        app = adsk.core.Application.get()
        ui  = app.userInterface
        # ui.messageBox('Stop addin')

        # delete the command in the panel 
        addinPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        mainCommand = addinPanel.controls.itemById('thermalRouterMainWindow')
        if mainCommand:
            mainCommand.deleteMe()

        # existingDef = ui.commandDefinitions.itemById('thermalRouterMainWindow')
        # if existingDef:
        #     existingDef.deleteMe()

        # delete all commands
        for existingDefId in cmdDefsIdList:
            existingDef = ui.commandDefinitions.itemById(existingDefId)
            if existingDef:
                existingDef.deleteMe()

        # existingDef = ui.commandDefinitions.itemById('3DPrint')
        # if existingDef:
        #     existingDef.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


