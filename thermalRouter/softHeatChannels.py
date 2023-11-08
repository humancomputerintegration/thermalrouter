import adsk.core, adsk.fusion, traceback
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
siliconeMaterialLib = ""
siliconeMaterialName = ""
thubberMaterialLib = ''
thubberMaterialName = ''
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


class setSimulationInfoHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface  
            global facesToCoolDown, iterationamounts, heatSourceFaceTokens, costCoeff
            global heatSourceType, heatSourceTemperature, heatSourcePower, ambientTemperature
            global siliconeMaterialLib, siliconeMaterialName, thubberMaterialLib, thubberMaterialName
            # Get the inputs entered in the dialog.
            inputs = args.command.commandInputs
            
            # get inputs
            # facesToCoolDown = inputs.itemById('selectFaces').selection(0).entity
            facesToCoolDown = adsk.core.ObjectCollection.create()
            for i in range(inputs.itemById('selectFaces').selectionCount):
                facesToCoolDown.add(inputs.itemById('selectFaces').selection(i).entity)
            
            if inputs.itemById('isCustomedMaterial').value == False:
                siliconeMaterialLib = None
                siliconeMaterialName = None
                thubberMaterialLib = None
                thubberMaterialName = None
            else:
                siliconeMaterialLib = inputs.itemById('SiliconeMaterialLibList').selectedItem.name
                siliconeMaterialName = inputs.itemById('SiliconeMaterialList').selectedItem.name
                thubberMaterialLib = inputs.itemById('ThubberMaterialLibList').selectedItem.name
                thubberMaterialName = inputs.itemById('ThubberMaterialList').selectedItem.name
            iterationamounts = inputs.itemById('iterationNumber').valueOne
            
            heatSourceFaces = inputs.itemById('selectHeatFace')
            heatSourceFaceTokens = []
            for i in range(heatSourceFaces.selectionCount) :
                heatSourceFaceTokens.append(heatSourceFaces.selection(i).entity.entityToken)
            
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

            cmd = ui.commandDefinitions.itemById('softSelectOuterBodies')
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

            cmd = ui.commandDefinitions.itemById('softSimulationHandler')
            cmd.execute()
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))  

class SoftChannelsCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
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
            if cmdInput.id == "SiliconeMaterialLibList":
                mLibs = app.materialLibraries
                materialLib = inputs.itemById('SiliconeMaterialLibList').selectedItem.name
                mLib = mLibs.itemByName(materialLib)
                materialList = inputs.itemById('SiliconeMaterialList')
                materialList.listItems.clear()
                for i in range(mLib.materials.count):
                    # print(mLib.materials.item(i).name)
                    materialList.listItems.add(mLib.materials.item(i).name, False)

            if cmdInput.id == "ThubberMaterialLibList":
                mLibs = app.materialLibraries
                materialLib = inputs.itemById('ThubberMaterialLibList').selectedItem.name
                mLib = mLibs.itemByName(materialLib)
                materialList = inputs.itemById('ThubberMaterialList')
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
                    inputs.itemById('SiliconeMaterialList').isVisible = False
                    inputs.itemById('SiliconeMaterialLibList').isVisible = False
                    inputs.itemById('SiliconeMaterialSelection').isVisible = False
                    inputs.itemById('ThubberMaterialList').isVisible = False
                    inputs.itemById('ThubberMaterialLibList').isVisible = False
                    inputs.itemById('ThubberMaterialSelection').isVisible = False
                    inputs.itemById('iterationNumber').isVisible = False
                    inputs.itemById('CostOfMaterial').isVisible = False
                    inputs.itemById('ambientTemperature').isVisible = False


                
            if cmdInput.id == 'isCustomedMaterial':
                if cmdInput.value == True:
                    inputs.itemById('SiliconeMaterialList').isVisible = True
                    inputs.itemById('SiliconeMaterialLibList').isVisible = True
                    inputs.itemById('SiliconeMaterialSelection').isVisible = True
                    inputs.itemById('ThubberMaterialList').isVisible = True
                    inputs.itemById('ThubberMaterialLibList').isVisible = True
                    inputs.itemById('ThubberMaterialSelection').isVisible = True
                else :
                    inputs.itemById('SiliconeMaterialList').isVisible = False
                    inputs.itemById('SiliconeMaterialLibList').isVisible = False
                    inputs.itemById('SiliconeMaterialSelection').isVisible = False
                    inputs.itemById('ThubberMaterialList').isVisible = False
                    inputs.itemById('ThubberMaterialLibList').isVisible = False
                    inputs.itemById('ThubberMaterialSelection').isVisible = False

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


class SoftChannelsCommandPreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Code to react to the event.
        try:
            global doPreview
            if doPreview == False:
                return
            cmdArgs = adsk.core.CommandEventArgs.cast(args)
            # Get the current value of inputs entered in the dialog.
            inputs = cmdArgs.command.commandInputs
            global facesToCoolDown, iterationamounts, heatSourceFaceTokens
            global siliconeMaterialLib, siliconeMaterialName, thubberMaterialLib, thubberMaterialName
            # Get the inputs entered in the dialog.

            # inputs = args.command.commandInputs
            # get inputs
            if inputs.itemById('isPreviewMode').value == True :
                if inputs.itemById('isCustomedMaterial').value == False or (inputs.itemById('SiliconeMaterialLibList').selectedItem != None and inputs.itemById('ThubberMaterialLibList').selectedItem != None):
                    if inputs.itemById('isCustomedMaterial').value == False or (inputs.itemById('SiliconeMaterialList').selectedItem != None and inputs.itemById('ThubberMaterialList').selectedItem != None):
                        if inputs.itemById('previewIterationNum').selectedItem != None:

                            # facesToCoolDown = inputs.itemById('selectFaces').selection(0).entity
                            facesToCoolDown = adsk.core.ObjectCollection.create()
                            for i in range(inputs.itemById('selectFaces').selectionCount):
                                facesToCoolDown.add(inputs.itemById('selectFaces').selection(i).entity)
                            heatSourceFaces = inputs.itemById('selectHeatFace')
                            if inputs.itemById('isCustomedMaterial').value == False:
                                siliconeMaterialLib = None
                                siliconeMaterialName = None
                                thubberMaterialLib = None
                                thubberMaterialName = None
                            else:
                                siliconeMaterialLib = inputs.itemById('SiliconeMaterialLibList').selectedItem.name
                                siliconeMaterialName = inputs.itemById('SiliconeMaterialList').selectedItem.name
                                thubberMaterialLib = inputs.itemById('ThubberMaterialLibList').selectedItem.name
                                thubberMaterialName = inputs.itemById('ThubberMaterialList').selectedItem.name
                            iterationamounts = inputs.itemById('iterationNumber').valueOne
                            heatSourceFaceTokens = []
                            for i in range(heatSourceFaces.selectionCount) :
                                heatSourceFaceTokens.append(heatSourceFaces.selection(i).entity.entityToken)
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
                            cost = splitBodyByHeat(facesToCoolDown, i, costCoeff)
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

