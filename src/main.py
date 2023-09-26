# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""_summary_:
This is the main class and where the program starts
This class is first going to call the method to load the csv
csv is then parsed and loaded into a shelve object
then another class starts calling the address validation API
get the responses from it and update the shelve object
Final output is generated from the shelve object

Returns:
    _type_: _description_
"""

import glob
import googlemaps
import os
import sys
import time
import config_loader
import shelve
from pathlib import Path
import read_write_addresses
from read_write_addresses import read_write_addressess_class
from av_result_parser import av_result_parser_class
import csv
import json

config = config_loader.Config()

# Create a client of the googleMaps client library
gmaps = googlemaps.Client(key=config.api_key)

av_result_parser_load = av_result_parser_class()

class HighVolumeAVMain: 

    """_summary_: Read the csv file, parse it, construct the addresses. Insert the addresses in the persistant shelve object

    Returns:
        _type_: _description_
    """  
    def read_and_store_addresses():

        try:
            with read_write_addressess_class() as read_write_addressess_load:
                read_write_addressess_load.read_csv_with_addresses()
                return True
        except IndexError as ie:
            print(ie)

    def parse_av_response():
        # This functions checks if the load in the shelve object is accurate or not
        # read_write_addressess_load.test_datastore()

        with shelve.open(config.shelve_db, 'c') as address_datastore:
            # Create progress bar
            total = len(address_datastore)
            bar_length = 50 
            progress = 0
            
            # Call addressvalidation API with the addresses from shelves to validate the addresses
            # After validation store the address back in the shelve store
        
            for key in address_datastore:
                try:
                    #pass address through without the primary key
                    address_validation_result = gmaps.addressvalidation(address_datastore[key])

                    #pass validated address plus the input
                    parsed_response=av_result_parser_load.parse_av_response(address_validation_result, address_datastore[key])
                    
                    #add the primary key for the row
                    parsed_response['primaryKey'] = key
                    address_datastore[key] = parsed_response

                    # Increment progress bar
                    progress += 1
                    percent = 100.0 * int(progress) / total
                    sys.stdout.write('\r')
                    sys.stdout.write("Completed: [{:{}}] {:>3}%"
                                    .format('='*int(percent/(100.0/bar_length)),
                                        bar_length, int(percent)))
                    sys.stdout.write('\r')
                    sys.stdout.flush()
                    time.sleep(0.001)
                except Exception as err:
                    print(err)
                
            return True

    """_summary_:
    open the file in the write mode, read the shelve file, store the content back as CSV
    """
    def create_export_csv():

        with open(config.output_csv, 'w', newline='') as outputCSV:
            csvWriter = csv.writer(outputCSV)
            
            # Get the output headers from the config file
            header = config.output_columns
    
            csvWriter.writerow(header)
            with shelve.open(config.shelve_db) as address_shelve:
                
                for key in address_shelve:
                    # The address going to be inserted in the cs
                    data = []

                    print(address_shelve[key].keys())

                    print(len(header))

                    for col in header:
                        print(col)
                    # Grab the input address
                    for col in header:
                        if col in address_shelve[key]:
                            data.append(address_shelve[key][col])
                        else:
                            # If not, write a blank cell
                            data.append('')
                            
                    # Write a row to the csv file
                    csvWriter.writerow(data)
                    
    """_summary_:
    Open the file in the write mode
    Read the shelve file
    Store the content back as JSON
    """
    def create_export_json():
        #THIS DOESNT WORK DONT USE 
        with open(config.output_csv, 'w') as output_csv:
            csvWriter = csv.writer(output_csv)
        #  
        # Write the CSV headers to the file
        # header = ['inputAddress', 'inputGranularity', 'validationGranularity', 'geocodeGranularity', 'addressComplete', 'hasUnconfirmedComponents', 'hasInferredComponents', 'hasReplacedComponents', 'placeId', 'spellCorrected']
        # csvWriter.writerow(header)
        #
        with shelve.open(config.shelve_db) as address_shelve:
                
            outputJson=json.dumps(dict(address_shelve), indent=4 )
            csvWriter.writerow(outputJson)

    # Store duplicate addresses, output_csv will process addresses once     
    def print_duplication():
    
        with open('duplicationReport.csv', 'w') as duplication_report:
            
            for key in read_write_addresses.global_duplicate_counter.keys():
                duplication_report.write("%s,%s\n"%(key,read_write_addresses.global_duplicate_counter[key]))

    """_summary_:
    Delete the shelve file after it is done
    By not doing this it creates a bug if this program is run multiple times from same computer
    without changing the shelve file name
    """
    def teardown():
   
        for dbFile in Path(config.directory).glob('*.db'):
            try:
                dbFile.unlink()
                print("Unlinking file "+str(dbFile))
            except OSError as e:
                print("Error while deleting db files: %s : %s" % (dbFile, e.strerror))
                 
#
#  The flow of events:
#  First: Read the addresses and store it in a shelve object
#  Second: Call the address Validation API by reading the addresses from the shelve
#  Third: Create the CSV from data stored in shelve
#  Clean up the project and the files it created
#
try:
    (HighVolumeAVMain.read_and_store_addresses() and HighVolumeAVMain.parse_av_response())
    if config.output_format == "csv":
        HighVolumeAVMain.create_export_csv()

    elif config.output_format == "json":
        HighVolumeAVMain.create_export_json()
    
    HighVolumeAVMain.print_duplication()
    HighVolumeAVMain.teardown()

except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")
    print("Error happened when calling the main functions")
    raise