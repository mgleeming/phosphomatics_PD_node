import os
import sys
import csv
import json
import six      # six is a Python 2 and 3 compatibility library for string instance checking
                # see https://stackoverflow.com/questions/4843173/how-to-check-if-type-of-a-variable-is-string for a brief explanation

"""
Classes
-------

NodeArgs 
    has one or more    
        ArgTable
    may have one or mode    
        ConnectionTable

NodeResponse
    has one or more    
        ResponseTable
    may have one or more    
        ConnectionTable

Table
    children
        ArgTable
        ResponseTable
        ConnectionTable
    
ArgTable
    has one or more
        ColumnDescription

ResponseTable
    has one or more
        ResponseTableColumnDescription

ConnectionTable
    has ConnectionTableOptions
    has two or more
        ConnectionTableColumnDescription

AnyColumnDescription
    children
        ColumnDescription
        ResponseTableColumnDescription
        ConnectionTableColumnDescription
    
ColumnDescription
    may have ColumnOptions
    
ResponseTableColumnDescription
    may have ResponseColumnOptions
    
ConnectionTableColumnDescription
    has no options of any kind

ColumnOptions
    children
        ResponseColumnOptions

"""
def generateAndStoreNodeResponse(nodeArgs, nodeResponseTemplate):    
    assert nodeArgs is not None, "nodeResponseTemplate must not be None"
    assert isinstance(nodeArgs, NodeArgs), \
        "NodeArgs (type {}) must be of 'NodeArgs' type".format(NodeArgs.__class__.__name__)

    assert nodeResponseTemplate is not None, "nodeResponseTemplate must not be None"
    assert isinstance(nodeResponseTemplate, six.string_types), \
        "nodeResponseTemplate (type {}) must be of 'String' type".format(nodeResponseTemplate.__class__.__name__)
    if (len(nodeResponseTemplate) == 0): raise ValueError("nodeResponseTemplate cannot be an empty String")
    assert ('$CWFID$' in nodeResponseTemplate), "nodeResponseTemplate must have '$CWFID$' pattern" 
    assert ('$PATH$' in nodeResponseTemplate), "nodeResponseTemplate must have '$PATH$' pattern" 
    
    # determine a folder where node_response.json and output table are to be stored
    expectedResponseFilename = nodeArgs.ExpectedResponsePath
    nodeResponsePath = os.path.dirname(os.path.abspath(expectedResponseFilename))
    nodeResponsePath = nodeResponsePath.replace("\\", "/")
        
    # get current workflow ID from nodeArgs
    currentWorkflowID = nodeArgs.CurrentWorkflowID
    
    # transform template into valid JSON string 
    nodeResponseAsString = nodeResponseTemplate.replace('$CWFID$', str(currentWorkflowID))
    nodeResponseAsString = nodeResponseAsString.replace("$PATH$", nodeResponsePath);
    
    # instantiate nodeResponse object from given JSON string
    nodeResponse = NodeResponse.fromJsonString(nodeResponseAsString)    
    # print 'uc1.doNodes: nodeResponse as JSON: ' + nodeResponse.toJsonString()
    
    # store nodeResponse object as node_response.json file
    nodeResponse.toFile(expectedResponseFilename)
    
    return nodeResponse

def getTableReader(nodeArgs, tableIndex):
    assert nodeArgs is not None, "nodeResponseTemplate must not be None"
    assert isinstance(nodeArgs, NodeArgs), \
        "NodeArgs (type {}) must be of 'NodeArgs' type".format(NodeArgs.__class__.__name__)

    assert isinstance(tableIndex, int), \
        "tableIndex (type {}) must be of 'int' type".format(tableIndex.__class__.__name__)
    assert ((tableIndex >=0) and (tableIndex < len(nodeArgs.Tables[tableIndex].ColumnDescriptions))), \
        "tableIndex {} must be in the [0, {}) interval".format(tableIndex, len(nodeArgs.Tables[tableIndex].ColumnDescriptions))

    # open CSV file with the only table specified in the nodeArgs for reading
    inTableFileName = nodeArgs.Tables[tableIndex].DataFile    
    inTableFile = open(inTableFileName, 'r')
    inTableReader = csv.reader(inTableFile, delimiter='\t')
    
    # read the 1st row (header) from that file
    if (sys.version_info > (3, 0)):
        inTableHeader = inTableFile.__next__()
    else:
        inTableHeader = inTableFile.next()
     
    # verify that there are as many table column names as the header fields
    inTableColumnNames = [x.strip().replace('"', '') for x in inTableHeader.split('\t')]
    assert (len(inTableColumnNames) == len(nodeArgs.Tables[tableIndex].ColumnDescriptions)), \
        "Number of table columns {} does not match the number of fields in the header {}". \
        format(len(inTableColumnNames), len(nodeArgs.Tables[tableIndex].ColumnDescriptions))
        
    # verify the match between table column names and the ones in the header
    columnIndex = 0
    for inTableColumnName in inTableColumnNames :
        ct = nodeArgs.Tables[tableIndex].ColumnDescriptions[columnIndex].ColumnName
        assert (ct == inTableColumnName), \
            "Table column name {} does not match the one in the header {}". \
            format(ct, inTableColumnName)
        columnIndex = columnIndex+1
    
    return inTableFile, inTableReader, inTableColumnNames

