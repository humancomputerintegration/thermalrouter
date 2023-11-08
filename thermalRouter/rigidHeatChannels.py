import adsk.core, adsk.fusion, adsk.cam, traceback
import json
import time
import math
import xml.dom.minidom as myXml
import random
from . import config, simUtils

handlers = config.handlers


progressDialog = None

bodiesToSplit = None
heatSourceFaceTokens = []
heatSourceFaces = None
heatSourceType = ""
heatSourceTemperature = 0
ambientTemperature = 300
heatSourcePower = 0
NylonMaterialLib = ""
NylonMaterialName = ""
compLength = 0
bodyName = ""
iterationamounts = 3
costCoeff = 1
doPreview = False
strategyResult = []

simOuterBodiesCollection = None

bodies = []

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
            global simOuterBodiesCollection, bodies, bodiesToSplit, heatSourceFaces
            # Get the inputs entered in the dialog.
            inputs = args.command.commandInputs

            iterationNum = inputs.itemById('pickingUpConfiguration').selectedItem.index + 1
            # print(iterationNum)
            splitBodyByHeat(bodiesToSplit, iterationNum, costCoeff)
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
                splitBodyByHeat(bodiesToSplit, i+1, costCoeff)

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


# Event handler class.
class setSimulationInfoHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface  
            global bodiesToSplit, iterationamounts, heatSourceFaceTokens, costCoeff, heatSourceFaces
            global heatSourceType, heatSourceTemperature, heatSourcePower, ambientTemperature
            global NylonMaterialLib, NylonMaterialName
            # Get the inputs entered in the dialog.
            inputs = args.command.commandInputs
            
            # get inputs
            bodiesToSplit = adsk.core.ObjectCollection.create()
            for i in range(inputs.itemById('selectBodies').selectionCount):
                bodiesToSplit.add(inputs.itemById('selectBodies').selection(i).entity)
            
            # heatSourceFaces = inputs.itemById('selectHeatFace')
            # heatSourceFaceTokens = []
            # for i in range(heatSourceFaces.selectionCount) :
            #     heatSourceFaceTokens.append(heatSourceFaces.selection(i).entity.entityToken)
            heatSourceFaces = adsk.core.ObjectCollection.create()
            for i in range(inputs.itemById('selectHeatFace').selectionCount):
                heatSourceFaces.add(inputs.itemById('selectHeatFace').selection(i).entity)


            if inputs.itemById('isCustomedMaterial').value == False:
                NylonMaterialLib = None
                NylonMaterialName = None
            else:
                NylonMaterialLib = inputs.itemById('NylonMaterialLibList').selectedItem.name
                NylonMaterialName = inputs.itemById('NylonMaterialList').selectedItem.name
            
            iterationamounts = inputs.itemById('iterationNumber').valueOne
            
            heatSourceType = inputs.itemById('heatSourceType').selectedItem.name
            if heatSourceType == 'Constant Temperature':
                heatSourceTemperature = inputs.itemById('temperaturValue').value
            elif heatSourceType == 'Constant Power':
                heatSourcePower = inputs.itemById('powerValue').value
            else:
                raise

            costName = inputs.itemById('CostOfMaterial').valueOne
            costCoeff = 1
            if costName == 0:
                costCoeff = 0.7
            elif costName == 1:
                costCoeff = 1
            elif costName == 2:
                costCoeff = 1.4
            else:
                raise    
            
            ambientTemperature = inputs.itemById('ambientTemperature').value
            
            cmd = ui.commandDefinitions.itemById('rigidSelectOuterBodies')
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

            cmd = ui.commandDefinitions.itemById('rigidSimulationHandler')
            cmd.execute()
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))   


class RigidChannelsCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global doPreview
            app = adsk.core.Application.get()
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            # onInputChange for slider controller
            if cmdInput.id == "NylonMaterialLibList":
                mLibs = app.materialLibraries
                materialLib = inputs.itemById('NylonMaterialLibList').selectedItem.name
                mLib = mLibs.itemByName(materialLib)
                materialList = inputs.itemById('NylonMaterialList')
                materialList.listItems.clear()
                for i in range(mLib.materials.count):
                    # print(mLib.materials.item(i).name)
                    materialList.listItems.add(mLib.materials.item(i).name, False)

            if cmdInput.id == 'isPreviewMode':
                previewIterationNum = inputs.itemById('previewIterationNum')
                costEstimate = inputs.itemById('CostOutput')
                if cmdInput.value == True:
                    previewIterationNum.isVisible = True
                    costEstimate.isVisible = True
                else:
                    previewIterationNum.isVisible = False
                    costEstimate.isVisible = False

            if cmdInput.id == 'isAdvancedOptions':
                if cmdInput.value == True:
                    inputs.itemById('isCustomedMaterial').isVisible = True
                    inputs.itemById('iterationNumber').isVisible = True
                    inputs.itemById('CostOfMaterial').isVisible = True
                    inputs.itemById('ambientTemperature').isVisible = True
                else:
                    inputs.itemById('isCustomedMaterial').value = False
                    inputs.itemById('isCustomedMaterial').isVisible = False
                    inputs.itemById('NylonMaterialList').isVisible = False
                    inputs.itemById('NylonMaterialLibList').isVisible = False
                    inputs.itemById('NylonMaterialSelection').isVisible = False
                    inputs.itemById('iterationNumber').isVisible = False
                    inputs.itemById('CostOfMaterial').isVisible = False
                    inputs.itemById('ambientTemperature').isVisible = False
                    

            if cmdInput.id == 'isCustomedMaterial':
                if cmdInput.value == True:
                    inputs.itemById('NylonMaterialList').isVisible = True
                    inputs.itemById('NylonMaterialLibList').isVisible = True
                    inputs.itemById('NylonMaterialSelection').isVisible = True
                else :
                    inputs.itemById('NylonMaterialList').isVisible = False
                    inputs.itemById('NylonMaterialLibList').isVisible = False
                    inputs.itemById('NylonMaterialSelection').isVisible = False

            if cmdInput.id == 'heatSourceType':
                if cmdInput.selectedItem.name == 'Constant Temperature':
                    inputs.itemById('temperaturValue').isVisible = True
                    inputs.itemById('powerValue').isVisible = False
                if cmdInput.selectedItem.name == 'Constant Power':
                    inputs.itemById('temperaturValue').isVisible = False
                    inputs.itemById('powerValue').isVisible = True

            if cmdInput.id in ['iterationNumber', 'powerValue', 'temperaturValue', 'ambientTemperature', 'heatSourceType'] :
                doPreview = False
            else:
                doPreview = True
        
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('command changed failed:\n{}'.format(traceback.format_exc()))


# preview function
class RigidChannelsCommandPreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Code to react to the event.
        try:
            global doPreview
            if doPreview == False:
                return
            cmdArgs = adsk.core.CommandEventArgs.cast(args)
            global bodiesToSplit
            # Get the current value of inputs entered in the dialog.
            inputs = cmdArgs.command.commandInputs
            global bodiesToSplit, iterationamounts, heatSourceFaceTokens, heatSourceFaces
            global NylonMaterialLib, NylonMaterialName
            # Get the inputs entered in the dialog.

            # inputs = args.command.commandInputs
            # get inputs
            if inputs.itemById('isPreviewMode').value == True :
                if inputs.itemById('isCustomedMaterial').value == False or inputs.itemById('NylonMaterialLibList').selectedItem != None:
                    if inputs.itemById('isCustomedMaterial').value == False or inputs.itemById('NylonMaterialList').selectedItem != None:
                        if inputs.itemById('previewIterationNum').selectedItem != None:

                            bodiesToSplit = adsk.core.ObjectCollection.create()
                            for i in range(inputs.itemById('selectBodies').selectionCount):
                                bodiesToSplit.add(inputs.itemById('selectBodies').selection(i).entity)

                            # heatSourceFaces = inputs.itemById('selectHeatFace')
                            # heatSourceFaceTokens = []
                            # for i in range(heatSourceFaces.selectionCount) :
                            #     heatSourceFaceTokens.append(heatSourceFaces.selection(i).entity.entityToken)
                            
                            heatSourceFaces = adsk.core.ObjectCollection.create()
                            for i in range(inputs.itemById('selectHeatFace').selectionCount):
                                heatSourceFaces.add(inputs.itemById('selectHeatFace').selection(i).entity)
                            

                            if inputs.itemById('isCustomedMaterial').value == False:
                                NylonMaterialLib = None
                                NylonMaterialName = None
                            else:
                                NylonMaterialLib = inputs.itemById('NylonMaterialLibList').selectedItem.name
                                NylonMaterialName = inputs.itemById('NylonMaterialList').selectedItem.name
                                
                            iterationamounts = inputs.itemById('iterationNumber').valueOne

                            selectedName = inputs.itemById('previewIterationNum').selectedItem.name
                            i = int(selectedName[-1]) # i is iteration number
                            costName = inputs.itemById('CostOfMaterial').valueOne
                            costCoeff = 1
                            if costName == 0:
                                costCoeff = 0.7
                            elif costName == 1:
                                costCoeff = 1
                            elif costName == 2:
                                costCoeff = 1.4
                            else:
                                raise                            
                            cost = splitBodyByHeat(bodiesToSplit, i, costCoeff)
                            if inputs.itemById('isCustomedMaterial').value == False:
                                inputs.itemById('CostOutput').formattedText = '<b>$' + str(round(cost, 1)) + '</b>'
                                inputs.itemById('CostOutput').isVisible = True

            '''
            Set this property indicating that the preview is a good
            result and can be used as the final result when the command.
            is executed.
            cmd = ui.commandDefinitions.itemById('simulationMenu')
            cmd.execute() 
            cmdArgs.isValidResult = True           
            ''' 
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    


class rigidMainCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            
            global activeDoc
            activeDoc = app.activeDocument

            cmd = args.command
            cmd.setDialogInitialSize(550,800)
            onInputChanged = RigidChannelsCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)
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

            selectedBodyInput = inputs.addSelectionInput('selectBodies', 'Select bodies to have rigid-heat-channels','Select bodies to have rigid-heat-channels')
            selectedBodyInput.addSelectionFilter('Bodies')
            selectedBodyInput.setSelectionLimits(1,10)


            previewInput = inputs.addBoolValueInput('isPreviewMode', 'Preview Mode', True)
            previewIterationNum = inputs.addDropDownCommandInput('previewIterationNum', 'Iteration Number to Preview', adsk.core.DropDownStyles.TextListDropDownStyle)
            for i in range(1, 6):
                previewIterationNum.listItems.add('Iteration '+str(i), False)
            previewIterationNum.isVisible = False

            costOutput = inputs.addTextBoxCommandInput('CostOutput', 'Estimated Cost', '', 1, True)
            costOutput.isVisible = False


            
            advancedInput = inputs.addBoolValueInput('isAdvancedOptions', 'Advanced Options', True)

            # decide scale of holes array
            costInput = inputs.addIntegerSliderListCommandInput('CostOfMaterial', 'Expected Cost on Thermal Material', [0, 1, 2])
            costInput.setText('Low ☘', 'High ⚡')
            costInput.valueOne = 1
            costInput.isVisible = False
            
            ambientTempeartureInput = inputs.addValueInput('ambientTemperature', 'Ambient Temperature (℃)', '', adsk.core.ValueInput.createByString('20'))
            ambientTempeartureInput.isVisible = False

            iterationAmount = inputs.addIntegerSliderCommandInput('iterationNumber', 'Iteration Amount', 1, 5)
            iterationAmount.valueOne = 3
            iterationAmount.isVisible = False

            materialInput = inputs.addBoolValueInput('isCustomedMaterial', 'Customize the Materials', True)
            materialInput.isVisible = False

            inputs.addTextBoxCommandInput('NylonMaterialSelection', '', '<u><b>Please select the material for the Nylon part:</b></u>', 1, True).isVisible = False
            mLibs = app.materialLibraries      
            materialLibList = inputs.addDropDownCommandInput('NylonMaterialLibList', 'Material Library', adsk.core.DropDownStyles.TextListDropDownStyle)
            materialLibList.isVisible = False
            for i in range(mLibs.count):
                materialLibList.listItems.add(mLibs.item(i).name, False)

            materialList = inputs.addDropDownCommandInput('NylonMaterialList', 'Material', adsk.core.DropDownStyles.TextListDropDownStyle)
            materialList.isVisible = False
            
	

            # Connect to the execute event.
            onExecute = setSimulationInfoHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            onExecutePreview = RigidChannelsCommandPreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            handlers.append(onExecutePreview)      
    
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    

def calcCost(newMaterialVol):
    ICE9_cost_per_kilo = 132 # USD/kg
    ICE9_density = 1.450 # g/cm^3
    ICE9_cost_per_gram = ICE9_cost_per_kilo/1000 # USD/g
    ICE9_cost_per_cm3 = ICE9_cost_per_gram*ICE9_density # USD/cm^3
    cost = newMaterialVol * ICE9_cost_per_cm3
    return cost