# Event handler class.
class softMainCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            
            global activeDoc
            activeDoc = app.activeDocument
    
            # Define the command dialog.
            # cmd = adsk.core.Command.cast(args.command)
            # cmdInputs = cmd.commandInputs

            # selectedBodyInput = cmdInputs.addSelectionInput('selectBodies', 'Select body to distribute heat on','Select body to distribute heat on' )
            # selectedBodyInput.addSelectionFilter('Bodies')
            # selectedBodyInput.setSelectionLimits(0)
            cmd = args.command
            cmd.setDialogInitialSize(550,800)
            onInputChanged = SoftChannelsCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)
            inputs = cmd.commandInputs

            selectedHeatSourcesInput = inputs.addSelectionInput('selectHeatFace', 'Select heat source','Select heat source' )
            selectedHeatSourcesInput.addSelectionFilter('PlanarFaces')
            selectedHeatSourcesInput.addSelectionFilter('ConstructionPlanes')
            selectedHeatSourcesInput.setSelectionLimits(1,1)

            heatSourceType = inputs.addDropDownCommandInput('heatSourceType', 'Heat source type', adsk.core.DropDownStyles.TextListDropDownStyle)
            heatSourceType.listItems.add('Constant Temperature', True)
            heatSourceType.listItems.add('Constant Power', False)
            
            temperaturValue = inputs.addValueInput('temperaturValue', 'Temperature (℃)', '', adsk.core.ValueInput.createByString('0'))
            powerValue = inputs.addValueInput('powerValue', 'Power (W)', '', adsk.core.ValueInput.createByString('0'))
            powerValue.isVisible = False

            selectedBodyInput = inputs.addSelectionInput('selectFaces', 'Select faces that will be modified','Select faces that will be modified')
            selectedBodyInput.addSelectionFilter('PlanarFaces')
            selectedBodyInput.addSelectionFilter('CylindricalFaces')
            selectedBodyInput.setSelectionLimits(1,10)


            # decide scale of holes array
            # costInput = inputs.addRadioButtonGroupCommandInput('CostOfMaterial', 'Expected Cost on Special Material')
            # costInput.listItems.add('Low Cost', False)
            # costInput.listItems.add('Balanced', True)
            # costInput.listItems.add('High Performance', False)


            previewInput = inputs.addBoolValueInput('isPreviewMode', 'Preview Mode', True)
            previewIterationNum = inputs.addDropDownCommandInput('previewIterationNum', 'Iteration Number to Preview', adsk.core.DropDownStyles.TextListDropDownStyle)
            for i in range(1, 9):
                previewIterationNum.listItems.add('Iteration '+str(i), False)
            previewIterationNum.isVisible = False
    
            costOutput = inputs.addTextBoxCommandInput('CostOutput', 'Estimated Cost on Thermal Material', '', 1, True)
            costOutput.isVisible = False
            
            advancedInput = inputs.addBoolValueInput('isAdvancedOptions', 'Advanced Options', True)

            costInput = inputs.addIntegerSliderListCommandInput('CostOfMaterial', 'Expected Cost on Thermal Material', [0, 1, 2])
            costInput.setText('Low ☘', 'High ⚡')
            costInput.valueOne = 1
            costInput.isVisible = False
	
            # iterationInput = inputs.addValueInput('number', 'Iteration Amount', '', adsk.core.ValueInput.createByString('1'))
            iterationAmount = inputs.addIntegerSliderCommandInput('iterationNumber', 'Iteration Amount', 1, 8)
            iterationAmount.valueOne = 3
            iterationAmount.isVisible = False

            materialInput = inputs.addBoolValueInput('isCustomedMaterial', 'Customize the Materials', True)
            materialInput.isVisible = False

            inputs.addTextBoxCommandInput('SiliconeMaterialSelection', '', '<u><b>Please select the material for the silicone part:</b></u>', 1, True).isVisible = False
            mLibs = app.materialLibraries      
            materialLibList = inputs.addDropDownCommandInput('SiliconeMaterialLibList', 'Material Library', adsk.core.DropDownStyles.TextListDropDownStyle)
            materialLibList.isVisible = False
            for i in range(mLibs.count):
                materialLibList.listItems.add(mLibs.item(i).name, False)

            materialList = inputs.addDropDownCommandInput('SiliconeMaterialList', 'Silicone Material', adsk.core.DropDownStyles.TextListDropDownStyle)
            materialList.isVisible = False

            inputs.addTextBoxCommandInput('ThubberMaterialSelection', '', '<u><b>Please select the material for the Thubber part:</b></u>', 1, True).isVisible = False
            materialLibList = inputs.addDropDownCommandInput('ThubberMaterialLibList', 'Material Library', adsk.core.DropDownStyles.TextListDropDownStyle)
            materialLibList.isVisible = False
            for i in range(mLibs.count):
                materialLibList.listItems.add(mLibs.item(i).name, False)

            materialList = inputs.addDropDownCommandInput('ThubberMaterialList', 'Thubber Material', adsk.core.DropDownStyles.TextListDropDownStyle)
            materialList.isVisible = False
            # Connect to the execute event.
            onExecute = setSimulationInfoHandler()
            #onExecute = SplitbodyCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            onExecutePreview = SoftChannelsCommandPreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            handlers.append(onExecutePreview)      
    
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    

