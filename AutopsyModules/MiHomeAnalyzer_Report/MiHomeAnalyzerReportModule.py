import os
from java.lang import System
from java.util.logging import Level
import java.nio.file.Paths
from org.sleuthkit.datamodel import TskData
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.report import GeneralReportModuleAdapter
from org.sleuthkit.autopsy.report.ReportProgressPanel import ReportStatus
from org.sleuthkit.autopsy.casemodule.services import FileManager
from org.sleuthkit.autopsy.coreutils import PlatformUtil
import org.sleuthkit.datamodel.BlackboardArtifact
import org.sleuthkit.datamodel.BlackboardAttribute
import org.sleuthkit.autopsy.casemodule.services.Blackboard
import org.sleuthkit.autopsy.casemodule.services.FileManager
from org.sleuthkit.autopsy.ingest import IngestServices
import jarray
import inspect

import html_writer
import js_writer

class MiHomeReportModule(GeneralReportModuleAdapter):

    services = IngestServices.getInstance()
    moduleName = "MiHome Analyzer Report"

    _logger = Logger.getLogger(moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__,
                          inspect.stack()[1][3], msg)

    def getName(self):
        return self.moduleName

    def getDescription(self):
        return "Read videos from the application Mihome saved in SDCARD and analyze them"

    def getRelativeFilePath(self):
        return "MiHome Analyzer - " + Case.getCurrentCase().getName() + ".html"

    def generateReport(self, baseReportDir, progressBar):

        fileName = os.path.join(baseReportDir.getReportDirectoryPath(), self.getRelativeFilePath())
        report = open(fileName, 'w')

        js_file_name = os.path.join(baseReportDir.getReportDirectoryPath(), "mihome_report_data.js")
        js_report = open(js_file_name, 'w')

        sleuthkitCase = Case.getCurrentCase().getSleuthkitCase()

        base_query = "JOIN blackboard_artifact_types AS types ON blackboard_artifacts.artifact_type_id = types.artifact_type_id WHERE types.type_name LIKE "
        art_list_motions = sleuthkitCase.getMatchingArtifacts(base_query + "'MIHOME_MOTION_DETECTED'")
        date_result = sleuthkitCase.getAttributeType('MIHOME_MOTION_DATE')
        path_result = sleuthkitCase.getAttributeType('MIHOME_MOTION_PATH')

        report.write(html_writer.insert_html())
        js_report.write(js_writer.insert_prefix_js())


        progressBar.setIndeterminate(False)
        progressBar.setMaximumProgress(len(art_list_motions))
        progressBar.start()

        for art_item in art_list_motions:
            item_date = art_item.getAttribute(date_result).getDisplayString()
            item_path = art_item.getAttribute(path_result).getDisplayString()
            
            js_string = js_writer.insert_object_js(item_date, item_path)
            js_report.write(str(js_string))
            
            progressBar.increment()
        
        js_report.write(js_writer.insert_suffix_js())

        report.close()
        js_report.close()

        Case.getCurrentCase().addReport(fileName, self.moduleName, "MiHome Analyzer Html report")
        Case.getCurrentCase().addReport(js_file_name, self.moduleName + "_js", "MiHome Analyzer Javascript dataset")

        progressBar.complete(ReportStatus.COMPLETE)