def splitBodyByHeat(bodiestosplit_, iteration, costCoeff):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        des = adsk.fusion.Design.cast(app.activeProduct)
        root = adsk.fusion.Component.cast(des.rootComponent)

        product = app.activeProduct        
        design = app.activeProduct
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sideBodies = adsk.core.ObjectCollection.create()
        combinedBodies = rootComp.features.combineFeatures
        extrudes = rootComp.features.extrudeFeatures

        global compLength, bodyName
        global bodiesToSplit, heatSourceFaceTokens, heatSourceFaces, simOuterBodiesCollection
        global NylonMaterialLib, NylonMaterialName
        
        bodyCollection =  bodiestosplit_

        # body = bodiestosplit_.item(0)
        # bodyName = str(body.name)
        # comp = body.parentComponent.bRepBodies
        # new = body.createComponent()
        # newComp = new.parentComponent.bRepBodies

        bodies = []

        for i in range(0, 1):
            if iteration == 1:
                numSpokes = 3
                spokeLength = 20
                # as a % of side length
                spokeWidth = 1
            elif iteration == 2:
                numSpokes = 4
                spokeLength = 20
                # as a % of side length
                spokeWidth = 0.75
            elif iteration == 3:
                numSpokes = 5
                spokeLength = 20
                # as a % of side length
                spokeWidth = 0.6
            elif iteration == 4:
                numSpokes = 6
                spokeLength = 20
                # as a % of side length
                spokeWidth = 0.5
            elif iteration == 5:
                numSpokes = 8
                spokeLength = 20
                spokeWidth = 0.375

            # Create sketch
            # xyPlane = rootComp.xYConstructionPlane
            # sketch = sketches.add(xyPlane)
            # sketch = sketches.add()


            # heatSourceFace = selectInput.selection(i).entity.faces.item(4)
            
            # selectBody('Heat' + str(1+i))
            # selectInput = ui.activeSelections
            # heatSourceFace = selectInput.item(0).entity.faces.item(4)
            # print(heatSourceFace.tempId)
            
            # heatSourceFace = design.findEntityByToken(heatSourceFaceTokens[0])
            # heatSourceFace = heatSourceFace.pop()

            heatSourceFace = heatSourceFaces.item(0)
            equivalentRadius = math.sqrt((heatSourceFace.area/math.pi))*0.9*costCoeff

            sketch = sketches.addWithoutEdges(heatSourceFace)

            centerPoint = heatSourceFace.centroid
            
            # mat3d:adsk.core.Matrix3D = sketch.transform
            # mat3d.invert()
            # centerPoint.transformBy(mat3d)
            # centerPoint = adsk.core.Point3D.create(centerPoint.x, centerPoint.y, 0)

            # edgeLength = heatSourceFace.edges.item(1).length*spokeWidth
            edgeLength = equivalentRadius * spokeWidth * costCoeff
            if edgeLength < .15:
                edgeLength = .15

            circles = sketch.sketchCurves.sketchCircles
            mat = sketch.transform
            mat.invert()
            centerPoint.transformBy(mat)
            # circle1 = circles.addByCenterRadius(vtx0, vtx2)
            circles.addByCenterRadius(centerPoint, equivalentRadius)
            prof = sketch.profiles.item(0)
            # Define that the extent is a distance extent of 100 cm
            extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            distance = adsk.core.ValueInput.createByReal(15)
            extInput.setDistanceExtent(True, distance)

            # Create the extrusion
            ext = extrudes.add(extInput)
            column = ext.bodies.item(0)
            circularFace = column.faces.item(1)

            axes = rootComp.constructionAxes
            axisInput = axes.createInput()

            # Add by circularFace
            axisInput.setByCircularFace(circularFace)
            axes.add(axisInput)

            sketch2 = sketches.addWithoutEdges(heatSourceFace)
            rects = sketch2.sketchCurves.sketchLines

            # widthOffset = adsk.core.Point3D.create(vtx1.x, vtx1.y - edgeLength, vtx1.z)
            # lengthOffset = adsk.core.Point3D.create(widthOffset.x + spokeLength, widthOffset.y, widthOffset.z)
            # rect1 = rects.addThreePointRectangle(vtx1, widthOffset, lengthOffset)
            point1 = adsk.core.Point3D.create(centerPoint.x + edgeLength/2, centerPoint.y, centerPoint.z)
            point2 = adsk.core.Point3D.create(centerPoint.x - edgeLength/2, centerPoint.y + spokeLength, centerPoint.z)
            rects.addTwoPointRectangle(point1, point2)
            prof = sketch2.profiles.item(0)

            extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extInput.setDistanceExtent(True, distance)
            ext2 = extrudes.add(extInput)
            cube1 = ext2.bodies.item(0)
            sideBodies.add(cube1)

            # Create input entities for circular pattern
            inputEntites = adsk.core.ObjectCollection.create()
            inputEntites.add(cube1)
            
            # Create the input for circular pattern
            circularFeats = rootComp.features.circularPatternFeatures
            circularFeatInput = circularFeats.createInput(inputEntites, axes.item(0))
            
            # Set the quantity of the elements
            circularFeatInput.quantity = adsk.core.ValueInput.createByReal(numSpokes)
            
            # Set the angle of the circular pattern
            circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
            
            # Set symmetry of the circular pattern
            circularFeatInput.isSymmetric = False
            
            # Create the circular pattern
            circularFeat = circularFeats.add(circularFeatInput)
            for c in range(0,circularFeat.bodies.count):
                sideBodies.add(circularFeat.bodies.item(c))

            combineInput = combinedBodies.createInput(column, sideBodies)
            newBody = combinedBodies.add(combineInput)
            bodies.append(newBody.bodies.item(0))

            axes.item(0).deleteMe()
        targetBody = bodies[0]
        extraBodies = adsk.core.ObjectCollection.create()
        if len(bodies) > 1:
            for i in range(1, len(bodies)):
                extraBodies.add(bodies[i])
            combinedBodies = rootComp.features.combineFeatures
            combineInput = combinedBodies.createInput(targetBody, extraBodies)
            comBody = combinedBodies.add(combineInput)
            splitTool = comBody.bodies.item(0)
        else:
            splitTool = targetBody

        splitBodyFeats = rootComp.features.splitBodyFeatures


        # Create SplitBodyFeatureInput
        # print('split tool', splitTool.name)
        # Create split body feature

        newMaterialVol = 0
        mLibs = app.materialLibraries
        if NylonMaterialLib == None:
            mLib = mLibs.itemByName('Thermal Router Material Library')
        else:
            mLib = mLibs.itemByName(NylonMaterialLib)  
        if NylonMaterialName == None:
            material = mLib.materials.itemByName('ICE9 Nylon')
        else:
            material = mLib.materials.itemByName(NylonMaterialName)
        
        for i in range(bodyCollection.count):
            bodyToSplit = bodyCollection.item(i)
            
            outerBodyIndex = -1
            # reassign outter bodies due to body is splitted
            if simOuterBodiesCollection is not None:
                outerBodyIndex = simOuterBodiesCollection.find(bodyToSplit)
            if outerBodyIndex != -1: # means this is an outer body
                simOuterBodiesCollection.removeByIndex(outerBodyIndex)

            bodyToSplit = bodyToSplit.createComponent()
            splitBodyInput = splitBodyFeats.createInput(bodyToSplit, splitTool, True)
            splitBodyFeats.add(splitBodyInput)
            splitedBodies = bodyToSplit.parentComponent.bRepBodies

            #---distinguish the bodies---
            for j in range(splitedBodies.count):
                interferenceBodies = adsk.core.ObjectCollection.create()
                interferenceBodies.add(splitTool)
                interferenceBodies.add(splitedBodies.item(j))
                interferenceInput = design.createInterferenceInput(interferenceBodies)
                interferenceResults = design.analyzeInterference(interferenceInput)
            
                if interferenceResults.count == 1:
                    splitedBodies.item(j).material = material
                    newMaterialVol += splitedBodies.item(j).volume
                if outerBodyIndex != -1: # means this is an outer body
                    simOuterBodiesCollection.add(splitedBodies.item(j))
            #---END---
        
        # print('vol', newMaterialVol)
        removeFeatures = rootComp.features.removeFeatures
        removeFeatures.add(splitTool)
        # splitTool.isLightBulbOn = False
        # print('isTran', splitTool.isTransient)
        # print('deleteme', splitTool.deleteMe())
        # splitBodyName = str(splitTool.name)
        # compLength = newComp.count
        totalCost = calcCost(newMaterialVol)
        return totalCost
        # ui.messageBox("Heat has been distributed throughout the body. Click OK to run simulation.")
    except:
        if ui:
            ui.messageBox('command executed failed:\n{}'.format(traceback.format_exc()))