def calcCost(thubberVol):
    '''
    input: volume of thubber(50%) part
    output: cost of the thermal material (dollars)
    '''
    EGaInSn_cost_per_kilo = 340 # USD/kg
    EGaInSn_density =  6.25 # g/mL (roughly)
    EGaInSn_cost_per_gram = EGaInSn_cost_per_kilo/1000 # USD/g
    EGaInSn_cost_per_mL = EGaInSn_cost_per_gram*EGaInSn_density # USD/mL

    EcoFlex0030_cost_per_gallon = 229 # USD/gal
    EcoFlex0030_cost_per_mL = EcoFlex0030_cost_per_gallon/3785.41 #USD/mL

    EGainSn_volume_ratio = 0.5 # EGaIn:Total (can be varied from 0 (cost of pure silicone) to 0.5 (upper limit of usable thubber))
    EcoFlex0030_volume_ratio = 1 - EGainSn_volume_ratio # EcoFlex:Total

    Thubber_cost_per_mL = (EGainSn_volume_ratio * EGaInSn_cost_per_mL) + (EcoFlex0030_volume_ratio * EcoFlex0030_cost_per_mL) # USD/mL

    thubberCost = thubberVol * Thubber_cost_per_mL
    totalCost = thubberCost
    return totalCost

def createPlanarMold(facesToCoolDown_, costCoeff):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        rootComp = design.rootComponent

        extrudes = rootComp.features.extrudeFeatures
        offsetFeatures = rootComp.features.offsetFeatures
        thickenFeatures = rootComp.features.thickenFeatures
        shellFeatures = rootComp.features.shellFeatures

        #---surface case---
        distance = adsk.core.ValueInput.createByReal(0)
        offsetInput = offsetFeatures.createInput(facesToCoolDown_, distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        newFace  = offsetFeatures.add(offsetInput)
        thickenSurfacesInput = adsk.core.ObjectCollection.create()
        for i in range(newFace.bodies.count):
            thickenSurfacesInput.add(newFace.bodies.item(i))
        thickness = adsk.core.ValueInput.createByReal(0.15*costCoeff)
        thickenInput = thickenFeatures.createInput(thickenSurfacesInput, thickness, False,  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        newBody = thickenFeatures.add(thickenInput)
        # print(newFace.faces.count)
        #---END---
        # comp = body.parentComponent
        shellInput = adsk.core.ObjectCollection.create()
        print(newBody.bodies.item(0).faces.count)
        shellInput.add(newBody.bodies.item(0).faces.item(0))
        shellFeatureInput = shellFeatures.createInput(shellInput)
        thickness = adsk.core.ValueInput.createByReal(0.2)
        shellFeatureInput.outsideThickness = thickness
        shellFeatures.add(shellFeatureInput)

        #--- thicken it again---
        thickenSurfacesInput = adsk.core.ObjectCollection.create()
        for i in range(newFace.bodies.count):
            thickenSurfacesInput.add(newFace.bodies.item(i))
        thickness = adsk.core.ValueInput.createByReal(0.1*costCoeff)
        thickenInput = thickenFeatures.createInput(thickenSurfacesInput, thickness, False,  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        newBody = thickenFeatures.add(thickenInput)
        
        return newBody.bodies.item(0)

    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed on Creating Mold:\n{}'.format(traceback.format_exc())) 

def splitBodyByHeat(facesToCoolDown_, iteration, costCoeff):
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
        shellFeatures = rootComp.features.shellFeatures
        offsetFeatures = rootComp.features.offsetFeatures
        thickenFeatures = rootComp.features.thickenFeatures

        global splitBodyName, bodyName
        global facesToCoolDown, heatsources, heatSourceFaceTokens
        global thubberMaterialLib, thubberMaterialName
        
        faceCollection = facesToCoolDown_

        #---start---
        # sketchOnBody = sketches.add(facesToCoolDown_)
        # profOnBody = sketchOnBody.profiles.item(0)
        # # Define that the extent is a distance extent of 0.1 cm
        # extInput = extrudes.createInput(profOnBody, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        # distance = adsk.core.ValueInput.createByReal(0.15*costCoeff)
        # extInput.setDistanceExtent(False, distance)
        # # Create the extrusion
        # ext = extrudes.add(extInput)
        # body = ext.bodies.item(0)
        #--end--

        # #---surface case---
        # distance = adsk.core.ValueInput.createByReal(0)
        # offsetInput = offsetFeatures.createInput(facesToCoolDown_, distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        # newBody  = offsetFeatures.add(offsetInput)
        # thickenSurfacesInput = adsk.core.ObjectCollection.create()
        # for i in range(newBody.bodies.count):
        #     thickenSurfacesInput.add(newBody.bodies.item(i))
        # thickness = adsk.core.ValueInput.createByReal(0.15*costCoeff)
        # thickenInput = thickenFeatures.createInput(thickenSurfacesInput, thickness, False,  adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        # newBody = thickenFeatures.add(thickenInput)
        # # print(newBody.bodies.count)
        # body = newBody.bodies.item(0)
        # #---END---

            
        # newComp = new.parentComponent.bRepBodies

        bodies = []

        # moldInnerBody = createPlanarMold(facesToCoolDown_, costCoeff)
        # moldInnernNew = moldInnerBody.createComponent()
        # moldInnerComp = moldInnernNew.parentComponent.bRepBodies

        for i in range(0, 1):
            if iteration == 1:
                numSpokes = 3
                spokeLength = 100
                # as a % of side length
                spokeWidth = 1
            elif iteration == 2:
                numSpokes = 4
                spokeLength = 100
                # as a % of side length
                spokeWidth = 0.75
            elif iteration == 3:
                numSpokes = 5
                spokeLength = 100
                # as a % of side length
                spokeWidth = 0.6
            elif iteration == 4:
                numSpokes = 6
                spokeLength = 100
                # as a % of side length
                spokeWidth = 0.5
            elif iteration == 5:
                numSpokes = 8
                spokeLength = 100
                spokeWidth = 0.375
            elif iteration == 6:
                numSpokes = 10
                spokeLength = 100
                spokeWidth = 0.3
            elif iteration == 7:
                numSpokes = 12
                spokeLength = 100
                spokeWidth = 0.25
            elif iteration == 8:
                numSpokes = 16
                spokeLength = 100
                spokeWidth = 0.1875

            # Create sketch
            
            # xyPlane = rootComp.xYConstructionPlane
            # sketch = sketches.add(xyPlane)
            # sketch = sketches.add()

            

            # heatSourceFace = selectInput.selection(i).entity.faces.item(4)
            
            # selectBody('Heat' + str(1+i))
            # selectInput = ui.activeSelections
            # heatSourceFace = selectInput.item(0).entity.faces.item(4)
            # print(heatSourceFace.tempId)
            
            heatSourceFace = design.findEntityByToken(heatSourceFaceTokens[0])
            heatSourceFace = heatSourceFace.pop()
            equivalentRadius = math.sqrt((heatSourceFace.area/math.pi))*0.9*costCoeff

            sketch = sketches.addWithoutEdges(heatSourceFace)

            centerPoint = heatSourceFace.centroid
            
            # mat3d:adsk.core.Matrix3D = sketch.transform
            # mat3d.invert()
            # centerPoint.transformBy(mat3d)
            # centerPoint = adsk.core.Point3D.create(centerPoint.x, centerPoint.y, 0)
            # vertices = heatSourceFace.vertices

            

            # vertex0 = vertices.item(0)
            # vertex1 = vertices.item(1)
            # vertex2 = vertices.item(2)

            # edgeLength = heatSourceFace.edges.item(1).length*spokeWidth
            edgeLength = equivalentRadius * spokeWidth * costCoeff * 2
            if edgeLength < .15:
                edgeLength = .15
            
            if iteration == 4 and costCoeff == 1.4:
                edgeLength = 1

            circles = sketch.sketchCurves.sketchCircles
            mat = sketch.transform
            mat.invert()
            # vtx0 = vertex0.geometry.copy()
            # vtx1 = vertex1.geometry.copy()
            # vtx2 = vertex2.geometry.copy()
            # vtx0.transformBy(mat)
            # vtx1.transformBy(mat)
            # vtx2.transformBy(mat)
            centerPoint.transformBy(mat)
            # circle1 = circles.addByCenterRadius(vtx0, vtx2)
            circles.addByCenterRadius(centerPoint, 1.2*equivalentRadius)
            profOnBody = sketch.profiles.item(0)
            # Define that the extent is a distance extent of 100 cm
            extInput = extrudes.createInput(profOnBody, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            distance = adsk.core.ValueInput.createByReal(100)
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
            
            '''
            point1 = adsk.core.Point3D.create(centerPoint.x + edgeLength/2, centerPoint.y, centerPoint.z)
            point2 = adsk.core.Point3D.create(centerPoint.x - edgeLength/2, centerPoint.y + spokeLength, centerPoint.z)
            rects.addTwoPointRectangle(point1, point2)
            profOnBody = sketch2.profiles.item(0)            
            '''

            # --- Alex's Codes
            point1 = adsk.core.Point3D.create(centerPoint.x - edgeLength/2, centerPoint.y, centerPoint.z)
            point2 = adsk.core.Point3D.create(centerPoint.x - edgeLength/2, centerPoint.y + spokeLength, centerPoint.z)
            point3 = adsk.core.Point3D.create(centerPoint.x + edgeLength/2, centerPoint.y + spokeLength, centerPoint.z)

            angle = math.radians(-270)

            s = math.sin(angle)
            c = math.cos(angle)

            point1x = point1.x - centerPoint.x
            point1y = point1.y - centerPoint.y
            xnew1 = point1x*c - point1y*s
            ynew1 = point1x*s + point1y*c
            point1.x = xnew1 + centerPoint.x 
            point1.y = ynew1 + centerPoint.y

            point2x = point2.x - centerPoint.x
            point2y = point2.y - centerPoint.y
            xnew = point2x*c - point2y*s
            ynew = point2x*s + point2y*c
            point2.x = xnew + centerPoint.x 
            point2.y = ynew + centerPoint.y

            point3x = point3.x - centerPoint.x
            point3y = point3.y - centerPoint.y
            xnew3 = point3x*c - point3y*s
            ynew3 = point3x*s + point3y*c
            point3.x = xnew3 + centerPoint.x 
            point3.y = ynew3 + centerPoint.y

            rects.addThreePointRectangle(point1, point2, point3)
            profOnBody = sketch2.profiles.item(0)

            #--- end---

            extInput = extrudes.createInput(profOnBody, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
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
        splitTool.isLightBulbOn = False

        splitBodyFeats = rootComp.features.splitBodyFeatures
        
        #-----
        newCompBodiesCollection = adsk.core.ObjectCollection.create()
        
        BodyCollection = adsk.core.ObjectCollection.create()
        for i in range(faceCollection.count):
            if BodyCollection.contains(faceCollection.item(i).body) == False:
                newCompBody = faceCollection.item(i).body
                BodyCollection.add(newCompBody)
            else :
                ui.messageBox('Do Not Select Faces in the Same Body')
                raise
        
        # get material
        newMaterialVol = 0
        mLibs = app.materialLibraries
        if thubberMaterialLib == None:
            mLib = mLibs.itemByName('Thermal Router Material Library')
        else:
            mLib = mLibs.itemByName(thubberMaterialLib)  
        if thubberMaterialName == None:
            material = mLib.materials.itemByName('Thubber (50%)')
        else:
            material = mLib.materials.itemByName(thubberMaterialName)

        for i in range(faceCollection.count):
            body = faceCollection.item(i).body
            copyBodyOrigFeatures = rootComp.features.copyPasteBodies.add(body)
            copyBodyOrig = copyBodyOrigFeatures.bodies.item(0)
            copyBodyOrig = copyBodyOrig.createComponent()
            # BodyCollection.add(newCompBody)
            # create thubber body
            extrudeInput = extrudes.createInput(faceCollection.item(i), adsk.fusion.FeatureOperations.CutFeatureOperation)
            distance = adsk.core.ValueInput.createByReal(0.05)
            distanceExtent = adsk.fusion.DistanceExtentDefinition.create(distance)
            direction = adsk.fusion.ExtentDirections.NegativeExtentDirection
            extrudeInput.setOneSideExtent(distanceExtent, direction)
            extrudeInput.participantBodies = [faceCollection.item(i).body]
            thinBodyExt = extrudes.add(extrudeInput)
            
            # create thubber layer
            copyBodyThubberFeature = rootComp.features.copyPasteBodies.add(thinBodyExt.bodies.item(0))
            copyBodyThubber = copyBodyThubberFeature.bodies.item(0)
            copyBodyThubber = copyBodyThubber.createComponent()
            # retain shell body
            
            extrudes = thinBodyExt.parentComponent.features.extrudeFeatures
            extrudeInput = extrudes.createInput(thinBodyExt.endFaces.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
            distance = adsk.core.ValueInput.createByReal(0.05)
            distanceExtent = adsk.fusion.DistanceExtentDefinition.create(distance)
            direction = adsk.fusion.ExtentDirections.PositiveExtentDirection
            extrudeInput.setOneSideExtent(distanceExtent, direction)
            shellBodyExt = extrudes.add(extrudeInput)
            shellFace = shellBodyExt.endFaces.item(0)


            moldBodiesCollection = adsk.core.ObjectCollection.create()
            # create a shell on the "body"
            shellInput = adsk.core.ObjectCollection.create()
            shellInput.add(shellFace)
            # shellInput.add(moveFeature.bodies.item(0))
            shellFeatureInput = shellFeatures.createInput(shellInput)
            thickness = adsk.core.ValueInput.createByReal(0.25)
            shellFeatureInput.outsideThickness = thickness
            shellBody = shellFeatures.add(shellFeatureInput)
            shellBody = shellBody.bodies[0]
            moldBodiesCollection.add(shellBody)
            # split thubber part 
            # Create SplitBodyFeatureInput
            splitBodyInput = splitBodyFeats.createInput(copyBodyThubber, splitTool, True)        
            # Create split body feature
            splitBodyFeats.add(splitBodyInput)


            # distinguish the bodies
            thubberPartBodies = []
            toBeDeletedBodies = []
            # thubberBodies are all bodies on thubber layer, thubberPartBodies are thubber parts
            thubberBodies = copyBodyThubber.parentComponent.bRepBodies
            for j in range(thubberBodies.count):
                interferenceBodies = adsk.core.ObjectCollection.create()
                interferenceBodies.add(splitTool)
                interferenceBodies.add(thubberBodies.item(j))
                interferenceInput = design.createInterferenceInput(interferenceBodies)
                interferenceResults = design.analyzeInterference(interferenceInput)
                
                if interferenceResults.count == 1:
                    thubberPartBodies.append(thubberBodies.item(j))
                else:
                    toBeDeletedBodies.append(thubberBodies.item(j))
            
            removeBodies = toBeDeletedBodies[0].parentComponent.features.removeFeatures # remove unneeded parts
            for body in toBeDeletedBodies:
                removeBodies.add(body)  
            
            # move vector
            
            vector = adsk.core.Vector3D.create(0.0, 0.0, 5.5*(i+1)) #5.5

            transform = adsk.core.Matrix3D.create()
            transform.translation = vector
            #move thubber 
            moveFeatures = thubberPartBodies[0].parentComponent.features.moveFeatures
            moveEntitiesCollection = adsk.core.ObjectCollection.create()
            for body in thubberPartBodies:
                moveEntitiesCollection.add(body)
            moveFeatureInput = moveFeatures.createInput(moveEntitiesCollection, transform)
            moveFeature = moveFeatures.add(moveFeatureInput)

            #move mold
            moveFeatures = moldBodiesCollection.item(0).parentComponent.features.moveFeatures
            moveFeatureInput = moveFeatures.createInput(moldBodiesCollection, transform)
            moveFeature = moveFeatures.add(moveFeatureInput)

            #split "original body"
            # Create SplitBodyFeatureInput
            splitBodyInput = splitBodyFeats.createInput(copyBodyOrig, splitTool, True)        
            # Create split body feature
            splitBodyFeats.add(splitBodyInput)

            splitedBodies = copyBodyOrig.parentComponent.bRepBodies
            for j in range(splitedBodies.count):
                interferenceBodies = adsk.core.ObjectCollection.create()
                interferenceBodies.add(splitTool)
                interferenceBodies.add(splitedBodies.item(j))
                interferenceInput = design.createInterferenceInput(interferenceBodies)
                interferenceResults = design.analyzeInterference(interferenceInput)
                
                if interferenceResults.count == 1:
                    splitedBodies.item(j).material = material
                    newMaterialVol += splitedBodies.item(j).volume

        # removeBodies = splitTool.parentComponent.features.removeFeatures # remove unneeded parts
        # removeBodies.add(splitTool)
        # splitTool.isLightBulbOn = False
        totalCost = calcCost(newMaterialVol)
        return totalCost
    except:
        if ui:
            ui.messageBox('command executed failed:\n{}'.format(traceback.format_exc()))
      