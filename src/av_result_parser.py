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

import csv
import config_loader

config =config_loader.Config()

# Define all the variables used in this class
# These are all elements from the AV response
RESULT="result"
PLACE_ID="placeId"
GEOCODE="geocode"
LOCATION="location"
USPS_DATA="uspsData"
ADDRESS="address"
FORMATTED_ADDRESS="formattedAddress"
VERDICT="verdict"
POSTAL_ADDRESS="postalAddress"
STANDARDIZED_ADDRESS="standardizedAddress"
METADATA="metadata"
LATITUDE="latitude"
LONGITUDE="longitude"
ADDRESS_COMPONENTS="addressComponents"
CONFIRMATION_LEVEL="confirmationLevel"
COMPONENT_TYPE="componentType"
ADDRESS_LINES="addressLines"

class av_result_parser_class:
    

    def parse_av_response(self, address_validation_result, input):
        """_summary_:                 
             Check to see if result component contains verdict. Verdict contains the overall quality indicators, and should always be stored    
             If running in test mode (run mode 1), allow the application to store some data to understand Address Validation API response     
             Test Mode: 1
             Production mode -Users: 2
             Production mode -NoUsers: 3
             If running in Production mode -No Users, allow the application to store Place ID

        Args:
            address_validation_result (dict): Input of the address validation response in json format

        Returns:
            _type_: _description_
        """

        run_mode=config.run_mode
        
        parsed_result = dict()
        """_summary_:
        Dict to store the parsed result

        Returns:
            _type_: _description_
        """git 
            
        if run_mode == 1:
            """_summary_:
            Most permissive mode. DO NOT USE this mode other than for testing

            Returns:
                _type_: _description_
            """    

            #added a try catch to stop crashing on invalid requests (which happens if an address cant be resolved or bad data)
            try:
                parsed_result[PLACE_ID]=av_result_parser_class.get_place_ID(address_validation_result)
                parsed_result.update(av_result_parser_class.get_latlong(address_validation_result))
                parsed_result[FORMATTED_ADDRESS]=av_result_parser_class.get_formatted_address(address_validation_result)
                parsed_result.update(av_result_parser_class.get_postal_address(address_validation_result))
                parsed_result.update(av_result_parser_class.get_verdict(address_validation_result))         
                parsed_result.update(av_result_parser_class.get_address_type(address_validation_result))            
                parsed_result.update(av_result_parser_class.get_usps_data(address_validation_result))
                parsed_result.update(av_result_parser_class.get_address_components(address_validation_result))

            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                print("Error in getting place ID")
                #removed the raise which was ending execution upon error

        if run_mode == 2:
            """_summary_:
            Optimum flattened mode

            Returns:
                _type_: _description_
            """ 
            try:  
                parsed_result[PLACE_ID]=av_result_parser_class.get_place_ID(address_validation_result)
                parsed_result.update(av_result_parser_class.get_latlong(address_validation_result))
                parsed_result.update(av_result_parser_class.get_verdict(address_validation_result))  
                parsed_result.update(av_result_parser_class.get_address_components(address_validation_result))
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                print("Error in getting place ID")
                #removed the raise which was ending execution upon error

        if run_mode == 3:
            try:
                parsed_result[PLACE_ID]=av_result_parser_class.get_place_ID(address_validation_result)
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                print("Error in getting place ID")
                #removed the raise which was ending execution upon error
        parsed_result['inputAddress'] = input
        print (parsed_result)
        return parsed_result

    def get_address_components(address_validation_result):
        """_summary_:  https://developers.google.com/maps/documentation/address-validation/reference/rest/v1/TopLevel/validateAddress#AddressComponent
            componentType: confirmationLevel && inferred|spellcorrected etc

        Args:
            address_validation_result (dict): Address Validation result as returned
            from the AV API
        """            
    
        address_components_dict=dict()
        try:     
            if "addressComponents" in address_validation_result[RESULT][ADDRESS]:
                address_components=address_validation_result[RESULT][ADDRESS][ADDRESS_COMPONENTS]
               
                for address_component in address_components:
                    component_type=address_component[COMPONENT_TYPE]
                    """_summary_:
                    Store the componentType which contains locality, postal_code, country etc.
                    This is done to flatten the output json and make it smaller
                    """                    
                   
                    address_component_additional_attr=["inferred","spellCorrected","replaced","unexpected"]

                    if  any((match :=item) in address_component_additional_attr for item in address_component):

                        """_summary_:
                        Insert address components in the dict object  and concatinate with
                        attributes from address_component_additional_attr
                        """                         
                        
                        address_components_dict[str(component_type)]=(address_component[CONFIRMATION_LEVEL]+"|"+str(match))
                    else:            
                        address_components_dict[str(component_type)]=address_component[CONFIRMATION_LEVEL]

            return address_components_dict
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error in formatted address")
            raise
        return address_components

    def get_place_ID(address_validation_result):
        """_summary_: Check if response have geocode and placeID and store it in the parsed_result
                    object. Details of PlaceID here: https://developers.google.com/maps/documentation/places/web-service/place-id

        Args:
            address_validation_result (dict): Address Validation result as returned
            from the AV API

        Returns:
            _type_: a dict containing the placeID
        """        
        try:
            if GEOCODE in address_validation_result[RESULT]:
                if PLACE_ID in address_validation_result[RESULT][GEOCODE]:
                    return address_validation_result[RESULT][GEOCODE][PLACE_ID]
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error in getting place ID")
            return "ERROR!!!"
            


    def get_formatted_address(address_validation_result):
        """_summary_: Get the formatted address from the AV response

        Args:
            address_validation_result (dict): Address Validation result as returned
            from the AV API

        Returns:
            _type_: A dict containing the formatted address
        """        
        try: 
            if ADDRESS in address_validation_result[RESULT]:
                   
                #Add the formatted address to the parsed result dict
                if FORMATTED_ADDRESS in address_validation_result[RESULT][ADDRESS]:
                    return address_validation_result[RESULT][ADDRESS][FORMATTED_ADDRESS]
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error in formatted address")
            raise

    def get_verdict(address_validation_result):
        """_summary_: Verdict object as described here:
        https://developers.google.com/maps/documentation/address-validation/reference/rest/v1/TopLevel/validateAddress#verdict
        is extracted from the response.

        Args:
            address_validation_result (dict): Input of the address validation response in json format

        Returns:
            dict: A dict containing the verdict from the Address Validation response
        """        
        try:
            #if VERDICT in address_validation_result:
            verdict_dict = {}
             # Check to see if result component contains verdict. Verdict contains the overall quality indicators, and should always be stored
            print("BEFORE GETTING VERDICT")
            if VERDICT in address_validation_result[RESULT]:
                print("GETTING VERDICT")
                #Loop through the result object and add componens to the parsed result dict 
                for key in address_validation_result[RESULT][VERDICT].keys():
                    verdict_dict[key] = address_validation_result[RESULT][VERDICT][key]
                    #return address_validation_result[RESULT][VERDICT][key]
                return verdict_dict

        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error in extracting verdict object")
            raise


    def get_latlong(address_validation_result):
        """_summary_: Location element contains latlong, plus code, boundaries etc.
        we just want to retireve the lat long and not all elements inside the location element.

        Args:
            address_validation_result (dict): Input of the address validation response in json format
           
        Returns:
            _type_: _description_
        """       
        try:
            latlong_dict={}
            #Init the Lat/Lng values as zero to handle cases where the API doesn't return a result. 
            latlong_dict[LATITUDE] = 0
            latlong_dict[LONGITUDE] = 0
            if GEOCODE in address_validation_result[RESULT]:
                if LOCATION in address_validation_result[RESULT][GEOCODE]:
                    if LATITUDE in address_validation_result[RESULT][GEOCODE][LOCATION]:
                        latlong_dict[LATITUDE] = address_validation_result[RESULT][GEOCODE][LOCATION][LATITUDE]
                    
                    #Get the longitude from geocode
                    if LONGITUDE in address_validation_result[RESULT][GEOCODE][LOCATION]:
                        latlong_dict[LONGITUDE] = address_validation_result[RESULT][GEOCODE][LOCATION][LONGITUDE]
            return latlong_dict
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error getting latitude or longitude")
            raise


    def get_postal_address(address_validation_result):
        """_summary_: Get the detailed postal address fromt the Address Validation result

        Args:
            address_validation_result (dict): Address Validation result as returned
            from the AV API

        Returns:
            _type_: _description_
        """        
        try:
            # Initialize a dict to capture the response
            postal_address=dict()
            # Check to see if the object has been returned as part of the response
            if POSTAL_ADDRESS in address_validation_result[RESULT][ADDRESS]:
                #Loop though the postal address components and add them to the dictionary
                for postal_address_component in address_validation_result[RESULT][ADDRESS][POSTAL_ADDRESS]:
                    #The address lines are returned as a list so we will extract them in a seperate loop
                    if postal_address_component == ADDRESS_LINES:
                        continue
                    postal_address[postal_address_component] = address_validation_result[RESULT][ADDRESS][POSTAL_ADDRESS][postal_address_component]
                
                # Check the address lines have been returned
                if ADDRESS_LINES in address_validation_result[RESULT][ADDRESS][POSTAL_ADDRESS]:
                    addressLines = ""
                    iteration = 0
                    # Loop through the address lines list, and store them as a string with a pipe seperator
                    for address_line in address_validation_result[RESULT][ADDRESS][POSTAL_ADDRESS][ADDRESS_LINES]:
                        if iteration == 0:
                            addressLines = addressLines + address_line
                        else:
                            addressLines = addressLines + "|" + address_line
                        
                    iteration += 1
                    # Add the address lines string to the dictionary
                    postal_address[ADDRESS_LINES] = addressLines

            return postal_address

        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error in formatted address")
            raise

    def get_address_type(address_validation_result):
        """_summary_: Retruns address validation Metadata as described here:
        https://developers.google.com/maps/documentation/address-validation/reference/rest/v1/TopLevel/validateAddress#addressmetadata

        Args:
            address_validation_result (dict): Input of the address validation response in json format

        Returns:
            dict: containing address metadata 
        """        

        address_metadata_data=dict()
        if METADATA in address_validation_result[RESULT]:
            
            print("Retrieving metadata from the USPS dataset")
            for key in address_validation_result[RESULT][METADATA].keys():
                address_metadata_data[key] = address_validation_result[RESULT][METADATA][key]
            
        return address_metadata_data

    def get_usps_data(address_validation_result):
        
        """_summary_ : [USA Only] Store additional addresss metadata from 
                USPS dataset

        Args:
            address_validation_result (dict): Address Validation result as returned
            from the AV API

        Returns:
            _type_: _description_
        """  
        try:
            # Initiate empty dict to store the usps data
            usps_data=dict()
            
            if USPS_DATA in address_validation_result[RESULT]:
                # Check to see if uspsData component exists. This will only exist if the address is based in USA
                 
                for key in address_validation_result[RESULT][USPS_DATA].keys():
                    # [USA Only] Store the postal service standardized address
                     
                    if key == STANDARDIZED_ADDRESS:
                         
                        usps_data = address_validation_result[RESULT][USPS_DATA][STANDARDIZED_ADDRESS]
                        continue
                                               
                    print("uspsData extracted from result is:")      
                    print(usps_data)
            return usps_data      
        
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error in formatted address")
            raise