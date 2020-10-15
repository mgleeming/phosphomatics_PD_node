# -----------------------------------------------------------------------
#  Use Case 2
# -----------------------------------------------------------------------
import sys
import csv
import scriptutils
import traceback

class UC2(object):

    # node_response.json template
    nodeResponseTemplate = '''
    {
         "CurrentWorkflowID": $CWFID$,
         "Tables": [
           {
             "TableName": "Phosphomatics",
             "DataFile": "$PATH$/Phosphomatics.txt",
             "DataFormat": "CSV",
             "Options": {},
             "ColumnDescriptions": [
              {
                 "ColumnName": "Phosphomatics ID",
                 "ID": "ID",
                 "DataType": "Int",
                 "Options": {}
               },
               {
                 "ColumnName": "Accession",
                 "ID": "",
                 "DataType": "String",
                 "Options": {}
               },
               {
                 "ColumnName": "Residue",
                 "ID": "",
                 "DataType": "String",
                 "Options": {}
               },
               {
                 "ColumnName": "Position",
                 "ID": "",
                 "DataType": "Int",
                 "Options": {}
               },$QUANTIFICATION_COLUMNS$
             ]
           },
           {
             "TableName":"Phosphomatics-TargetPeptideGroup",
             "DataFile":"$PATH$/Phosphomatics-TargetPeptideGroup.txt",
             "DataFormat":"CSVConnectionTable",
             "Options":{
                "FirstTable":"Phosphomatics",
                "SecondTable":"Peptide Groups"
             },
             "ColumnDescriptions":[
              {
                "ColumnName":"Phosphomatics ID",
                "ID":"ID",
                "DataType":"Int",
                "Options":{}
              },
              {
                "ColumnName":"Peptide Groups Peptide Group ID",
                "ID":"ID",
                "DataType":"Int",
                "Options":{}
              }
            ]
           }
         ]
    }
    '''

    @classmethod
    def doTables(cls, nodeArgs, nodeResponse, indexDict):
        # get CSV reader for the only table specified in the nodeArgs
        mapFile, mapReader, mapHeader = scriptutils.getTableReader(nodeArgs, indexDict['mapTableIndex'])

        indexDict['pepGroupIDColInMapTable'] = mapHeader.index(
            'Peptide Groups Peptide Group ID')

        indexDict['modSiteIDColInMapTable'] = mapHeader.index(
            'Modification Sites Modification Site ID')

        # open CSV file for the Results table (1st) specified in the nodeResponse for writing
        outResultsTableFileName = nodeResponse.Tables[0].DataFile
        outResultsTableFile = open(outResultsTableFileName, 'w')
        outResultsTableWriter = csv.writer(outResultsTableFile, delimiter='\t', quoting=csv.QUOTE_NONNUMERIC)


        # open CSV file for connection table
        outConnectionTableFileName = nodeResponse.Tables[1].DataFile
        outConnectionTableFile = open(outConnectionTableFileName, 'w')
        outConnectionTableWriter = csv.writer(outConnectionTableFile, delimiter='\t', quoting=csv.QUOTE_NONNUMERIC)

        # write the 1st row (2-column header) to the connection table file
        outConnectionTableHeader = [
            nodeResponse.Tables[1].ColumnDescriptions[0].ColumnName,
            nodeResponse.Tables[1].ColumnDescriptions[1].ColumnName
        ]
        outConnectionTableWriter.writerow(outConnectionTableHeader)

        def getRow(ID, reader, index = 0):
            for row in reader:
                for column in row:
                    column = column.strip().replace('"', '')
                if row[index] == ID:
                    return row
            return

        # write the 1st row (2-column header) to the results table file
        outResultsTableHeader = []
        for columnDescription in nodeResponse.Tables[0].ColumnDescriptions:
            outResultsTableHeader.append(columnDescription.ColumnName)

        #for column in _NodeResponse__Tables
        outResultsTableWriter.writerow(outResultsTableHeader)

        # cycle throw input table rows and build/write out tables' rows
        phosphomaticsID = 1 # initialize unique ID
        for counter, mapRow in enumerate(mapReader):
            # trim and de-quote all input table row values
            for column in mapRow:
                column = column.strip().replace('"', '')

            pepFile, pepReader, pepHeader = scriptutils.getTableReader(
                nodeArgs, indexDict['peptideTableIndex'])
            modFile, modReader, modHeader = scriptutils.getTableReader(
                nodeArgs, indexDict['modSiteTableIndex'])

            if counter == 0:
                indexDict['modNameIndex'] = modHeader.index('Modification Name')
                indexDict['residueIndex'] = modHeader.index('Target Amino Acid')
                indexDict['accessionIndex'] = modHeader.index('Protein Accession')
                indexDict['positionIndex'] = modHeader.index('Position')
                indexDict['modIDColumnIndex'] = modHeader.index('Modification Sites Modification Site ID')

            peptide = getRow(
                mapRow[indexDict['pepGroupIDColInMapTable']], pepReader, index = indexDict['peptideIDColumnIndex'])
            modification = getRow(
                mapRow[indexDict['modSiteIDColInMapTable']], modReader, index = indexDict['modIDColumnIndex'])

            if modification[indexDict['modNameIndex']] != 'Phospho': continue

            outResultsTableRow = ["%s" %phosphomaticsID]

            outResultsTableRow.append(modification[indexDict['accessionIndex']])
            outResultsTableRow.append(modification[indexDict['residueIndex']])
            outResultsTableRow.append(modification[indexDict['positionIndex']])

            outResultsTableRow += [
                peptide[x] for x in indexDict['quantColIndicies']
            ]

            # write output results table row
            outResultsTableWriter.writerow(outResultsTableRow)

            # write entry to connection table
            connectionTableRow = [ "%s" %phosphomaticsID, peptide[indexDict['peptideIDColumnIndex']] ]
            outConnectionTableWriter.writerow(connectionTableRow)

            phosphomaticsID += 1

        # close  both in- and out- files
        outResultsTableFile.close()

        """
        print "uc2.doTables: Resulting \"" + nodeResponse.Tables[0].TableName + "\" table:\n" + open(outResultTableFileName, 'rb').read()
        """

        return

    @classmethod
    def perform(cls, nodeArgsFileName):

        nodeArgs = scriptutils.NodeArgs.fromFile(nodeArgsFileName)

        # get peptide table
        # not sure that these will always be in the same order in node_args

        indexDict = {
            'peptideTableIndex': None,
            'modSiteTableIndex': None,
            'mapTableIndex': None,
            'sequenceIndex' : None,
            'modificationIndex' : None,
            'quantColIndicies' : [],
        }

        for index, table in enumerate(nodeArgs.Tables):
            if isinstance(table, scriptutils.ArgTable) and table.TableName == 'Peptide Groups':
                peptideTable = table
                indexDict['peptideTableIndex'] = index
            if isinstance(table, scriptutils.ArgTable) and table.TableName == 'Modification Sites':
                indexDict['modSiteTableIndex'] = index
            if isinstance(table, scriptutils.ConnectionTable) and table.TableName == 'TargetPeptideGroup-ModificationSite':
                indexDict['mapTableIndex'] = index


        if not peptideTable:
            print('No peptide groups input table found - Exiting...')
            sys.exit()

        peptideTableColumns = peptideTable.ColumnDescriptions

        assert len(peptideTableColumns) > 0, 'No data columns found in peptide groups table'

        # need to dynamicall add new columns to match number of
        # input table abundance figures

        # new column string to add to template
        newColumns = ''

        # teplate for new column definitions
        colTemplate = '''
           {
             "ColumnName": "$COLNAME$",
             "ID": "",
             "DataType": "$COLDTYPE$",
             "Options": {}
           },'''


        for counter, column in enumerate(peptideTableColumns):
            if column._AnyColumnDescription__ColumnName == 'Sequence':
                indexDict['sequenceIndex'] = counter
            if column._AnyColumnDescription__ColumnName == 'Modifications':
                indexDict['modificationIndex'] = counter
            if column._AnyColumnDescription__ColumnName == 'Peptide Groups Peptide Group ID':
                indexDict['peptideIDColumnIndex'] = counter

            colOptions = column._ColumnDescription__Options

            if not hasattr(colOptions, 'DataGroupName'): continue

            if colOptions.DataGroupName == 'Abundances':
                name = column._AnyColumnDescription__ColumnName
                dataType = column._AnyColumnDescription__DataType
                newColumn = colTemplate.replace(
                    '$COLNAME$', name
                ).replace(
                    '$COLDTYPE$',dataType
                )
                newColumns += newColumn
                indexDict['quantColIndicies'].append(counter)


        cls.nodeResponseTemplate = cls.nodeResponseTemplate.replace(
            '$QUANTIFICATION_COLUMNS$', newColumns[0:-1]
        )

        nodeResponse = scriptutils.generateAndStoreNodeResponse(nodeArgs, cls.nodeResponseTemplate)

        cls.doTables(nodeArgs, nodeResponse, indexDict)

        return

if __name__ == "__main__":
    try:
        assert (len(sys.argv) == 2), \
            "Script requires one and only one parameter: full filename of the node_args.json file"

        UC2.perform(sys.argv[1])

    except AssertionError as assertionError:
        print ('uc2: Script failure on assert: ')
        print (assertionError)
    except Exception as exception:
        print ('uc2: Script failure with exception: ')
        print (traceback.format_exc())
    else:
        print ('uc2: Done with the script business.')

