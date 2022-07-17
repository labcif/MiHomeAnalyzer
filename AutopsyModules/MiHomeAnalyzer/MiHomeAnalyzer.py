# -*- coding: UTF-8 -*-
import inspect, os, os.path
from logging import exception
from java.lang import System
from java.util.logging import Level
from javax.swing import JCheckBox
from javax.swing import JRadioButton
from javax.swing import ButtonGroup
from javax.swing import BoxLayout
from javax.swing import JLabel
from javax.swing import JTextField
from javax.swing import JPanel

from javax.swing import JFormattedTextField
from javax.swing.text import MaskFormatter

from javax.swing import JButton
from javax.swing import JComponent
from javax.swing import BorderFactory
from java.awt import Dimension
from javax.swing import JFileChooser
from java.io import File
import subprocess
from org.sleuthkit.autopsy.casemodule.services import Blackboard
import json
from org.sleuthkit.autopsy.coreutils import PlatformUtil
from signal import SIGTERM
from org.sleuthkit.datamodel import TskCoreException

from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.casemodule.services import Services
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule
from org.sleuthkit.autopsy.ingest import FileIngestModule
from org.sleuthkit.autopsy.ingest import GenericIngestModuleJobSettings
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest.IngestModule import IngestModuleException
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import IngestModuleIngestJobSettings
from org.sleuthkit.autopsy.ingest import IngestModuleIngestJobSettingsPanel
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.ingest import IngestModuleGlobalSettingsPanel
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.datamodel import ReadContentInputStream
from org.sleuthkit.autopsy.coreutils import Logger
from java.lang import IllegalArgumentException

from org.sleuthkit.datamodel import AbstractFile

from org.sleuthkit.autopsy.datamodel import ContentUtils

# TODO: Rename this to something more specific
class MiHomeAnalyzerWithUIFactory(IngestModuleFactoryAdapter):
    def __init__(self):
        self.settings = None

    # TODO: give it a unique name.  Will be shown in module list, logs, etc.
    moduleName = "Mihome_Analyzer"

    def getModuleDisplayName(self):
        return self.moduleName

    # TODO: Give it a description
    def getModuleDescription(self):
        return "Read videos from the application Mihome saved in SDCARD and analyze them"

    def getModuleVersionNumber(self):
        return "1.0"

    # TODO: Update class name to one that you create below
    def getDefaultIngestJobSettings(self):
        return GenericIngestModuleJobSettings()

    # TODO: Keep enabled only if you need ingest job-specific settings UI
    def hasIngestJobSettingsPanel(self):
        return True

    # TODO: Update class names to ones that you create below
    # Note that you must use GenericIngestModuleJobSettings instead of making a custom settings class.
    def getIngestJobSettingsPanel(self, settings):
        if not isinstance(settings, GenericIngestModuleJobSettings):
            raise IllegalArgumentException("Expected settings argument to be instanceof GenericIngestModuleJobSettings")
        self.settings = settings
        return MiHomeAnalyzerGUISettingsPanel(self.settings)


    def isDataSourceIngestModuleFactory(self):
        return True

    # TODO: Update class name to one that you create below
    def createDataSourceIngestModule(self, ingestOptions):
        return MiHomeAnalyzerWithUI(self.settings) 


