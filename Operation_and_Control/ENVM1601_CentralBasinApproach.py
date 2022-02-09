# -*- coding: utf-8 -*-
"""
@author: ir. J.A. van der Werf (j.a.vanderwerf@tudelft.nl)
"""
import os
import copy

class Central_Basin_Approach():
    """
    This code runs a very basic 'central basin approach', used to assess if
    there is potential for CSO reduction. 
    Note that this is the most basic form of the CBA approach and more 
    accurate versions have been developed
    
    (see van der Werf, Kapelan and Langeveld, 2021:
     https://doi.org/10.1080/1573062X.2021.1943460 )
    
    Note also that this version of the CBA does not consider different
    weights for difference CSOs, which is one of the main drivers of RTC
    potential in this catchment. The code below can be adjusted to include
    this 
    """
    def __init__(self, model_directory=None,
                 model_name=None):
        if model_name == None:
            if model_directory == None:
                mn = [i for i in os.listdir() if '.inp' in i]
                assert len(mn) == 1, ('Zero or Multiple input files found ' +
                                      'in target directory, specify the ' +
                                      'desired inp file')
                self.model_path = mn[0]
            else:
                mn = [i for i in os.listdir(model_directory) if 'inp' in i]
                assert len(mn) == 1, ('Zero or Multiple input files found ' +
                                      'in given target directory,' +
                                      ' specify the desired inp file') 
                self.model_path = model_directory + '\\' + mn[0]
        else:
            if model_directory == None:
                assert os.path.isfile(model_name), ('The given "model_name"' +
                                                    'is not found, ' + 
                                                    'ensure the name contains'+
                                                    ' .inp and exists in ' +
                                                    os.getcwd())
                self.model_path = model_name
            else:
                assert os.path.isfile(model_directory +
                                      '\\' +
                                      model_name), ('The given "model_name"' +
                                                    'is not found, ' + 
                                                    'ensure the name contains'+
                                                    ' .inp and exists in ' +
                                                    model_directory)
                self.model_path = model_directory + '\\' + model_name
                
    def create_CAS_model(self, storage):
        """
        Before running the CAS Model, the simplified model needs to be 
        created. This code makes the single bucket of the system
        

        Parameters
        ----------
        storage : LIST
            A list of the names of the storage nodes in the model with the .

        Returns
        -------
        float
            The total available storage in the system without CSOs occurring.

        """
        if not isinstance(storage, list):
            return AttributeError('storage should be a list of the names' +
                                  'with the depth thresholds')
        if not isinstance(storage[0], list):
            if not isinstance(storage[0], tuple):
                return AttributeError('storage should be a list of lists or',
                                      'tuple such that',
                                      'stor =[[name, threshold]]')
        with open(self.model_path, 'r') as fh:
            read_model = fh.readlines()
        self.total_system_volume = 0
        for stor in storage:
            #Find the relevant curve for the storage node if specified
            if 'TABULAR' in read_model[[k for k in
                                        range([c for c, cl in
                                               enumerate(read_model)
                                               if '[STORAGE]' in cl][0],
                                              len(read_model))
                                        if stor[0] in
                                        read_model[k]][0]]:
                
                relevant_curve = read_model[[k for k in
                                            range([c for c, cl in
                                                   enumerate(read_model)
                                                   if '[STORAGE]' in cl][0],
                                                  len(read_model))
                                            if stor[0] in
                                            read_model[k]][0]].split()[5]
                all_curve = [i for i in read_model if relevant_curve in i]
                all_curve = [i for i in all_curve if i.split()[0] == 
                            relevant_curve]
                sp = 0; count = 0 
                volume = 0
                while sp < stor[1]:
                    volume += (((float(all_curve[count].split()[-1])+
                                float(all_curve[count+1].split()[-1]))/2)*
                               (float(all_curve[count+1].split()[-2])-
                                float(all_curve[count].split()[-2])))
                    sp += (float(all_curve[count+1].split()[-2])-
                           float(all_curve[count].split()[-2]))
                    count += 1
            else:
                volume = stor[1]*float(read_model[[k for k in
                                                   range([c for c, cl in
                                                          enumerate(read_model)
                                                          if '[STORAGE]' in
                                                          cl][0],
                                                         len(read_model))
                                                   if stor[0] in
                                                   read_model[k]][0]].\
                                       split()[5])
            self.total_system_volume += volume
            
        return self.total_system_volume
    
    def run_CAS_model(self, wwtp_capacity, inflow, time_step):
        """
        

        Parameters
        ----------
        wwtp_capacity : FLOAT
            The wwtp capacity in m3/s.
        inflow : LIST
            The total inflow (DWF and Runoff). This is a list of floats
            generated from the output file
        time_step: Float
            The timestep at which the results are reported. This is to 
            transfer inflow to a volume

        Returns
        -------
        total_cso_volume : FLOAT
            The total CSO volume computed for the event(s) run using the model.
        storage_tracked : LIST
            LIST of the amount of storage available in the system at each 
            inflow timeset.

        """
        available_storage = copy.copy(self.total_system_volume) #starting at 0
        total_cso_volume = 0 # starting at 0
        storage_tracked =[] #initlialise empty list
        for inflow_t in inflow:

            if inflow_t*time_step > wwtp_capacity*time_step + available_storage:
                #if there is more inflow than the system can cope with (statically
                #and dynamically, then there is an overflow and no storage is left)
                available_storage = 0
                total_cso_volume += (inflow_t*time_step -
                                     wwtp_capacity*time_step -
                                     available_storage)
                
            else:
                # the difference in in and out is the difference in storage
                #but it cannot exceed the total system volume
                available_storage = min(available_storage +
                                        wwtp_capacity*time_step -
                                        inflow_t*time_step,
                                        self.total_system_volume)
            storage_tracked.append(available_storage) #record the current 
            #available storage
        return total_cso_volume, storage_tracked