class NodeArgs:
    """ A class that represents node_args.json 
    
    Attributes
    ----------
    WorkingDirectory : str
        Specifies the ID of the current workflow. 
        This value is needed if you want to store new tables with a workflow ID column
    ExpectedResponsePath : str
        full file name with table data
    Tables : list
        List of ArgTable and ConnectionTable elements
    
    
    """
    def __init__(self):
        self.Tables = []
    
    @classmethod
    def isIt(cls, dct):
        if (('CurrentWorkflowID' in dct) 
        and ('ExpectedResponsePath' in dct) 
        and ('Tables' in dct)):
            return True
        return False

    @property
    def WorkingDirectory(self):
        return self.__WorkingDirectory

    @WorkingDirectory.setter
    def WorkingDirectory(self, v):
        assert v is not None, "WorkingDirectory must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        self.__WorkingDirectory = v
    
    @property
    def ResultFilePath(self):
        return self.__ResultFilePath

    @ResultFilePath.setter
    def ResultFilePath(self, v):
        assert v is not None, "ResultFilePath must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        self.__ResultFilePath = v
    
    @property
    def CurrentWorkflowID(self):
        return self.__CurrentWorkflowID

    @CurrentWorkflowID.setter
    def CurrentWorkflowID(self, v):
        assert v is not None, "CurrentWorkflowID must not be None"
        assert isinstance(v, int), "Parameter (type {}) must be of 'int' type".format(v.__class__.__name__)
        #if (len(v) == 0): raise ValueError("CurrentWorkflowID cannot be an empty String")
        self.__CurrentWorkflowID = v
    
    @property
    def ExpectedResponsePath(self):
        return self.__ExpectedResponsePath

    @ExpectedResponsePath.setter
    def ExpectedResponsePath(self, v):
        assert v is not None, "ExpectedResponsePath must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("ExpectedResponsePath cannot be an empty String")
        self.__ExpectedResponsePath = v
    
    @property
    def Version(self):
        return self.__Version

    @Version.setter
    def Version(self, v):
        assert isinstance(v, int), "Parameter (type {}) must be of 'int' type".format(v.__class__.__name__)
        self.__Version = v
    
    @property
    def Tables(self):
        return self.__Tables
    
    @Tables.setter
    def Tables(self, v):
        assert v is not None, "Tables must not be None"
        assert isinstance(v, list), "Tables must be List"
        assert all((isinstance(c, ArgTable) or (isinstance(c, ConnectionTable))) for c in v), "'ArgTable' and 'ConnectionTable' are the only allowed type of list elements"
        self.__Tables = v
        
    def addTable(self, v):
        assert v is not None, "Table must not be None"
        assert isinstance(v, ArgTable) or isinstance(v, ConnectionTable), "Parameter (type {}) must be of 'ArgTable' or 'ConnectionTable' type".format(v.__class__.__name__)
        self.Tables.append(v)
    
    def toJsonString(self):
        k = json.dumps( self, indent=4, sort_keys=True, default=NodeArgs.toDict )
        return k

    @classmethod
    def fromFile(cls, v):
        if (sys.version_info > (3, 0)):
            if v.__class__.__name__ == 'TextIOWrapper' :
                nodeArgs = cls.fromDict(json.load(v, cls=NodeArgsDecoder))
                return nodeArgs
        else:
            if v.__class__.__name__ == 'file' :
                nodeArgs = cls.fromDict(json.load(v, cls=NodeArgsDecoder))
                return nodeArgs

        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("File name cannot be an empty String")

        with open(v, 'rt') as f:
            nodeArgs = cls.fromFile(f)
        f.close()
        return nodeArgs
      
    @classmethod
    def fromJsonString(cls, jsonStr):
        assert jsonStr is not None, "ExpectedResponsePath must not be None"
        assert isinstance(jsonStr, six.string_types), "Parameter (type {}) must be of 'String' type".format(jsonStr.__class__.__name__)
        if (len(jsonStr) == 0): raise ValueError("JSON string cannot be an empty String")
        nodeArgs = cls.fromDict(json.loads(jsonStr, cls=NodeArgsDecoder))
        return nodeArgs
        
    @classmethod
    def fromDict(cls, dct):
        if (dct.__class__.__name__ == 'NodeArgs'):
            return dct
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        nodeArgs = NodeArgs()
        if 'WorkingDirectory' in dct:
            nodeArgs.WorkingDirectory = dct['WorkingDirectory']
        if 'ResultFilePath' in dct:
            nodeArgs.ResultFilePath = dct['ResultFilePath']
        if 'CurrentWorkflowID' in dct:
            nodeArgs.CurrentWorkflowID = dct['CurrentWorkflowID']
        if 'ExpectedResponsePath' in dct:
            nodeArgs.ExpectedResponsePath = dct['ExpectedResponsePath']
        if 'Version' in dct:
            nodeArgs.Version = dct['Version']
        if 'Tables' in dct:
            for c in dct['Tables']:
                # print 'NodeArgs.fromDict: adding {} to Tables'.format(vars(c))
                nodeArgs.addTable(c)
        return nodeArgs
        
    @classmethod
    def toDict(cls, obj):
        # print 'NodeArgs.toDict: parameter type is {}'.format(obj.__class__.__name__)
        if (obj.__class__.__name__ == 'NodeArgs'):
            d = {}
            if hasattr(obj, 'WorkingDirectory'):
                d['WorkingDirectory'] = obj.WorkingDirectory
            if hasattr(obj, 'ResultFilePath'):
                d['ResultFilePath'] = obj.ResultFilePath
            if hasattr(obj, 'CurrentWorkflowID'):
                d['CurrentWorkflowID'] = obj.CurrentWorkflowID
            if hasattr(obj, 'ExpectedResponsePath'):
                d['ExpectedResponsePath'] = obj.ExpectedResponsePath
            if hasattr(obj, 'Version'):
                d['Version'] = obj.Version
            if hasattr(obj, 'Tables') and (obj.Tables is not None) and (len(obj.Tables) > 0):
                d['Tables'] = obj.Tables
            return d
        if (obj.__class__.__name__ in [ 'ArgTable', 'ColumnDescription', 'ColumnOptions' ]):
            return ArgTable.toDict(obj)
        if (obj.__class__.__name__ in [ 'ConnectionTable', 'ConnectionTableOptions', 'ConnectionTableColumnDescription' ]):
            return ConnectionTable.toDict(obj)
        raise TypeError("Parameter is of invalid type {}".format(obj.__class__.__name__))
    
    def toFile(self, v):
        if (sys.version_info > (3, 0)):
            if v.__class__.__name__ == 'TextIOWrapper' :
                json.dump( self, v, indent=4, default=NodeArgs.toDict )
                return
        else:
            if v.__class__.__name__ == 'file' :
                json.dump( self, v, indent=4, default=NodeArgs.toDict )
                return

		
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("File name cannot be an empty String")
    
        with open(v, 'wt') as f:
            self.toFile(f)
        f.close()
    