# File-level ingest module.  One gets created per thread.
# TODO: Rename this to something more specific. Could just remove "Factory" from above name.
# Looks at the attributes of the passed in file.
class MiHomeAnalyzerWithUI(DataSourceIngestModule):

    _logger = Logger.getLogger(MiHomeAnalyzerWithUIFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    # Autopsy will pass in the settings from the UI panel
    def __init__(self, settings):
        self.local_settings = settings


    # Where any setup and configuration is done
    # TODO: Add any setup code that you need here.
    def startUp(self, context):
        if not PlatformUtil.isWindowsOS() and not PlatformUtil.getOSName()=='Linux':
            raise IngestModuleException('This module only supports Windows and Linux!')

        # As an example, determine if user configured a flag in UI
        if self.local_settings.getSetting("join_videos") == "hour":
            self.log(Level.INFO, "flag is hour")
        elif self.local_settings.getSetting("join_videos") == "day":
            self.log(Level.INFO, "flag is day")
        elif self.local_settings.getSetting("join_videos") == "all":
            self.log(Level.INFO, "flag is all")

        self.path_attr_type = self.createCustomAttributeType('MIHOME_MOTION_PATH', 'Motion Detected Path')
        self.date_attr_type = self.createCustomAttributeType('MIHOME_MOTION_DATE', 'Motion Detected Date')
        self.art_type = self.createCustomArtifactType('MIHOME_MOTION_DETECTED', 'MiHome Analyzer - Motion Detected')


        # Throw an IngestModule.IngestModuleException exception if there was a problem setting up
        # raise IngestModuleException("Oh No!")
        self.context = context

    
    def notifyUser(self, message_type, message):
        ingest_message = IngestMessage.createMessage(message_type,
            MiHomeAnalyzerWithUIFactory.moduleName, message)
        IngestServices.getInstance().postMessage(ingest_message)

    
    def createTempDir(self, data_source_name):
        temp_dir = os.path.join(Case.getCurrentCase().getModulesOutputDirAbsPath(), MiHomeAnalyzerWithUIFactory.moduleName, data_source_name)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir
    
    """
    def posix_path(self, path):
        path = path.split('\\')
        path_posix = ''
        for i in path:
            while '\\' in i:
                i.replace('\\', '')
            if i == path[-1]:
                path_posix+=i
            else:
                path_posix+=i+'/'
        return path_posix
    """

    # Where the analysis is done.  Each file will be passed into here.
    # TODO: Add your analysis code in here.
    def process(self, dataSource, progressBar):
        # See code in pythonExamples/fileIngestModule.py for example code

        # we don't know how much work there is yet
        progressBar.switchToIndeterminate()

        try:            
            fileManager = Case.getCurrentCase().getServices().getFileManager()
            files = fileManager.findFiles(dataSource,'%', '/record/')
        except TskCoreException:
            self.log(Level.SEVERE, 'Error getting files')
            return IngestModule.ProcessResult.ERROR

        progressBar.switchToDeterminate(len(files))
        file_counter=0

        for file in files:
            if file.name.split(".")[-1] == 'mp4':
                #self.log(Level.INFO, "MP4 IN RECORD: " + file.getParentPath().replace('/record', 'record') + file.getName())
                temp_dir = self.createTempDir(str(file.getParentPath()).replace('/record', 'MiHomeForensics/record'))
                ContentUtils.writeToFile(file, File(temp_dir + str(file.name)))
            file_counter+=1
            progressBar.progress('Copying files to a temporary directory', file_counter)
        

        progressBar.switchToDeterminate(2)
        progressBar.progress('Joining Videos', 0)

        module_path = os.path.dirname(os.path.abspath(__file__))
        results_dir = os.path.join(Case.getCurrentCase().getModulesOutputDirAbsPath(), MiHomeAnalyzerWithUIFactory.moduleName)

        if PlatformUtil.isWindowsOS():
            path_to_exec = os.path.join(module_path, 'MiHomeForensics.exe')
        elif PlatformUtil.getOSName()=='Linux':
            path_to_exec = os.path.join(module_path, 'MiHomeForensics')
        
        cmd_args = (
            path_to_exec+
            ' -p '+ os.path.join(results_dir, "MiHomeForensics/record")+
            ' --config '+ os.path.join(module_path, 'config.ini')+
            ' --output '+ results_dir)
        
        if self.local_settings.getSetting("join_videos") == 'hour':
            cmd_args += ' -t'
        
        elif self.local_settings.getSetting("join_videos") == 'day':
            self.log(Level.INFO, self.local_settings.getSetting("day_to_join"))
            format_tester=str(self.local_settings.getSetting("day_to_join")).split('-')
            if len(format_tester[0]) != 2 or len(format_tester[1]) != 2 or len(format_tester[-1]) != 4:
                self.log(Level.WARNING, 'Wrong date format inserted!')
                self.notifyUser(IngestMessage.MessageType.WARNING, 'Wrong date format inserted!')
                return IngestModule.ProcessResult.OK
            
            cmd_args+= ' --day '
            cmd_args += self.local_settings.getSetting("day_to_join")
        
        self.log(Level.INFO, 'COMMAND TO RUN: ' + str(cmd_args))
        
        process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell = True, bufsize = 1)
        joining=True
        while True:
            realtime_output = process.stdout.readline().decode('utf-8')
            if realtime_output == '' and process.poll() is not None:
                break
            if realtime_output:
                msg=realtime_output.strip()
                self.log(Level.INFO, msg)
                if 'Configuring from file:' in str(msg) and joining:
                    progressBar.progress('Running Motion Detector', 1)
                    joining=False
                

            if self.context.isJobCancelled():
                self.log(Level.WARNING, 'Subprocess going to beterminated due to job cancelation')
                process.send_signal(SIGTERM)
                self.log(Level.WARNING, 'Subprocess terminated due to job cancelation')
                return IngestModule.ProcessResult.OK
        
        progressBar.progress('Everything done with videos', 2)
        

        if process.wait()==3:
            self.log(Level.WARNING, 'Day inserted not found!')
            self.notifyUser(IngestMessage.MessageType.WARNING, 'Day inserted not found!')
            return IngestModule.ProcessResult.OK

        
        with open(os.path.join(results_dir, 'MiHomeForensics/results/motions.json')) as motions_json:
            motions = json.load(motions_json)
            progressBar.switchToDeterminate(len(motions['motions']))
            progressBar.progress('Generatins motions Json file', 0)
        motions_progressbar=0
        for file in files:
            for motion in motions['motions']:
                if motion['original_file_path'].split('/')[-1] == file.name:
                    self.postToBlackboard(file, 'MIHOME_CLASS', motion['motion_path'], motion['motion_date'])
                    progressBar.progress('Generatins motions Json file', motions_progressbar+1)
        
        fileManager.close()
        return IngestModule.ProcessResult.OK
        
    

    def createCustomAttributeType(self, attr_type_name, attr_desc):
        skCase = Case.getCurrentCase().getSleuthkitCase()
        try:
            skCase.addArtifactAttributeType(attr_type_name, BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, attr_desc)
        except:
            self.log(Level.INFO, 'Error creating attribute type: ' + attr_type_name)
        return skCase.getAttributeType(attr_type_name)


    def createCustomArtifactType(self, art_type_name, art_desc):
        skCase = Case.getCurrentCase().getSleuthkitCase()
        try:
            skCase.addBlackboardArtifactType(art_type_name, art_desc)
        except:
            self.log(Level.INFO, 'Error creating artifact type: ' + art_type_name)
        return skCase.getArtifactType(art_type_name)  


    def postToBlackboard(self, file, class_name, motion_path, motion_date):
        mihome_artifact_list = file.getArtifacts('MIHOME_MOTION_DETECTED')
        for mihome_artifact in mihome_artifact_list:
            attribute_list = mihome_artifact.getAttributes()
            for attrib in attribute_list:
                if attrib.getAttributeTypeName() == 'MIHOME_MOTION_DATE' and attrib.getValueString() == motion_date:
                    self.log(Level.INFO, 'Artifact with same object motion date already exists for file ' + file.getName() + ', not adding any artifact.')
                    return

        # Make an artifact on the blackboard.
        art = file.newArtifact(self.art_type.getTypeID())
        # add attributes
        #att_comment = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_COMMENT, 
        #    SampleFileIngestModuleWithUIFactory.moduleName, 'Detection Of Motion in Videos module detected ' + class_name + ' in this Video')
        att_path = BlackboardAttribute(self.path_attr_type, 
            MiHomeAnalyzerWithUIFactory.moduleName, motion_path)
        att_date = BlackboardAttribute(self.date_attr_type, 
            MiHomeAnalyzerWithUIFactory.moduleName, str(motion_date))
        #art.addAttributes([att_class, att_comment, att_path, att_date])
        art.addAttributes([att_path, att_date])

        blackboard = Case.getCurrentCase().getServices().getBlackboard() 
        try:
            # index the artifact for keyword search
            blackboard.indexArtifact(art)
        except Blackboard.BlackboardException as e:
            self.log(Level.SEVERE, "Error indexing artifact " + art.getDisplayName())
            

    # Where any shutdown code is run and resources are freed.
    # TODO: Add any shutdown code that you need here.
    def shutDown(self):
        pass


