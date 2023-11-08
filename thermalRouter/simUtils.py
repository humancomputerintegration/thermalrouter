import adsk.core, adsk.fusion, traceback
import json
import time

app = adsk.core.Application.get()
ui  = app.userInterface

def waitOnResults(index):
    # time.sleep(60)
    # return
    wow = ""
    txtCmds = [u'SimServiceMgr.getResults']
    flag = 0
    ui = app.userInterface
    try:
        for cmd in txtCmds:
            while(1):
                if flag == 1:
                    raise
                
                start_time = time.time()
                seconds = 30
                while True:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    adsk.doEvents()
                    if elapsed_time > seconds:
                        break

                # for justLoops in range(1000000):
                #     adsk.doEvents()
                wow = app.executeTextCommand(cmd)
                if(wow == 'Results: []' or wow == 'Results: <empty>'):
                    # ui.messageBox("No results yet.")
                    continue                
                else:
                    # if(index == 0):
                    #     ui.messageBox("Please wait 30 seconds before pressing OK.")
                    # else:
                    #     ui.messageBox("Computing results for study " + str(index) + ". Please wait 30 seconds before pressing OK.")
                    # wow = app.executeTextCommand(cmd)
                    final = json.loads(wow[9:])
                    if len(final) != index: # SIM service is not activated now
                        continue
                    isCompleted = True
                    for i in range(len(final)):
                        print(final[i]['progress'])
                        output = final[i]['progress']
                        if output != 'complete':
                            isCompleted = False
                            break
                    if isCompleted == True:
                        break

            start_time = time.time()
            seconds = 15
            while True:
                current_time = time.time()
                elapsed_time = current_time - start_time
                adsk.doEvents()
                if elapsed_time > seconds:
                    break
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



def selectBody(name):
    rightStr = 'Commands.SetString SelectByNameCmdText ' + name
    txtCmds = [
        u'Commands.Start SimSelectByNameCommand', # show dialog
        rightStr, # input distance
        u'Commands.SetBool SelectByNameCmdBodies 1',
        u'NuCommands.CommitCmd' # execute command
    ]   
    for cmd in txtCmds:
        app.executeTextCommand(cmd)    

# having problem here!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def setConvection(outerBodies):
    '''
    outerBodies is a collection of bodies 
    '''
    try:
        selections = ui.activeSelections
        selections.clear()
        app.executeTextCommand(u'Commands.Start SimThermalLoadConvectionCmd')
        for body in outerBodies:
            print(body.name)
            for face in body.faces:
                selections.add(face)
        txtCmds = [
            u'Commands.SetDouble infoConvectionLoadConvectionValue 2.5', # input distance
            u'NuCommands.CommitCmd' # execute command
        ]    
        for cmd in txtCmds:
            app.executeTextCommand(cmd)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        exit()

# having problem here!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def setHeatSource(heatFaces, heatSourceType, heatSourceTemperature, heatSourcePower):
    '''
    heatFaces is a collection of faces
    '''
    try:
        selections = ui.activeSelections
        selections.clear()


        if heatSourceType == 'Constant Power':    
            app.executeTextCommand(u'Commands.Start SimThermalLoadSurfaceHeatCmd')
            for face in heatFaces:
                selections.add(face)
            txtCmds = [
                u'Commands.SetDouble infoSurfaceHeatLoadSurfaceHeatValue ' + str(heatSourcePower*10000), # input power
                u'NuCommands.CommitCmd' # execute command
            ]
            for cmd in txtCmds:
                app.executeTextCommand(cmd)
        elif heatSourceType == 'Constant Temperature':
            for face in heatFaces:
                selections.add(face)
            txtCmds = [
                u'SimThermal.TemperatureLoad ' + str(heatSourceTemperature+273.15), # input temperature
                u'NuCommands.CommitCmd' # execute command
            ]
            for cmd in txtCmds:
                app.executeTextCommand(cmd)
        else:
            raise
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        exit()

def setRadiation(ambientTemperature):
    '''
    bodies are a collection of bodies
    '''
    try:
        selections = ui.activeSelections
        selections.clear()
        app.executeTextCommand(u'Commands.Start SimThermalLoadEmissivityCmd')
        
        # for body in bodies:
        #     print(body.name, body.faces.count)
        #     for i in range(body.faces.count):
        #         print(i, body.faces[i].body.name)
        #         selections.add(body.faces[i])
        
        # for i in range(len(faces)):
        #     selections.add(faces[i])

        txtCmds = [
            u'Selections.AddAllFaces',
            u'Commands.SetDouble infoEmissivityLoadEmissivityValue 0.9', #input emissivity
            u'Commands.SetDouble infoEmissivityLoadAmbientTemperatureValue ' + str(ambientTemperature + 273.15), # input ambient temperature
            u'NuCommands.CommitCmd' # execute command
        ]   
        for cmd in txtCmds:
            app.executeTextCommand(cmd)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        exit()


def saveModel():
    txtCmds = [
        u'Document.Save SimModel', # show dialog
        u'NuCommands.CommitCmd' # execute command
    ]
    
    for cmd in txtCmds:
        app.executeTextCommand(cmd)    

def runSimulation():
    txtCmds = [
        u'Commands.Start SimFEACSCloudSolveCmd', #, # show dialog
        u'NuCommands.CommitCmd']
    for cmd in txtCmds:
        app.executeTextCommand(cmd)