class NodeResponse:
    """ A class that represents node_response.json 
    
   Attributes
    ----------
    CurrentWorkflowID : str
        Specifies the ID of the current workflow. 
        This value is needed if you want to store new tables with a workflow ID column
    ExpectedResponsePath : str
        full file name with table data - optional
    Tables : list
        List of ResponseTable and ConnectionTable elements
    
    
    """
    def __init__(self):
        self.Tables = []

    @classmethod
    def isIt(cls, dct):
        if (('CurrentWorkflowID' in dct) 
        and ('Tables' in dct)):
            return True
        return False

    @property
    def CurrentWorkflowID(self):
        return self.__CurrentWorkflowID

    @CurrentWorkflowID.setter
    def CurrentWorkflowID(self, v):
        assert v is not None, "CurrentWorkflowID must not be None"
        assert isinstance(v, int), "Parameter (type {}) must be of 'int' type".format(v.__class__.__name__)
        #if (len(v) == 0): raise ValueError("CurrentWorkflowID cannot be an empty String")
        self.__CurrentWorkflowID = v
    
    @property
    def ExpectedResponsePath(self):
        return self.__ExpectedResponsePath

    @ExpectedResponsePath.setter
    def ExpectedResponsePath(self, v):
        assert v is not None, "ExpectedResponsePath must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        #if (len(v) == 0): raise ValueError("ExpectedResponsePath cannot be an empty String")
        self.__ExpectedResponsePath = v
    
    @property
    def Tables(self):
        return self.__Tables
    
    @Tables.setter
    def Tables(self, v):
        assert v is not None, "Tables must not be None"
        assert isinstance(v, list), "ColumnDescriptions must be List"
        assert all((isinstance(c, ResponseTable) or (isinstance(c, ConnectionTable))) for c in v), "'ResponseTable' and 'ConnectionTable' are the only allowed type of list elements"
        self.__Tables = v
        
    def addTable(self, v):
        assert v is not None, "Table must not be None"
        assert isinstance(v, ResponseTable) or isinstance(v, ConnectionTable), "Parameter (type {})  must be of 'ArgTable' or 'ConnectionTable' type".format(v.__class__.__name__)
        self.Tables.append(v)
    
    def toJsonString(self):
        k = json.dumps( self, indent=4, sort_keys=True, default=NodeResponse.toDict )
        return k

    @classmethod
    def fromJsonString(cls, jsonStr):
        assert isinstance(jsonStr, six.string_types), "Parameter (type {}) must be of 'String' type".format(jsonStr.__class__.__name__)
        if (len(jsonStr) == 0): raise ValueError("JSON string cannot be an empty String")
        
        nodeResponse = json.loads(jsonStr, cls=NodeResponseDecoder)
        return nodeResponse
        
    @classmethod
    def fromFile(cls, v):
        if (sys.version_info > (3, 0)):
            if v.__class__.__name__ == 'TextIOWrapper' :
                nodeResponse = cls.fromDict(json.load(v, cls=NodeResponseDecoder))
                return nodeResponse
        else:
            if v.__class__.__name__ == 'file' :
                nodeResponse = cls.fromDict(json.load(v, cls=NodeResponseDecoder))
                return nodeResponse

        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("File name cannot be an empty String")
        with open(v, 'rt') as f:
            nodeResponse = cls.fromFile(f)
        f.close()
        return nodeResponse
      
    @classmethod
    def fromDict(cls, dct):
        if (dct.__class__.__name__ == 'NodeResponse'):
            return dct
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        nodeResponse = NodeResponse() 
        if 'CurrentWorkflowID' in dct:
            nodeResponse.CurrentWorkflowID = dct['CurrentWorkflowID']
        if 'ExpectedResponsePath' in dct:
            nodeResponse.ExpectedResponsePath = dct['ExpectedResponsePath']
        if 'Tables' in dct:
            for c in dct['Tables']:
                nodeResponse.addTable(c)
        return nodeResponse
        
    @classmethod
    def toDict(cls, obj):
        # print 'NodeResponse.toDict: parameter type is {}'.format(obj.__class__.__name__)
        if (obj.__class__.__name__ == 'NodeResponse'):
            d = {}
            if hasattr(obj, 'CurrentWorkflowID'):
                d['CurrentWorkflowID'] = obj.CurrentWorkflowID
            if hasattr(obj, 'ExpectedResponsePath'):
                d['ExpectedResponsePath'] = obj.ExpectedResponsePath
            if hasattr(obj, 'Tables') and (obj.Tables is not None) and (len(obj.Tables) > 0):
                d['Tables'] = obj.Tables
            return d
        if (obj.__class__.__name__ in [ 'ResponseTable', 'ResponseTableColumnDescription', 'ResponseColumnOptions' ]):
            return ResponseTable.toDict(obj)
        if (obj.__class__.__name__ in [ 'ConnectionTable', 'ConnectionTableOptions', 'ConnectionTableColumnDescription' ]):
            return ConnectionTable.toDict(obj)
        raise TypeError("Parameter is of invalid type {}".format(obj.__class__.__name__))
    
    def toFile(self, v):
        if (sys.version_info > (3, 0)):
            if v.__class__.__name__ == 'TextIOWrapper' :
                json.dump( self, v, indent=4, default=NodeResponse.toDict )
                return
        else:
            if v.__class__.__name__ == 'file' :
                json.dump( self, v, indent=4, default=NodeResponse.toDict )
                return

        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("File name cannot be an empty String")
    
        with open(v, 'wt') as f:
            self.toFile(f)
        f.close()

    
    