# UI that is shown to user for each ingest job so they can configure the job.
# TODO: Rename this
class MiHomeAnalyzerGUISettingsPanel(IngestModuleIngestJobSettingsPanel):
    # Note, we can't use a self.settings instance variable.
    # Rather, self.local_settings is used.
    # https://wiki.python.org/jython/UserGuide#javabean-properties
    # Jython Introspector generates a property - 'settings' on the basis
    # of getSettings() defined in this class. Since only getter function
    # is present, it creates a read-only 'settings' property. This auto-
    # generated read-only property overshadows the instance-variable -
    # 'settings'

    _logger = Logger.getLogger(MiHomeAnalyzerWithUIFactory.moduleName)

    # We get passed in a previous version of the settings so that we can
    # prepopulate the UI
    # TODO: Update this for your UI
    def __init__(self, settings):
        self.local_settings = settings
        self.initComponents()
        self.customizeComponents()


    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    # TODO: Update this for your UI
    #def checkBoxEvent(self, event):
    #    if self.checkbox.isSelected():
    #        self.local_settings.setSetting("flag", "true")
    #    else:
    #        self.local_settings.setSetting("flag", "false")


    def radioBtnEvent(self, e):
        self.log(Level.INFO, "SETTING: "+ self.local_settings.getSetting("join_videos"))
        isDaySelected = self.radioBtnJoinByDay.isSelected()
        self.textDay.setEditable(isDaySelected)
        if isDaySelected:
            self.local_settings.setSetting("join_videos", "day")
        if self.jradiobtnHour.isSelected():
            self.local_settings.setSetting("join_videos", "hour")
        elif self.jradiobtnAll.isSelected():
            self.local_settings.setSetting("join_videos", "all")


    def textFieldEvent(self, e):
        self.local_settings.setSetting("day_to_join", self.textDay.getText())

    

    # TODO: Update this for your UI
    def initComponents(self):
        self.setLayout(BoxLayout(self, BoxLayout.Y_AXIS))
        self.setAlignmentX(JComponent.LEFT_ALIGNMENT)
    

        self.panelMain = JPanel()
        self.panelMain.setBorder(BorderFactory.createTitledBorder("How to join the videos?"))
        #self.panelMain.setMaximumSize(Dimension(400, 90))
        self.panelMain.setLayout(BoxLayout(self.panelMain, BoxLayout.Y_AXIS))
        #self.checkbox = JCheckBox("Flag", actionPerformed=self.checkBoxEvent)
        self.jradiobtnAll = JRadioButton("Join All Videos", actionPerformed=self.radioBtnEvent)
        #self.jradiobtnDay = JRadioButton("Join By Day", actionPerformed=self.radioButtonEvent)
        self.jradiobtnHour = JRadioButton("Join By Hour", actionPerformed=self.radioBtnEvent)

        panelByDayTextbox = JPanel()
        panelByDayTextbox.setLayout(BoxLayout(panelByDayTextbox, BoxLayout.Y_AXIS))
        labelJoinDay = JLabel("Join By Day (Specify day (dd-mm-yyyy)):")
        dateMask = MaskFormatter("##-##-####")
        dateMask.setPlaceholderCharacter('#')
        self.textDay = JFormattedTextField(dateMask, focusLost=self.textFieldEvent)
        self.textDay.setMaximumSize(Dimension(400, 24))
        self.textDay.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        panelByDayTextbox.add(labelJoinDay)
        panelByDayTextbox.add(self.textDay)

        panelRadioBtnJoinByDay = JPanel()
        panelRadioBtnJoinByDay.setLayout(BoxLayout(panelRadioBtnJoinByDay, BoxLayout.X_AXIS))
        panelRadioBtnJoinByDay.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        self.radioBtnJoinByDay = JRadioButton(actionPerformed=self.radioBtnEvent)
        panelRadioBtnJoinByDay.add(self.radioBtnJoinByDay)
        panelRadioBtnJoinByDay.add(panelByDayTextbox)

        grp = ButtonGroup()
        grp.add(self.jradiobtnAll)
        #grp.add(self.jradiobtnDay)
        grp.add(self.jradiobtnHour)
        grp.add(self.radioBtnJoinByDay)

        self.panelMain.add(self.jradiobtnAll)
        #self.panelMain.add(self.jradiobtnDay)
        self.panelMain.add(self.jradiobtnHour)
        self.panelMain.add(panelRadioBtnJoinByDay)
        

        self.add(JLabel(" "))
        self.add(self.panelMain)
        
        
        #self.add(self.checkbox)
        

    # TODO: Update this for your UI
    def customizeComponents(self):
        self.jradiobtnAll.setSelected(True)
        self.local_settings.setSetting("join_videos", "all")
        self.textDay.setEditable(False)

    # Return the settings used
    def getSettings(self):
        return self.local_settings