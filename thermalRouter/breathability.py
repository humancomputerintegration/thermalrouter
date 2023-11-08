import adsk.core, adsk.fusion, adsk.cam, traceback
import json
import time
import math
import xml.dom.minidom as myXml
import random
from . import config, simUtils

handlers = config.handlers

progressDialog = None

heatSourceFaceTokens = []
heatSourceFaces = None
heatSourceType = ""
heatSourceTemperature = 0
ambientTemperature = 300
heatSourcePower = 0

planeList = None
iterationamounts = 0
shape = ''
polygonEdge = 3
holesArrayScale = 0.5
doPreview = False
strategyResult = []

holesize = 0.2

simOuterBodiesCollection = None

simulation_result_folder = r'D:\simResults\\'

class saveSimResultsHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self,args):   
        try:
            global app, ui
            app = adsk.core.Application.get()
            ui  = app.userInterface
            # for i in range(iterationamounts):
            #     waitOnResults(i + 1)
            print("Please wait one minute before pressing okay.")
            for i in range(iterationamounts):
                progressDialog.progressValue = int(75 + 10/iterationamounts * i)
                if i == 0:
                    study = '"Simulation Case"'
                else: 
                    # original code is str(i+3), don't know why
                    study = '"Simulation Case_' + str(i+1) + '"'
                # ui.messageBox(study)         
                app.executeTextCommand(u'Asset.Activate ' + study)
                app.executeTextCommand(u'Commands.Start SimSwitchToPostProcessingCommand')
                app.executeTextCommand(r'SimResults.ExportActiveResults '+ r'D:\simResults\results' + str(i))
            # os.system("py " + testing_stl_location)      
            # winningConfig()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def saveSimResults(iteration):
    '''
    iteration starts from 1
    '''
    try:
        global app, ui
        app = adsk.core.Application.get()
        ui  = app.userInterface
        if iteration == 1:
            study = '"Simulation Case"'
        else: 
            # original code is str(i+3), don't know why
            study = '"Simulation Case_' + str(iteration) + '"'
        # ui.messageBox(study)         
        app.executeTextCommand(u'Asset.Activate ' + study)
        app.executeTextCommand(u'Commands.Start SimSwitchToPostProcessingCommand')

        app.executeTextCommand(u'SimResults.ActiveResultType 1') # temperature
        app.executeTextCommand(r'SimResults.ExportActiveResults '+ simulation_result_folder + r'SimResultTemperature' + str(iteration))
        
        app.executeTextCommand(u'SimResults.ActiveResultType 6') # thermal gradient
        app.executeTextCommand(r'SimResults.ExportActiveResults '+ simulation_result_folder + r'SimResultGradient' + str(iteration))
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def winningConfig():
    # proc = subprocess.Popen(["python", best_config_location, str(iterationamounts)],stdout=subprocess.PIPE,shell=True)
    # proc.wait()
    # # print(proc.communicate())
    
    # stdout, stderr = proc.communicate()
    # # print(stdout, stderr)
    # ui.messageBox(str(stdout)[2])
    # bestConfig = int(str(stdout)[2])
    # # original code is str(bestConfig+3), don't know why
    # study = '"Simulation Case_' + str(bestConfig) + '"'       
    # app.executeTextCommand(u'Asset.Activate ' + study)
    
    '''
    since all the simulations are outdated now, 
    I think maybe we shouldn't show (activate) any of them.
    Otherwise, we only get an outdated simulation result with warnings.
    anyway, it's up to you, Alex!
    '''

    global app, ui
    app = adsk.core.Application.get()
    ui  = app.userInterface
    global iterationamounts
    global strategyResult

    simResults = [] # a list, each item is a result of one iteration
    # each result is a tuple, (minTemperature, 10% maxTemperature, 10%minGradient, 10%maxGradient)
    
    sampleNum = 10000
    bestThreshold = 0.1

    for i in range(iterationamounts):
    # this one is about temperature 
        doc = myXml.parse(simulation_result_folder + 'SimResultTemperature'  +str(i+1) + '.vtu')
        root = doc.documentElement 
        dataElements = root.getElementsByTagName('DataArray') 
        tempData = dataElements[0].firstChild.data 
        splitedTempData = tempData.split()
        splitedTempData_float = list(map(float, splitedTempData))
        if (len(splitedTempData_float) > sampleNum):
            sortedTempData = random.sample(splitedTempData_float, sampleNum)
        else:
            sortedTempData = splitedTempData_float
        sortedTempData.sort()
        minT = sortedTempData[int(len(sortedTempData)*bestThreshold)]
        # threshold for max temperature
        maxT = sortedTempData[len(sortedTempData) - int(len(sortedTempData)*bestThreshold)]

        # and this one is about thermal gradient 
        doc = myXml.parse(simulation_result_folder + 'SimResultGradient'  +str(i+1) + '.vtu')
        root = doc.documentElement
        dataElements = root.getElementsByTagName('DataArray') 
        gradData = dataElements[0].firstChild.data 
        splitedGradData = gradData.split()
        splitedGradData_float = list(map(float, splitedGradData))
        if (len(splitedGradData_float) > sampleNum):
            sortedGradData = random.sample(splitedGradData_float, sampleNum)
        else:
            sortedGradData = splitedGradData_float
        sortedGradData.sort()
        minG = sortedTempData[int(len(sortedGradData)*bestThreshold)] # threshold for min gradient
        # threshold for max gradient
        maxG = sortedTempData[len(sortedGradData) - int(len(sortedGradData)*bestThreshold)]

        resultOfThisIteration = (minT, maxT, minG, maxG)
        simResults.append(resultOfThisIteration)

    strategyResult = [] #[minminT, minmaxT, maxminT, maxmaxT, ...G]'s iteration
    for strategyIdx in range(8):
        bestIndex = 0
        bestValue = simResults[bestIndex][strategyIdx]
        if strategyIdx in [0, 1, 4, 5]: # get minimal one
            for idx in range(len(simResults)):
                if (simResults[idx][strategyIdx] < bestValue):
                    bestValue = simResults[idx][strategyIdx]
                    bestIndex = idx
        else: # get maximal one
            for idx in range(len(simResults)):
                if (simResults[idx][strategyIdx] > bestValue):
                    bestValue = simResults[idx][strategyIdx]
                    bestIndex = idx
        strategyResult.append(bestIndex+1) # +1 to match iteration number

    progressDialog.progressValue = int(100)
    progressDialog.hide()
    cmd = ui.commandDefinitions.itemById('pickingUpBestConfiguration')
    cmd.execute()
    # ui.messageBox('The best is', strategyResult)


class pickingUpCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self,args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            cmd = args.command
            cmd.setDialogInitialSize(550,800)
            inputs = cmd.commandInputs
            global strategyResult, iterationamounts
            
            textBoxInput = inputs.addTextBoxCommandInput('pickingUpText', '', '', 4, True)
            textBoxInput.formattedText = '<br><div align="center"><font size="4" color="red"><b>Select one which best suits your needs.</b></font></div>.'
            
            if len(strategyResult) != 0:
                textBoxInput = inputs.addTextBoxCommandInput('simReslutsMinMinT', '', '', 2, True)
                text = '\t Minimal Lowest Temperature:\t Iteration ' + str(strategyResult[0])
                textBoxInput.text = text

                textBoxInput = inputs.addTextBoxCommandInput('simReslutsMinMaxT', '', '', 2, True)
                text = '\t Minimal Highest Temperature:\t Iteration ' + str(strategyResult[1])
                textBoxInput.text = text

                textBoxInput = inputs.addTextBoxCommandInput('simReslutsMaxMinT', '', '', 2, True)
                text = '\t Maximal Lowest Temperature:\t Iteration ' + str(strategyResult[2])
                textBoxInput.text = text

                textBoxInput = inputs.addTextBoxCommandInput('simReslutsMaxMaxT', '', '', 2, True)
                text = '\t Maximal Highest Temperature:\t Iteration ' + str(strategyResult[3])
                textBoxInput.text = text

                textBoxInput = inputs.addTextBoxCommandInput('simReslutsMinMinG', '', '', 2, True)
                text = '\t Minimal Lowest Gradient:\t Iteration ' + str(strategyResult[4])
                textBoxInput.text = text

                textBoxInput = inputs.addTextBoxCommandInput('simReslutsMinMaxG', '', '', 2, True)
                text = '\t Minimal Highest Gradient:\t Iteration ' + str(strategyResult[5])
                textBoxInput.text = text
            
                textBoxInput = inputs.addTextBoxCommandInput('simReslutsMaxMinG', '', '', 2, True)
                text = '\t Maximal Lowest Gradient:\t Iteration ' + str(strategyResult[6])
                textBoxInput.text = text
            
                textBoxInput = inputs.addTextBoxCommandInput('simReslutsMaxMaxG', '', '', 2, True)
                text = '\t Maximal Highest Gradient:\t Iteration ' + str(strategyResult[7])
                textBoxInput.text = text

            choicesInput = inputs.addRadioButtonGroupCommandInput('pickingUpConfiguration', 'Please select one iteration')
            # choicesInput.isFullWidth = True	
            for i in range(1, iterationamounts+1): #start from 1 to iterationAmount
                itemName = 'Iteration ' + str(i)
                choicesInput.listItems.add(itemName, False)
            
            onExecute = pickingUpCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            onExecute = pickingUpCommandValidateInputsHandler()
            cmd.validateInputs.add(onExecute)
            handlers.append(onExecute)
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            exit()