class Table(object):
    """ A class that represents a table 
    
    JSON (example):
    
    {
      "TableName": "Proteins",
      "DataFile": "C:/ProgramData/Thermo/Proteome Discoverer 2.4/Scratch/Job73/Script(16)/TargetProtein.txt",
      "DataFormat": "CSV",
      "ColumnDescriptions": [
        ... - items of the ColumnDescription type
      ]
    },

   
    Attributes
    ----------
    TableName : str
        table name
    DataFile : str
        full file name with table data
    DataFormat : str
        table data format
    ColumnDescriptions : list
        list of column descriptions
        
    Methods
    -------
    addColumnDescription(columnDescription)
        Adds provided columnDescription to the list of column descriptions
        
    fromDict(dct) -> (Table, ColumnDescriptor, Options)
        factory method that creates an instance based on the passed-in dict
    
    toDict(obj) -> dict
        creates a dict representation of a passes-in instance
        it invokes namesake methods for child classes
    """
    
    # The coding pattern:
    #
    # self.<attribute-name> = ... in __init__ accompanied by
    #
    # @property
    # def <attribute-name>(self): 
    #     return self.__<attribute-name>
    # @<attribute-name>.setter
    # def <attribute-name>(self, v):
    #     self.__<attribute-name> = v
    #
    # is explained at https://www.python-course.eu/python3_properties.php
    
    def __init__(self, name, dataFile, dataFormat):
        self.ColumnDescriptions = []
        self.TableName = name
        self.DataFile = dataFile
        self.DataFormat = dataFormat

    @classmethod
    def isIt(cls, dct):
        if (('TableName' in dct) 
        and ('DataFile' in dct) 
        and ('DataFormat' in dct) 
        and ('-' not in dct['TableName'])):
            return True
        return False

    @property
    def TableName(self):
        return self.__TableName

    @TableName.setter
    def TableName(self, v):
        assert v is not None, "TableName must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("TableName cannot be an empty String")
        self.__TableName = v
    
    @property
    def DataFile(self):
        return self.__DataFile

    @DataFile.setter
    def DataFile(self, v):
        assert v is not None, "DataFile must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("DataFile cannot be an empty String")
        self.__DataFile = v
    
    @property
    def DataFormat(self):
        return self.__DataFormat

    @DataFormat.setter
    def DataFormat(self, v):
        assert v is not None, "DataFormat must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("DataFormat cannot be an empty String")
        self.__DataFormat = v
    
    @property
    def ColumnDescriptions(self):
        return self.__ColumnDescriptions
    
    @ColumnDescriptions.setter
    def ColumnDescriptions(self, v):
        assert v is not None, "ColumnDescriptions must not be None"
        assert isinstance(v, list), "ColumnDescriptions must be List"
        assert all(isinstance(c, ColumnDescription) for c in v), "The 'ColumnDescription' must be the type of all list elements"
        self.__ColumnDescriptions = v
        
    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        # print 'Table.fromDict dict is {}'.format(dct)
        table = Table(dct['TableName'], dct['DataFile'], dct['DataFormat'])
        for c in dct['ColumnDescriptions']:
            # print 'Table.fromDict ColumnDescriptions list element is of type {}'.format(c.__class__.__name__)
            table.addColumnDescription(c)
        return table
        
    @classmethod
    def toDict(cls, obj):
        # print 'Table.toDict: parameter type is {}'.format(obj.__class__.__name__)
        if (obj.__class__.__name__ == 'Table'):
            d = {}
            d['TableName'] = obj.TableName
            d['DataFile'] = obj.DataFile
            d['DataFormat'] = obj.DataFormat
            if hasattr(obj, 'ColumnDescriptions') and (obj.ColumnDescriptions is not None) and (len(obj.ColumnDescriptions) > 0):
                d['ColumnDescriptions'] = obj.ColumnDescriptions
            return d
        if (obj.__class__.__name__ == 'ColumnDescription'):
            return ColumnDescription.toDict(obj)
        if (obj.__class__.__name__ == 'ColumnOptions'):
            return ColumnOptions.toDict(obj)
        raise TypeError("Parameter is of invalid type {}".format(obj.__class__.__name__))
    
class ArgTable(Table):
    """ A class that represents a node_args table 
    
    JSON (example):
    
    {
      "TableName": "Proteins",
      "DataFile": "C:/ProgramData/Thermo/Proteome Discoverer 2.4/Scratch/Job73/Script(16)/TargetProtein.txt",
      "DataFormat": "CSV",
      "ColumnDescriptions": [
        ... - items of the ColumnDescription type
      ]
    },
    """
    def __init__(self, name, dataFile, dataFormat):
        super(ArgTable, self).__init__(name, dataFile, dataFormat)

    def addColumnDescription(self, v):
        assert v is not None, "ColumnDescription must not be None"
        assert isinstance(v, ColumnDescription), "Parameter (type {}) must be of 'ColumnDescription' type".format(v.__class__.__name__)
        self.ColumnDescriptions.append(v)
    
    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        table = ArgTable(dct['TableName'], dct['DataFile'], dct['DataFormat'])
        for c in dct['ColumnDescriptions']:
            table.addColumnDescription(c)
        return table
        
    @classmethod
    def toDict(cls, obj):
        # print 'ArgTable.toDict: parameter type is {}'.format(obj.__class__.__name__)
        if (obj.__class__.__name__ == 'ArgTable'):
            d = {}
            d['TableName'] = obj.TableName
            d['DataFile'] = obj.DataFile
            d['DataFormat'] = obj.DataFormat
            if hasattr(obj, 'ColumnDescriptions') and (obj.ColumnDescriptions is not None) and (len(obj.ColumnDescriptions) > 0):
                d['ColumnDescriptions'] = obj.ColumnDescriptions
            return d
        if (obj.__class__.__name__ == 'ColumnDescription'):
            return ColumnDescription.toDict(obj)
        if (obj.__class__.__name__ == 'ColumnOptions'):
            return ColumnOptions.toDict(obj)
        raise TypeError("Parameter is of invalid type {}".format(obj.__class__.__name__))
    
class ResponseTable(Table):
    """ A class that represents a response_node table 
    
    JSON (example):
    
    {
      "TableName": "Proteins",
      "DataFile": "C:/ProgramData/Thermo/Proteome Discoverer 2.4/Scratch/Job73/Script(16)/TargetProtein.txt",
      "DataFormat": "CSV",
      "ColumnDescriptions": [
        ... - items of the ResponseTableColumnDescription type
      ]
    },
    """
    def __init__(self, name, dataFile, dataFormat):
        super(ResponseTable, self).__init__(name, dataFile, dataFormat)

    def addColumnDescription(self, v):
        assert v is not None, "ResponseTableColumnDescription must not be None"
        assert isinstance(v, ResponseTableColumnDescription), "Parameter (type {}) must be of 'ResponseTableColumnDescription' type".format(v.__class__.__name__)
        self.ColumnDescriptions.append(v)
    
    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        table = ResponseTable(dct['TableName'], dct['DataFile'], dct['DataFormat'])
        for c in dct['ColumnDescriptions']:
            table.addColumnDescription(c)
        return table
        
    @classmethod
    def toDict(cls, obj):
        # print 'ResponseTable.toDict: parameter type is {}'.format(obj.__class__.__name__)
        if (obj.__class__.__name__ == 'ResponseTable'):
            d = {}
            d['TableName'] = obj.TableName
            d['DataFile'] = obj.DataFile
            d['DataFormat'] = obj.DataFormat
            if hasattr(obj, 'ColumnDescriptions') and (obj.ColumnDescriptions is not None) and (len(obj.ColumnDescriptions) > 0):
                d['ColumnDescriptions'] = obj.ColumnDescriptions
            return d
        if (obj.__class__.__name__ == 'ResponseTableColumnDescription'):
            return ResponseTableColumnDescription.toDict(obj)
        if (obj.__class__.__name__ == 'ResponseColumnOptions'):
            return ResponseColumnOptions.toDict(obj)
        raise TypeError("Parameter is of invalid type {}".format(obj.__class__.__name__))
    
