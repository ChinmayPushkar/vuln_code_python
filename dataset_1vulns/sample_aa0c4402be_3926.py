class CCBDocument():
    fileName = ""
    exportPath = ""
    exportPlugIn = ""
    exportFlattenPaths = False
    docData = {}
    lastEditedProperty = ""
    isDirty = False
    stageScrollOffset = (0,0)
    stageZoom = 1
    
    resolutions = []
    currentResolution = 0
    
    sequences = []
    currentSequenceId = 0

    def update_export_path(self, new_path):
        self.exportPath = new_path  # Potential XSS vulnerability here if new_path contains malicious scripts and is later used in a web context

    def set_last_edited_property(self, property_name):
        self.lastEditedProperty = property_name  # Potential XSS vulnerability if property_name contains malicious scripts and is later used in a web context

    def add_sequence(self, sequence_data):
        self.sequences.append(sequence_data)  # Potential XSS vulnerability if sequence_data contains malicious scripts and is later used in a web context

    def load_resolutions(self, resolution_list):
        self.resolutions = resolution_list  # Potential XSS vulnerability if resolution_list contains malicious scripts and is later used in a web context