# Event handler for the validateInputs event.
class pickingUpCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
            inputs = eventArgs.firingEvent.sender.commandInputs

            # Check to see if the user has selected an iteration
            if inputs.itemById('pickingUpConfiguration').selectedItem.index == -1:
                eventArgs.areInputsValid = False
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            exit()

class pickingUpCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self,args):
        try: 
            app = adsk.core.Application.get()
            global iterationamounts, costCoeff
            global simOuterBodiesCollection, bodies, bodiesToSplit, heatSourceFaces, holesize
            # Get the inputs entered in the dialog.
            inputs = args.command.commandInputs

            iterationNum = inputs.itemById('pickingUpConfiguration').selectedItem.index + 1
            # print(iterationNum)
            drawGeometry(planeList, holesize + (iterationNum / 12), shape, polygonEdge, holesArrayScale)
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            exit()

class simulationCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self,args):
        try:
            global app, ui
            # global progressDialog
            global iterationamounts, costCoeff
            global simOuterBodiesCollection, bodies, bodiesToSplit, heatSourceFaces
            global heatSourceType, heatSourceTemperature, heatSourcePower, ambientTemperature
            global planeList, holesize, shape, polygonEdge, holesArrayScale
            app = adsk.core.Application.get()
            design = app.activeProduct
            ui = app.userInterface
            cmd = args.command
            rootComp = design.rootComponent

            progressDialog = ui.createProgressDialog()
            progressDialog.isBackgroundTranslucent = False
            progressDialog.isCancelButtonShown = False
            # progressDialog.show('Simulation', ' %p %', 0, 100)
            # progressDialog.hide()
            progressDialog.message = "Your simulation is in progress! Processing %p %"

            # let user choose all the heat sources and bodies
            '''
            inputs = cmd.commandInputs
            simSelectedHeatBodyInput = inputs.addSelectionInput('simSelectHeatBodies', 'Select heat sources ','Select heat sources' )
            simSelectedHeatBodyInput.addSelectionFilter('Bodies')
            simSelectedHeatBodyInput.setSelectionLimits(1,10)


            '''

            # onExecute = simulationCommandExecuteHandler()
            # cmd.execute.add(onExecute)
            # handlers.append(onExecute) # keep the handler referenced beyond this function

            # ui.messageBox("Your simulation is in progress! The screen will momentarily freeze - do not fret.")
            # print(simOuterBodies)
            # print(simHeatBodies)
            # print(bodies)
            
            # get Document Path
            path = app.executeTextCommand(u'Document.path')

            if path == 'Untitled':
                ui.messageBox('Please save once!')
                return

            # Create Simulation Asset
            app.executeTextCommand(u'AssetMgt.Create {} SimModelAssetType'.format(path))

            # add iteration loop here 
            # raise
            timeline = design.timeline
            origDesignModelMarker = timeline.markerPosition

            # removeFeatures = rootComp.features.removeFeatures
            # selectBody('hair-dryer')
            # selections = ui.activeSelections
            # removeFeatures.add(selections.item(0).entity)

            timeline = design.timeline
            origSimModelMarker = timeline.markerPosition
            
            progressDialog.progressValue = int(0)
            adsk.doEvents()
            for i in range(iterationamounts):
                # print(int(100/iterationamounts * i))
                progressDialog.progressValue = int(100/iterationamounts * i)
                adsk.doEvents()
                drawGeometry(planeList, holesize + (i / 12), shape, polygonEdge, holesArrayScale)

                adsk.doEvents()
                progressDialog.progressValue = int(100/iterationamounts * (i+0.2))
                # raise
                # ui.messageBox("You will be prompted to save a file. Please name it: configuration" + str(i) + ". Thanks!")
                # exportSTL()

                # activate Simulation WorkSpace
                simWs = ui.workspaces.itemById('SimulationEnvironment')
                simWs.activate()

                # Create Thermal Steady
                app.executeTextCommand(u'SimCommonUI.CreateStudy SimCaseThermalSteady')
                
                # set Heat source
                simUtils.setHeatSource(heatSourceFaces, heatSourceType, heatSourceTemperature, heatSourcePower)

                # set all bodies radiation
                # allBodiesInDesign = adsk.core.ObjectCollection.create()
                # allComps = design.allComponents
                # for comp in allComps:
                #     for body in comp.bRepBodies:
                #         allBodiesInDesign.add(body)
                # for body in allBodiesInDesign:
                #     print(body.name)

                simUtils.setRadiation(ambientTemperature) # set all faces with radiation

                # set outer bodies convection
                simUtils.setConvection(simOuterBodiesCollection)
                
                
                progressDialog.progressValue = int(100/iterationamounts * (i+0.4))
                # raise
                simUtils.saveModel()
                simUtils.runSimulation()

                # for justLoops in range(1000000):
                #     adsk.doEvents()
                # ui.messageBox("untill left corner is done")
                simUtils.waitOnResults(i+1)

                # cmd = ui.commandDefinitions.itemById('saveSimResults')
                # cmd.execute()
                saveSimResults(i+1)

                sim =ui.workspaces.itemById('FusionSolidEnvironment') 
                sim.activate()
                # for i in range(15):
                #     timeline.moveToPreviousStep()
                # if i != iterationamounts - 1:
                timeline.markerPosition =  origSimModelMarker             
                simUtils.saveModel()
                app.activeViewport.refresh()
                
                # timeline.markerPosition =  origModelMarker 
            timeline.markerPosition = origDesignModelMarker
            winningConfig()
            
            
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            exit()



class setSimulationInfoHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface  
            global iterationamounts, heatSourceFaceTokens, heatSourceFaces
            global heatSourceType, heatSourceTemperature, heatSourcePower, ambientTemperature
            global planeList, holesize, shape, polygonEdge, holesArrayScale

            # Get the inputs entered in the dialog.
            inputs = args.command.commandInputs
            
            # get inputs
            # bodiesToSplit = adsk.core.ObjectCollection.create()
            # for i in range(inputs.itemById('selectHeatFace').selectionCount):
            #     bodiesToSplit.add(inputs.itemById('selectHeatFace').selection(i).entity)
            
            # heatSourceFaces = inputs.itemById('selectHeatFace')
            # heatSourceFaceTokens = []
            # for i in range(heatSourceFaces.selectionCount) :
            #     heatSourceFaceTokens.append(heatSourceFaces.selection(i).entity.entityToken)
            heatSourceFaces = adsk.core.ObjectCollection.create()
            for i in range(inputs.itemById('selectHeatFace').selectionCount):
                heatSourceFaces.add(inputs.itemById('selectHeatFace').selection(i).entity)

            
            iterationamounts = inputs.itemById('iterationNumber').valueOne
            
            heatSourceType = inputs.itemById('heatSourceType').selectedItem.name
            if heatSourceType == 'Constant Temperature':
                heatSourceTemperature = inputs.itemById('temperaturValue').value
            elif heatSourceType == 'Constant Power':
                heatSourcePower = inputs.itemById('powerValue').value
            else:
                raise
            
            ambientTemperature = inputs.itemById('ambientTemperature').value

            result = getInput(inputs)
            planeList, iterationamounts, shape, polygonEdge, holesArrayScale = result 
            
            cmd = ui.commandDefinitions.itemById('holesSelectOuterBodies')
            cmd.execute()   
          
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class selectOuterBodiesCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface  
            # Get the inputs entered in the dialog.
            cmd = args.command
            inputs = args.command.commandInputs

            simSelectedOuterBodyInput = inputs.addSelectionInput('simSelectOuterBodies', 'Select Outer Bodies ','Select all the outer bodies which exposed to the air' )
            simSelectedOuterBodyInput.addSelectionFilter('Bodies')
            simSelectedOuterBodyInput.setSelectionLimits(1)

            onExecute = selectOuterBodiesCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))   

class selectOuterBodiesCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface  
            # Get the inputs entered in the dialog.
            cmd = args.command
            inputs = args.command.commandInputs
            global simOuterBodiesCollection
            
            simOuterBodiesCollection = adsk.core.ObjectCollection.create()
            
            for i in range(inputs.itemById('simSelectOuterBodies').selectionCount):
                simOuterBodiesCollection.add(inputs.itemById('simSelectOuterBodies').selection(i).entity)

            

            cmd = ui.commandDefinitions.itemById('holesSimulationHandler')
            cmd.execute()
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class HolesCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global doPreview
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            # Check to see if it's the plane input.
            if args.input.id == 'planeSelect':
                # Enable/disable the point input field depending on if the plane input has been specified.
                planeInput = args.input
                #pointInput = args.firingEvent.sender.commandInputs.itemById('pointSelect')
                #if planeInput.selectionCount == 1:
                    #pointInput.isEnabled = True
                #else:
                    #pointInput.clearSelection()
                    #pointInput.isEnabled = False
            if cmdInput.id == 'shapeList':
                polygonEdge = inputs.itemById('polygonEdge')
                if cmdInput.selectedItem.name == 'Polygon':
                    polygonEdge.isVisible = True
                else:
                    polygonEdge.isVisible = False
            
            if cmdInput.id == 'isPreviewMode':
                previewIterationNum = inputs.itemById('previewIterationNum')
                if cmdInput.value == True:
                    previewIterationNum.isVisible = True
                else:
                    previewIterationNum.isVisible = False

            if cmdInput.id == 'isAdvancedOptions':
                if cmdInput.value == True:
                    inputs.itemById('shapeList').isVisible = True
                    inputs.itemById('iterationNumber').isVisible = True
                    inputs.itemById('ScaleOfHolesArray').isVisible = True
                    inputs.itemById('ambientTemperature').isVisible = True
                else:
                    inputs.itemById('shapeList').isVisible = False
                    inputs.itemById('iterationNumber').isVisible = False
                    inputs.itemById('ScaleOfHolesArray').isVisible = False
                    inputs.itemById('ambientTemperature').isVisible = False
                    inputs.itemById('polygonEdge').isVisible = False
            
            if cmdInput.id == 'heatSourceType':
                if cmdInput.selectedItem.name == 'Constant Temperature':
                    inputs.itemById('temperaturValue').isVisible = True
                    inputs.itemById('powerValue').isVisible = False
                if cmdInput.selectedItem.name == 'Constant Power':
                    inputs.itemById('temperaturValue').isVisible = False
                    inputs.itemById('powerValue').isVisible = True

            if cmdInput.id in ['iterationNumber', 'powerValue', 'temperaturValue', 'ambientTemperature', 'heatSourceType']:
                doPreview = False
            else:
                doPreview = True
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class HolesCommandPreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Code to react to the event.
        try:
            global doPreview
            global holesize
            if doPreview == False:
                return
            cmdArgs = adsk.core.CommandEventArgs.cast(args)

            # Get the current value of inputs entered in the dialog.
            inputs = cmdArgs.command.commandInputs
            
            if inputs.itemById('isPreviewMode').value == True :
                if inputs.itemById('previewIterationNum').selectedItem != None:
                    result = getInput(inputs) # result = (planeEnt, size, iterationamount, shape, polygonEdge, scale)
                    # Draw the preview geometry.
                    selectedName = inputs.itemById('previewIterationNum').selectedItem.name
                    i = int(selectedName[-1]) # i is iteration number
                    drawGeometry(result[0], holesize + (i / 12), result[2], result[3], result[4])

            '''
            Set this property indicating that the preview is a good
            result and can be used as the final result when the command
            is executed.
            cmd = ui.commandDefinitions.itemById('simulationMenu')
            cmd.execute() 
            cmdArgs.isValidResult = True           
            ''' 
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class holesMainCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            
            global activeDoc
            activeDoc = app.activeDocument
    
            # Define the command dialog.
            cmd = adsk.core.Command.cast(args.command)
            # cmd.setDialogMinimumSize(450, 200)
            cmd.setDialogInitialSize(500,800)
            inputs = cmd.commandInputs
            
            selectedHeatSourcesInput = inputs.addSelectionInput('selectHeatFace', 'Select heat sources','Select heat sources')
            selectedHeatSourcesInput.addSelectionFilter('PlanarFaces')
            selectedHeatSourcesInput.addSelectionFilter('ConstructionPlanes')
            selectedHeatSourcesInput.setSelectionLimits(1,1)

            heatSourceType = inputs.addDropDownCommandInput('heatSourceType', 'Heat source type', adsk.core.DropDownStyles.TextListDropDownStyle)
            heatSourceType.listItems.add('Constant Temperature', True)
            heatSourceType.listItems.add('Constant Power', False)

            temperaturValue = inputs.addValueInput('temperaturValue', 'Temperature (℃)', '', adsk.core.ValueInput.createByString('0'))
            powerValue = inputs.addValueInput('powerValue', 'Power (W)', '', adsk.core.ValueInput.createByString('0'))
            powerValue.isVisible = False

            # Create the selector for the plane.
            planeInput = inputs.addSelectionInput('planeSelect', 'Select Faces to be modified', 'Select Faces')
            planeInput.addSelectionFilter('PlanarFaces')
            planeInput.addSelectionFilter('ConstructionPlanes')
            planeInput.setSelectionLimits(1)

            previewInput = inputs.addBoolValueInput('isPreviewMode', 'Preview Mode', True)
            previewIterationNum = inputs.addDropDownCommandInput('previewIterationNum', 'Iteration Number to Preview', adsk.core.DropDownStyles.TextListDropDownStyle)
            for i in range(1, 6):
                previewIterationNum.listItems.add('Iteration '+str(i), False)
            previewIterationNum.isVisible = False
            
            advancedInput = inputs.addBoolValueInput('isAdvancedOptions', 'Advanced Options', True)

            # Create the list for types of shapes.
            shapeList = inputs.addDropDownCommandInput('shapeList', 'Shape Type', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            shapeList.listItems.add('Circle', True, 'Resources/Circle', -1)
            shapeList.listItems.add('Square', False, 'Resources/Square', -1)
            # resources of star should be generate in future
            shapeList.listItems.add('Star', False, 'Resources/Star', -1) 
            shapeList.listItems.add('Polygon', False, 'Resources/Pentagon', -1)
            shapeList.isVisible = False

            
            polygonEdge = inputs.addDropDownCommandInput('polygonEdge', 'Edges of the Polygon', adsk.core.DropDownStyles.TextListDropDownStyle)
            polygonEdge.listItems.add(str(3), True)
            for i in range(4, 9):
                polygonEdge.listItems.add(str(i), False)
            polygonEdge.isVisible = False

            '''
            des = adsk.fusion.Design.cast(app.activeProduct)
            um = des.unitsManager
            oneUnit = um.convert(1, des.unitsManager.defaultLengthUnits, 'cm')
            sizeSlider = cmdInputs.addFloatSliderCommandInput('sizeSlider', 'Size', des.unitsManager.defaultLengthUnits, oneUnit, oneUnit * 30, False)
            sizeSlider.valueOne = oneUnit
            sizeSlider.spinStep = oneUnit/2
            '''
            
            # decide scale of holes array
            scaleInput = inputs.addButtonRowCommandInput('ScaleOfHolesArray', 'Scale of Holes Array', False)
            scaleInput.listItems.add('Small', False, "Resources/Scale/Small")
            scaleInput.listItems.add('Medium', True, "Resources/Scale/Medium")
            scaleInput.listItems.add('Large', False, "Resources/Scale/Large")
            scaleInput.isVisible = False

            ambientTempeartureInput = inputs.addValueInput('ambientTemperature', 'Ambient Temperature (℃)', '', adsk.core.ValueInput.createByString('20'))
            ambientTempeartureInput.isVisible = False
            # iterationInput = cmdInputs.addValueInput('number', 'Iteration Amount', '', adsk.core.ValueInput.createByString('2'))
            
            iterationAmount = inputs.addIntegerSliderCommandInput('iterationNumber', 'Iteration Amount', 1, 5)
            iterationAmount.valueOne = 3
            iterationAmount.isVisible = False

            # Connect to the execute event.
            onExecute = setSimulationInfoHandler()
            #onExecute = CutoutCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)      
    
            # Connect to the execute preview event.
            # onExecutePreview = CutoutCommandExecutePreviewHandler()
            onExecutePreview = HolesCommandPreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            handlers.append(onExecutePreview)
            
            # Connect to the input changed event.
            # onInputChanged = CutoutCommandInputChangedHandler()
            onInputChanged = HolesCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)
            
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    