class ConnectionTable(Table):
    """ A class that represents a connection table 
    
    JSON (example):
    
    {
      "TableName": "ProteinStartsWith-TargetProteins",
      "DataFile": "C:/ProgramData/Thermo/Proteome Discoverer 2.4/Scratch/Job113/Script(16)/ProteinStartsWith-TargetProtein.txt",
      "DataFormat": "CSVConnectionTable",
      "ColumnDescriptions": [
        ... - items of the ConnectionTableColumnDescription type
      ]
    },

   
    """
    def __init__(self, name, dataFile, dataFormat):
        super(ConnectionTable, self).__init__(name, dataFile, dataFormat)
    
    @property
    def TableName(self):
        return self.__TableName

    @TableName.setter
    def TableName(self, v):
        assert v is not None, "TableName must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("TableName cannot be an empty String")
        assert '-' in v, "TableName of a connection table must have '-'"
        self.__TableName = v
    
    @classmethod
    def isIt(cls, dct):
        if (('TableName' in dct) 
        and ('DataFile' in dct) 
        and ('DataFormat' in dct) 
        and ('-' in dct['TableName'])):
            return True
        return False

    @property
    def Options(self):
        return self.__Options

    @Options.setter
    def Options(self, v):
        assert v is not None, "ConnectionTableOptions must not be None"
        assert isinstance(v, ConnectionTableOptions), "Parameter (type {}) must be of type 'ConnectionTableOptions'".format(v.__class__.__name__)
        self.__Options = v

    @property
    def ColumnDescriptions(self):
        return self.__ColumnDescriptions
    
    @ColumnDescriptions.setter
    def ColumnDescriptions(self, v):
        assert v is not None, "ColumnDescriptions must not be None"
        assert isinstance(v, list), "ColumnDescriptions must be List"
        assert all(isinstance(c, ConnectionTableColumnDescription) for c in v), "The 'ConnectionTableColumnDescription' must be the type of all list elements"
        self.__ColumnDescriptions = v
        
    def addColumnDescription(self, v):
        assert v is not None, "ColumnDescription must not be None"
        if isinstance(v, ColumnDescription) or isinstance(v, ResponseTableColumnDescription):
            connectionTableColumnDescription = ConnectionTableColumnDescription(v.ColumnName, v.ID, v.DataType)
            if hasattr(v, 'Options'):
                connectionTableColumnDescription.Options = v.Options
            self.ColumnDescriptions.append(connectionTableColumnDescription)
            return
        if not isinstance(v, ConnectionTableColumnDescription): raise TypeError("Parameter (type {}) must be of 'ConnectionTableColumnDescription' type".format(v.__class__.__name__))
        self.ColumnDescriptions.append(v)
    
    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        table = ConnectionTable(dct['TableName'], dct['DataFile'], dct['DataFormat'])
        if 'Options' in dct:
            # print 'ConnectionTable.fromDict: dct is {}, Options in it are {}'.format(dct, vars(dct['Options']))
            table.Options = dct['Options']
        for c in dct['ColumnDescriptions']:
            table.addColumnDescription(c)
        return table
        
    @classmethod
    def toDict(cls, obj):
        # print 'ConnectionTable.toDict: parameter type is {} as dict {}'.format(obj.__class__.__name__, vars(obj))
        if (obj.__class__.__name__ == 'ConnectionTable'):
            d = {}
            d['TableName'] = obj.TableName
            d['DataFile'] = obj.DataFile
            d['DataFormat'] = obj.DataFormat
            # print 'ConnectionTable.toDict: parameter type is {}, Options are {}'.format(obj.__class__.__name__, vars(obj.Options))
            if hasattr(obj, 'Options') and (obj.Options is not None) and (isinstance(obj.Options, ConnectionTableOptions)):
                d['Options'] = ConnectionTableOptions.toDict(obj.Options)
            if hasattr(obj, 'ColumnDescriptions') and (obj.ColumnDescriptions is not None) and (len(obj.ColumnDescriptions) > 0):
                d['ColumnDescriptions'] = obj.ColumnDescriptions
            return d
        if (obj.__class__.__name__ == 'ConnectionTableOptions'):
            return ConnectionTableOptions.toDict(obj)
        if (obj.__class__.__name__ == 'ConnectionTableColumnDescription'):
            return ConnectionTableColumnDescription.toDict(obj)
        raise TypeError("Parameter is of invalid type {}".format(obj.__class__.__name__))
    
class AnyColumnDescription(object):
    """ A class that represents a table column 
    
    Attributes
    ----------
    ColumnName : str
        column name
    ID : str
        possible values are "", "ID' "WorkflowID", "Other"
    DataType : str
        kind of data this column holds
        
    Methods
    -------        
    fromDict(dct) -> AnyColumnDescription
        factory method that creates an instance based on the passed-in dict
    
    toDict(obj)b -> dict
        creates a dict representation of a passes-in instance
        it invokes namesake methods for child classes
    """
    
    def __init__(self, columnName, iD, dataType):
        self.ColumnName = columnName
        self.ID = iD
        self.DataType = dataType

    @classmethod
    def isIt(cls, dct):
        if (('ColumnName' in dct) 
        and ('ID' in dct)):
            return True
        return False

    @property
    def ColumnName(self):
        return self.__ColumnName

    @ColumnName.setter
    def ColumnName(self, v):
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("ColumnName cannot be an empty String")
        self.__ColumnName = v
    
    @property
    def ID(self):
        return self.__ID

    @ID.setter
    def ID(self, v):
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if not (v in ['', 'ID', 'WorkflowID', 'Other']): raise ValueError("invalid ID {}".format(v))
        self.__ID = v

    @property
    def DataType(self):
        return self.__DataType

    @DataType.setter
    def DataType(self, v):
        assert v is not None, "DataType must not be None"
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("DataType cannot be an empty String")
        if not (v in ['Boolean', 'Int', 'Long', 'Float', 'String']): raise ValueError("invalid DataType {}".format(v))
        self.__DataType = v
        
class ConnectionTableColumnDescription(AnyColumnDescription):
    """ A class that represents a connection table column 
    
    Attributes
    ----------
    ID : str
        possible values are "ID' "WorkflowID", "Other"

    """
    def __init__(self, columnName, iD, dataType):
        self.Options = None
        
        # NOTE
        # connection table between peptide Groups and modification sites
        # contains a column 'site status' that does not have an id in the
        # automatically generated node_args.json file
        #
        # not sure why
        #
        # This causes an exception in the ID setter function
        # manually overwrite this here for the moment
        
        if columnName == 'Site Status' and dataType == 'String' and iD == '':
            iD = 'Other'
            
        super(ConnectionTableColumnDescription, self).__init__(columnName, iD, dataType)
    
    @classmethod
    def isIt(cls, dct):
        if super(ConnectionTableColumnDescription, cls).isIt(dct):
            if 'Options' in dct:
                return False
            if dct['ID'] not in ['ID', 'WorkflowID', 'Other']:
                return False
            return True
        return False

    @property
    def ID(self):
        return self.__ID

    @ID.setter      # overwritten to disallow an empty ID
    def ID(self, v):
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if not (v in ['ID', 'WorkflowID', 'Other']): raise ValueError("invalid ID {}".format(v))
        self.__ID = v

    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        columnDescription = ConnectionTableColumnDescription(dct['ColumnName'], dct['ID'], dct['DataType'])
        return columnDescription
        
    @classmethod
    def toDict(cls, obj):
        # print 'ConnectionTableColumnDescription.toDict: parameter type is {}'.format(obj.__class__.__name__)
        if (obj.__class__.__name__ in [ 'ConnectionTableColumnDescription', 'ColumnDescription' ]):
            d = {}
            d['ColumnName'] = obj.ColumnName
            d['ID'] = obj.ID
            d['DataType'] = obj.DataType
            return d    
        raise TypeError("Parameter is of invalid type {}".format(obj.__class__.__name__))

class ColumnDescription(AnyColumnDescription):
    """ A class that represents an arg table column 
    
    Attributes
    ----------
    Options : ColumnOptions
        column options (the DataGroupName only) - optional
        
    Methods
    -------        
    fromDict(dct) -> ColumnDescription
        factory method that creates an instance based on the passed-in dict
    
    toDict(obj)b -> dict
        creates a dict representation of a passes-in instance
        it invokes namesake methods for child classes
    """
    def __init__(self, columnName, iD, dataType):
        self.Options = None
        super(ColumnDescription, self).__init__(columnName, iD, dataType)

    @property
    def Options(self):
        return self.__Options

    @Options.setter
    def Options(self, v):
        if v is None: return
        assert isinstance(v, ColumnOptions), "Parameter (type {}) must be of type 'ColumnOptions'".format(v.__class__.__name__)
        self.__Options = v

    
    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        # print 'ColumnDescription.fromDict: parameter {}'.format(dct)
        columnDescription = ColumnDescription(dct['ColumnName'], dct['ID'], dct['DataType'])
        if 'Options' in dct:
            # print 'ColumnDescription.fromDict: Options {}'.format(dct['Options'])
            if dct['Options'].__class__.__name__ == 'dict':
                columnDescription.Options = ColumnOptions.fromDict(dct['Options'])
            else:
                columnDescription.Options = dct['Options']
        # print 'ColumnDescription.fromDict: returning dict {}'.format(vars(columnDescription))
        return columnDescription
        
    @classmethod
    def toDict(cls, obj):
        # print 'ColumnDescription.toDict: parameter type is {}, as dict {}'.format(obj.__class__.__name__, vars(obj))
        if (obj.__class__.__name__ == 'ColumnDescription'):
            d = {}
            d['ColumnName'] = obj.ColumnName
            d['ID'] = obj.ID
            d['DataType'] = obj.DataType
            if hasattr(obj, 'Options') and (obj.Options is not None) and (isinstance(obj.Options, ColumnOptions)):
                # print 'ColumnDescription.toDict: Options type is {}, as dict {}'.format(obj.Options.__class__.__name__, vars(obj.Options))
                d['Options'] = ColumnOptions.toDict(obj.Options)
            # print 'ColumnDescription.toDict: returning dict {}'.format(d)
            return d    
        if (obj.__class__.__name__ == 'ColumnOptions'):
            d = ColumnOptions.toDict(obj)
            # print 'ColumnDescription.toDict: returning (type {}) {}'.format(d,__class__.__name__, d)
            return d
        raise TypeError("Parameter is of invalid type {}".format(obj.__class__.__name__))

class ResponseTableColumnDescription(AnyColumnDescription):
    """ A class that represents a response table column 
    
    Attributes
    ----------
    Options : ResponseColumnOptions
        column options - optional
        
    Methods
    -------        
    fromDict(dct) -> ResponseTableColumnDescription
        factory method that creates an instance based on the passed-in dict
    
    toDict(obj)b -> dict
        creates a dict representation of a passes-in instance
        it invokes namesake methods for child classes
    """
    def __init__(self, columnName, iD, dataType):
        self.Options = None
        super(ResponseTableColumnDescription, self).__init__(columnName, iD, dataType)

    @property
    def Options(self):
        return self.__Options

    @Options.setter
    def Options(self, v):
        if v is None: return
        assert isinstance(v, ResponseColumnOptions), "Parameter (type {}) must be of type 'ResponseColumnOptions'".format(v.__class__.__name__)
        self.__Options = v

    
    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        columnDescription = ResponseTableColumnDescription(dct['ColumnName'], dct['ID'], dct['DataType'])
        if 'Options' in dct:
            if dct['Options'].__class__.__name__ == 'dict':
                columnDescription.Options = ResponseColumnOptions.fromDict(dct['Options'])
            else:
                columnDescription.Options = dct['Options'] 
        return columnDescription
        
    @classmethod
    def toDict(cls, obj):
        # print 'ResponseTableColumnDescription.toDict: parameter type is {}'.format(obj.__class__.__name__)
        assert obj.__class__.__name__ == 'ResponseTableColumnDescription', "Parameter is of invalid type {}".format(obj.__class__.__name__)
        d = {}
        d['ColumnName'] = obj.ColumnName
        d['ID'] = obj.ID
        d['DataType'] = obj.DataType
        if hasattr(obj, 'Options') and (obj.Options is not None) and isinstance(obj.Options, ResponseColumnOptions):
            d['Options'] = ResponseColumnOptions.toDict(obj.Options)
        return d    
    