# Gets the current values from the command dialog.
def getInput(inputs):
    try:
        for input in inputs:        
            if input.id == 'planeSelect':
                planeEnt = adsk.core.ObjectCollection.create()
                for i in range(0, input.selectionCount):
                    planeEnt.add(input.selection(i).entity)
            elif input.id == 'pointSelect':
                pointEnts = adsk.core.ObjectCollection.create()
                for i in range(0, input.selectionCount):
                    pointEnts.add(input.selection(i).entity)
            elif input.id == 'shapeList':
                shape = input.selectedItem.name # circle or polygon?
            elif input.id == 'polygonEdge':
                polygonEdge = int(input.selectedItem.name) # num of polygon's edges
            elif input.id == 'iterationNumber':
                iterationamount = input.valueOne
            elif input.id == 'ScaleOfHolesArray':
                if input.selectedItem.name == 'Small':
                    scale = 0.4
                elif input.selectedItem.name == 'Medium':
                    scale = 0.6
                elif input.selectedItem.name == 'Large':
                    scale = 0.8
                else : raise
                
        return (planeEnt, iterationamount, shape, polygonEdge, scale)
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    

   
# Draws the shapes based on the input argument.
# scale is a value between 0 and 1     
def drawGeometry(planeEnts, size, shape, polygonEdges, scale):
    try:
        # Get the design.
        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)

        print(scale)

        for planeEnt in planeEnts:
            # Create a new sketch plane.
            sk = des.rootComponent.sketches.addWithoutEdges(planeEnt)           

            
            # find the centroid of the 2D shape, we'll center our array about it
            point = planeEnt.centroid
            # clone point
            pnt :adsk.core.Point3D = point.copy()

            surfaceEvaluator_var = planeEnt.evaluator
            
            
            # get sketch matrix3d
            mat3d:adsk.core.Matrix3D = sk.transform
            orig_mat3d:adsk.core.Matrix3D = sk.transform
            mat3d.invert()
            # print(orig_mat3d, mat3d)
            # point transform
            pnt.transformBy(mat3d)

            # pull the centroid coordinates
            centerX = pnt.x
            centerY = pnt.y
            # controls the distance between holes (in cm)
            # spacingX = 0.75 # 0.75
            # spacingY = 0.75 # 1
            spacingX = size * 3
            spacingY = size * 3

            maxPnt = surfaceEvaluator_var.parametricRange().maxPoint
            minPnt = surfaceEvaluator_var.parametricRange().minPoint
            lengthX = abs(maxPnt.x - minPnt.x)
            lengthY = abs(maxPnt.y - minPnt.y)

            nHolesX = int(scale * lengthX / spacingX)
            nHolesY = int(scale * lengthY / spacingY)
            print(nHolesX, nHolesY)
            # controls the number of holes in the arrray
            # nHolesX = 8 #8
            # nHolesY = 6 #6

            pointCnt = 0

            print("new start")
            for i in range(int(-nHolesX/2), int(nHolesX/2)+1, 1):
                for j in range(int(-nHolesY/2), int(nHolesY/2)+1, 1):
                    centerPoint = adsk.core.Point3D.create(centerX + spacingX * i, centerY + spacingY * j, 0)

                    leftUpperPoint = adsk.core.Point3D.create(centerX + spacingX * i - 2*size/3, centerY + spacingY * j + 2*size/3, 0)
                    leftLowerPoint = adsk.core.Point3D.create(centerX + spacingX * i - 2*size/3, centerY + spacingY * j - 2*size/3, 0)
                    rightUpperPoint = adsk.core.Point3D.create(centerX + spacingX * i + 2*size/3, centerY + spacingY * j + 2*size/3, 0)
                    rightLowerPoint = adsk.core.Point3D.create(centerX + spacingX * i + 2*size/3, centerY + spacingY * j - 2*size/3, 0)
                    
                    centerPoint_test = centerPoint.copy()
                    centerPoint_test.transformBy(orig_mat3d)
                    leftUpperPoint.transformBy(orig_mat3d)
                    leftLowerPoint.transformBy(orig_mat3d)
                    rightUpperPoint.transformBy(orig_mat3d)
                    rightLowerPoint.transformBy(orig_mat3d)
                    (isTrue, paramCenterPoint) = surfaceEvaluator_var.getParameterAtPoint(centerPoint_test)
                    (isTrue, leftUpperPoint_test) = surfaceEvaluator_var.getParameterAtPoint(leftUpperPoint)
                    (isTrue, leftLowerPoint_test) = surfaceEvaluator_var.getParameterAtPoint(leftLowerPoint)
                    (isTrue, rightUpperPoint_test) = surfaceEvaluator_var.getParameterAtPoint(rightUpperPoint)
                    (isTrue, rightLowerPoint_test) = surfaceEvaluator_var.getParameterAtPoint(rightLowerPoint)

                    if surfaceEvaluator_var.isParameterOnFace(paramCenterPoint) == False:
                        continue
                    if surfaceEvaluator_var.isParameterOnFace(leftUpperPoint_test) == False:
                        continue
                    if surfaceEvaluator_var.isParameterOnFace(leftLowerPoint_test) == False:
                        continue
                    if surfaceEvaluator_var.isParameterOnFace(rightUpperPoint_test) == False:
                        continue
                    if surfaceEvaluator_var.isParameterOnFace(rightLowerPoint_test) == False:
                        continue
                        
                    pointCnt += 1

                    if shape == 'Circle':
                        circle = sk.sketchCurves.sketchCircles.addByCenterRadius(centerPoint, size/2)
                    elif shape == 'Square':
                        cornerPoint = adsk.core.Point3D.create(centerX + spacingX * i + size/2, centerY + spacingY * j + size/2, 0)
                        square = sk.sketchCurves.sketchLines.addCenterPointRectangle(centerPoint, cornerPoint)
                    elif shape == 'Star':
                        outterPointAngle = [90, 162, 234, 306, 18]
                        innerPointAngle = [126, 198, 270, 342, 54]
                        outterRadius = 2*size/3
                        innerRadius = outterRadius/3
                        outterPointCoordX = [centerX + spacingX*i + outterRadius*math.cos(math.pi*ang/180) for ang in outterPointAngle]
                        outterPointCoordY = [centerY + spacingY*j + outterRadius*math.sin(math.pi*ang/180) for ang in outterPointAngle]
                        innerPointCoordX = [centerX + spacingX*i + innerRadius*math.cos(math.pi*ang/180) for ang in innerPointAngle]
                        innerPointCoordY = [centerY + spacingY*j + innerRadius*math.sin(math.pi*ang/180) for ang in innerPointAngle]
                        outterPoint = []
                        innerPoint = []
                        for k in range(0, 5):
                            outterPoint.append(adsk.core.Point3D.create(outterPointCoordX[k], outterPointCoordY[k]))
                            innerPoint.append(adsk.core.Point3D.create(innerPointCoordX[k], innerPointCoordY[k]))
                        for k in range(0, 5):
                            sk.sketchCurves.sketchLines.addByTwoPoints(innerPoint[k], outterPoint[k])
                            sk.sketchCurves.sketchLines.addByTwoPoints(innerPoint[k], outterPoint[(k+1)%5])
                        
                    elif shape == 'Polygon':
                        radius = size/2
                        new_point_x = new_point_y = 0
                        for k in range(0, polygonEdges):
                            last_point_x, last_point_y = (new_point_x, new_point_y)

                            new_point_x = radius*math.cos(2*math.pi*k/polygonEdges) + centerX + spacingX * i
                            new_point_y = radius*math.sin(2*math.pi*k/polygonEdges) + centerY + spacingY * j

                            if k != 0 :
                                newPoint = adsk.core.Point3D.create(new_point_x, new_point_y)
                                lastPoint = adsk.core.Point3D.create(last_point_x, last_point_y)
                                sk.sketchCurves.sketchLines.addByTwoPoints(newPoint, lastPoint)
                            else:
                                firstPoint = adsk.core.Point3D.create(new_point_x, new_point_y)
                        sk.sketchCurves.sketchLines.addByTwoPoints(newPoint, firstPoint)
                            

            print(pointCnt)
            # Find the inner profiles (only those with one loop).
            profiles = adsk.core.ObjectCollection.create()
            
            if pointCnt == 0:
                continue
            for prof in sk.profiles:
                if prof.profileLoops.count == 1:
                    profiles.add(prof)
            # Create the extrude feature.            
            input = des.rootComponent.features.extrudeFeatures.createInput(profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
            input.setDistanceExtent(True, adsk.core.ValueInput.createByReal(1))
            input.participantBodies = [planeEnt.body]
            extrude = des.rootComponent.features.extrudeFeatures.add(input)
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    