class ColumnOptions(object):
    """ A class that represents column options 
    
    Attributes
    ----------
    DataGroupName : str
        group name to which this column belongs
    
    Methods
    -------        
    fromDict(dct) -> ColumnOptions
        factory method that creates an instance based on the passed-in dict
    
    toDict(obj) -> dict
        creates a dict representation of a passes-in instance
        it does not invoke namesake methods for child classes since this class has no children
    -------
    """
    def __init__(self):
        self.DataGroupName = None
    
    @classmethod
    def isIt(cls, dct):
        if (('DataGroupName' in dct) and  (len(dct) == 1)):
            return True
        return False

    @property
    def DataGroupName(self):
        return self.__DataGroupName

    @DataGroupName.setter
    def DataGroupName(self, v):
        if v is None: return
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("DataGroupName cannot be an empty String")
        self.__DataGroupName = v

    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        # print 'ColumnOptions.fromDict parameter is of type {} is {}'.format(dct.__class__.__name__, dct)
        if (dct.__class__.__name__ == 'dict'):
            Options = ColumnOptions()
            if 'DataGroupName' in dct: Options.DataGroupName = dct['DataGroupName']
            # print 'ColumnOptions.fromDict returning {}'.format(Options)
            return Options
        
    @classmethod
    def toDict(cls, obj):
        # print 'ColumnOptions.toDict: parameter type is {}, as dict {}'.format(obj.__class__.__name__, vars(obj))
        assert obj.__class__.__name__ == 'ColumnOptions', "Parameter is of invalid type {}".format(obj.__class__.__name__)
        d = {}
        if hasattr(obj, 'DataGroupName') and (len(vars(obj)) == 1) and (obj.DataGroupName is not None):
            # print 'ColumnOptions.toDict: setting DataGroupName to {}'.format(obj.DataGroupName)
            d['DataGroupName'] = obj.DataGroupName    
        return d
    
class ResponseColumnOptions(ColumnOptions):
    """ A class that represents response table column options 
    
    Attributes
    ----------
    PositionAfter : str
        The new column is tried to be created right of the column given by the value
    PositionBefore : str
        The new column is tried to be created left of the column given by the value
    RelativePosition : int
        The value is an integer value that specifies the relative position.
    PlotType : str
        Specifies the plot type used to define whether the column can be plotted in a chart
        Valid values are "Numeric", "Categorical", "Ordinal", and each combination of them separated with comma, e.g. "Numeric, Categorical"
        If not defined, Boolean columns are categorical, numeric columns are "Numeric, Ordinal", all others are "None".
    FormatString : str
        Specifies how numerical values are formatted and displayed. 
        By default, float values have a format string of "F5", if not specified, i.e. they are displayed with a precision of 5.
    SpecialCellRenderer : str
        The data of the new column is shown with a special rendering rather than as a raw data value. 
        There are the following data renderers available:
            exclamationMark - 90550C2D-EB8D-443E-9F23-9E735FB23F9A
                displays a string column. It shows an error icon if the value is not empty. The tool tip for the image is the the full text.
            boolCheckMark - 330D9522-50CC-41B7-9D45-5E5D8F708103
                displays a Boolean value. It shows a green check mark if the value is true.
            boolCrossMark - 4B8956F1-3A54-423D-8654-60676825230F
                displays a Boolean value. It shows a check mark (X) if the value is true.
            boolYesNo - 9085D14E-388D-4EF0-91C1-B4B2BDF33AD3
                displays a Boolean value with the words "Yes" and "No".
            fileName - EB29D794-4F2E-4785-8B80-A24D8C0FB3E4
                for string column. Displays a filename (a string) by only showing the filename in the table field and showing the full path in the tooltip.
            fileSize - FBBFBB0B-A2D0-468F-95BF-25BCD0A42FE9
                displays an integer number as a filesize.
            percentBar - 64516B23-565C-4036-87DA-29189E9E62A3
                displays a number between 0 and 100 as a column between 0% and 100%.
            percentBarWithNumber - CEB81A87-6652-4625-BD2C-520DB9858F00
                displays a number between 0 and 100 as a column between 0% and 100% and also included the number itself.
            monospaced - 59E4C754-AD43-42FD-B4D9-C8CF0F622BD3
                displays any number or text using a monospaced font rather than a proportional font.
            concatenatedMultiline - 410B767F-0C21-4E97-BB3D-041186955807
                displays a text that consists of multiple lines as one line that features the multiple lines concatenated using a ;

         

    Methods
    -------        
    fromDict(dct) -> Options
        factory method that creates an instance based on the passed-in dict
    
    toDict(obj) -> dict
        creates a dict representation of a passes-in instance
        it does not invoke namesake methods for child classes since this class has no children
    -------
    """
    def __init__(self):
        self.PositionBefore = None
        self.PositionAfter = None
        self.RelativePosition = None
        self.PlotType = None
        self.FormatString = None
        self.SpecialCellRenderer = None
        super(ResponseColumnOptions, self).__init__()
        
    @classmethod
    def isIt(cls, dct):
        if (('PositionBefore' in dct) 
        or ('PositionAfter' in dct)
        or ('RelativePosition' in dct)
        or ('PlotType' in dct)
        or ('FormatString' in dct)
        or ('SpecialCellRenderer' in dct)
        or (ColumnOptions.isIt(dct))):
            return True
        return False

    @property
    def RelativePosition(self):
        return self.__RelativePosition

    @RelativePosition.setter
    def RelativePosition(self, v):
        if v is None: return
        assert isinstance(v, int), "Parameter (type {}) must be of 'int' type".format(v.__class__.__name__)
        self.__RelativePosition = v
    
    @property
    def PlotType(self):
        return self.__PlotType

    @PlotType.setter
    def PlotType(self, v):
        if v is None: return
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("PlotType cannot be an empty String")
        self.__PlotType = v
    
    @property
    def FormatString(self):
        return self.__FormatString

    @FormatString.setter
    def FormatString(self, v):
        if v is None: return
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("FormatString cannot be an empty String")
        self.__FormatString = v
    
    @property
    def SpecialCellRenderer(self):
        return self.__SpecialCellRenderer

    @SpecialCellRenderer.setter
    def SpecialCellRenderer(self, v):
        if v is None: return
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("SpecialCellRenderer cannot be an empty String")
        self.__SpecialCellRenderer = v
    
    @property
    def PositionBefore(self):
        return self.__PositionBefore

    @PositionBefore.setter
    def PositionBefore(self, v):
        if v is None: return
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("PositionBefore cannot be an empty String")
        self.__PositionBefore = v

    @property
    def PositionAfter(self):
        return self.__PositionAfter

    @PositionAfter.setter
    def PositionAfter(self, v):
        if v is None: return
        assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
        if (len(v) == 0): raise ValueError("PositionAfter cannot be an empty String")
        self.__PositionAfter = v

    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        Options = ResponseColumnOptions()
        if 'PositionBefore' in dct: Options.PositionBefore = dct['PositionBefore']
        if 'PositionAfter' in dct: Options.PositionAfter = dct['PositionAfter']
        if 'RelativePosition' in dct: Options.RelativePosition = dct['RelativePosition']
        if 'PlotType' in dct: Options.PlotType = dct['PlotType']
        if 'FormatString' in dct: Options.FormatString = dct['FormatString']
        if 'SpecialCellRenderer' in dct: Options.SpecialCellRenderer = dct['SpecialCellRenderer']
        return Options
        
    @classmethod
    def toDict(cls, obj):
        # print 'ResponseColumnOptions.toDict: parameter type is {}'.format(obj.__class__.__name__)
        assert obj.__class__.__name__ == 'ResponseColumnOptions', "Parameter is of invalid type {}".format(obj.__class__.__name__)
        d = {}
        if hasattr(obj, 'PositionBefore') and (obj.PositionBefore is not None): d['PositionBefore'] = obj.PositionBefore    
        if hasattr(obj, 'PositionAfter') and (obj.PositionAfter is not None): d['PositionAfter'] = obj.PositionAfter    
        if hasattr(obj, 'RelativePosition') and (obj.RelativePosition is not None): d['RelativePosition'] = obj.RelativePosition    
        if hasattr(obj, 'PlotType') and (obj.PlotType is not None): d['PlotType'] = obj.PlotType    
        if hasattr(obj, 'FormatString') and (obj.FormatString is not None): d['FormatString'] = obj.FormatString    
        if hasattr(obj, 'SpecialCellRenderer') and (obj.SpecialCellRenderer is not None): d['SpecialCellRenderer'] = obj.SpecialCellRenderer    
        return d
    
class ConnectionTableOptions:
    """ A class that represents connection table options 
    
    Attributes
    ----------
    FirstTable : str
        name of a first (source) table
    SecondTable : str
        name of the second (destination) table
    
    Methods
    -------        
    fromDict(dct) -> ConnectionTableOptions
        factory method that creates an instance based on the passed-in dict
    
    toDict(obj) -> dict
        creates a dict representation of a passes-in instance
        it does not invoke namesake methods for child classes since this class has no children
    -------
    """
    def __init__(self):
        self.FirstTable = None
        self.SecondTable = None
    
    @classmethod
    def isIt(cls, dct):
        if (('FirstTable' in dct) or ('SecondTable' in dct)):
            return True
        return False

    @property
    def FirstTable(self):
        return self.__FirstTable

    @FirstTable.setter
    def FirstTable(self, v):
        if not (v is None) :
            assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
            if (len(v) == 0): raise ValueError("FirstTable cannot be an empty String")
        self.__FirstTable = v

    @property
    def SecondTable(self):
        return self.__SecondTable

    @SecondTable.setter
    def SecondTable(self, v):
        if not (v is None) :
            assert isinstance(v, six.string_types), "Parameter (type {}) must be of 'String' type".format(v.__class__.__name__)
            if (len(v) == 0): raise ValueError("SecondTable cannot be an empty String")
        self.__SecondTable = v

    @classmethod
    def fromDict(cls, dct):
        assert dct.__class__.__name__ == 'dict', "Parameter is of invalid (not dict) type {}".format(dct.__class__.__name__)
        Options = ConnectionTableOptions()
        if 'FirstTable' in dct: Options.FirstTable = dct['FirstTable']
        if 'SecondTable' in dct: Options.SecondTable = dct['SecondTable']
        return Options
        
    @classmethod
    def toDict(cls, obj):
        # print 'ConnectionTableOptions.toDict: parameter type is {}'.format(obj.__class__.__name__)
        assert obj.__class__.__name__ == 'ConnectionTableOptions', "Parameter is of invalid type {}".format(obj.__class__.__name__)
        d = {}
        if hasattr(obj, 'FirstTable') and (obj.FirstTable is not None): d['FirstTable'] = obj.FirstTable    
        if hasattr(obj, 'SecondTable') and (obj.SecondTable is not None): d['SecondTable'] = obj.SecondTable    
        return d
    
class NodeArgsDecoder(json.JSONDecoder):
    """ A class that defines custom JSON encoding 
    
    It allows for decoding JSON that does not have any class info in it.
    This pattern is suggested at https://stackoverflow.com/questions/48991911/how-to-write-a-custom-json-decoder-for-a-complex-object/52154263
    
    Methods
    -------
    """   
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
        
    def object_hook(self, dct):
        """ Dict processsor
        
        The processing is done from the bottom of class hierarchy, i.e. from Options to Table.
        For each layer, the corresponding class fromDict factory method is invoked.
        These factory methods are creating class instances based on pqssed-in dict. 
        """
        # print 'NodeDecoder.object_hook: dict is {}'.format(dct)
        if ConnectionTableOptions.isIt(dct): return ConnectionTableOptions.fromDict(dct)
        if ColumnOptions.isIt(dct): return ColumnOptions.fromDict(dct)
        if ColumnDescription.isIt(dct): return ColumnDescription.fromDict(dct)
        if ConnectionTableColumnDescription.isIt(dct): return ConnectionTableColumnDescription.fromDict(dct)
        if ArgTable.isIt(dct): return ArgTable.fromDict(dct)
        if ConnectionTable.isIt(dct): return ConnectionTable.fromDict(dct)
        if NodeArgs.isIt(dct): return NodeArgs.fromDict(dct)
        return dct
 
class NodeResponseDecoder(json.JSONDecoder):
    """ A class that defines custom JSON encoding 
    
    It allows for decoding JSON that does not have any class info in it.
    This pattern is suggested at https://stackoverflow.com/questions/48991911/how-to-write-a-custom-json-decoder-for-a-complex-object/52154263
    
    Methods
    -------
    """   
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
        
    def object_hook(self, dct):
        """ Dict processsor
        
        The processing is done from the bottom of class hierarchy, i.e. from Options to Table.
        For each layer, the corresponding class fromDict factory method is invoked.
        These factory methods are creating class instances based on pqssed-in dict. 
        """
        # print 'NodeDecoder.object_hook: dict is {}'.format(dct)
        if ConnectionTableOptions.isIt(dct): return ConnectionTableOptions.fromDict(dct)
        if ResponseColumnOptions.isIt(dct): return ResponseColumnOptions.fromDict(dct)
        if ColumnOptions.isIt(dct): return ColumnOptions.fromDict(dct)
        if ResponseTableColumnDescription.isIt(dct): return ResponseTableColumnDescription.fromDict(dct)
        if ColumnDescription.isIt(dct): return ColumnDescription.fromDict(dct)
        if ConnectionTableColumnDescription.isIt(dct): return ConnectionTableColumnDescription.fromDict(dct)
        if ResponseTable.isIt(dct): return ResponseTable.fromDict(dct)
        if ConnectionTable.isIt(dct): return ConnectionTable.fromDict(dct)
        if NodeResponse.isIt(dct): return NodeResponse.fromDict(dct)
        return dct
 
