# -*- coding: utf-8 -*-
"""

@author: ir J.A. van der Werf (j.a.vanderwerf@tudelft.nl)
"""


import pyswmm
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl


class HeuristicRTC():
    """
    Heuristic RTC is a python class used in the course 
    ENVM1601 for the MSc Environmental Engineering at the Delft
    University of Technology. This code is meant to aid students in their
    initial experience with Real Time Control of Urban Drainage Systems. 
    
    This code relies heavily on the EPA SWMM5 Python wrapper "pyswmm",
    developed and maintained by Briant McDonnell:
    https://doi.org/10.21105/joss.02292
    
    """
    def __init__(self,
                 model_directory=None,
                 model_name=None,
                 ):
        """
        The initialisation of the model run. Most of the code below is to 
        ensure that there is a correct link to a SWMM model.

        Parameters
        ----------
        model_directory : TYPE, str
            Takes the directory of the SWMM model to be used. 
            The default is None.
        model_name : TYPE, str
            Takes the name of the inputfile (including the '.inp' extension).
            The default is None.

        Returns
        -------
        None.

        """
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
            
            
        
    def run_model(self, rule_dictionary):
        """
        

        Parameters
        ----------
        rule_dictionary : DICT
            "rule dictionary" contains the rules which are used for 
            controlling the catchment. The translation form takes a list 
            of rules per actuator. These lists contain lists of the rules in 
            the form of :
                1. The node that the rule is based on
                2. The level that node needs to above or below to change the 
                   rule
                3. The set point for the relevant pump where:
                    0 = OFF
                    1 = ON (Full capacity as per the pump curve)
                    any value between 0-1 for the percentage utilised
                4. "higher" or "lower", to determine if the rule is about being
                   higher or lower than the given treshold
            example:
                rule_dictionary = {'p10_1': [['j_10', 0.2, 1, 'higher'],
                                   ['j_10', 0.2, 0, 'lower']],
                                   'p_2_1':[['j_2', 0.5, 1, 'higher'],
                                 ['j_2', 0.2, 0, 'lower'],
                                 ['j_2', 1.5, 0.5, 'higher']],
                                    'p_20_2': [['j_20', 0.3, 1, 'higher'],
                                   ['j_20', 0.2, 0, 'lower']],
                                    'p_21_2': [['j_21', 0.3, 1, 'higher'],
                                   ['j_21', 0.2, 0, 'lower']],
                                    'CSO_Pump_2': [['j_2', 2.6, 1, 'higher'],
                                         ['j_2', 2.3, 0, 'lower']],
                                    'CSO_Pump_21': [['j_21', 1, 1, 'higher'],
                                         ['j_21', 0.8, 0, 'lower']],
                                    'WWTP_inlet': [['j_10', 0.3, 1, 'higher'],
                                            ['j_10', 0.1, 0, 'lower']]}

        Returns
        -------
        DataFrame
            A pandas dataframe with the outfall recorded for each of
            the outfalls in the model.

        """
        assert isinstance(rule_dictionary, dict), ('Ensure that the rules ' +
                                                   'specified are in a ' +
                                                   'dictionary format')
        assert isinstance(list(rule_dictionary.values())[0],
                          list), ('The dictionary entries should be a -list-' +
                                  ' of conditions, not a ' + '%s' % 
                                  type(list(rule_dictionary.values())[0]))
        with pyswmm.Simulation(self.model_path) as sim:
            links_model = pyswmm.Links(sim) #initialise the link connections
            nodes_model = pyswmm.Nodes(sim) #initlialise the node connections
            system_routing = pyswmm.SystemStats(sim) #enable getting the stats
            sim.step_advance(900) #the system can only change every 15min
            self.list_of_pumps = [i.linkid for i in
                                  links_model if i.is_pump()] #makes a list of 
            #all the pumps available in the system that should be controlled
            self.list_of_outfalls = [i.nodeid for i in nodes_model
                                     if i.is_outfall()]
            #lists all the outfall in the system
            self.outfall_results = [[] for i in self.list_of_outfalls]
            #initialises a list of lists where the results can be stored during
            #the run
            self.times = [] #idem as above but for the time
            for step in sim:
                for pump in self.list_of_pumps:
                    try: #the try construction is to catch if the pump is not 
                         #specified, to give a more accurate error
                        for rule in rule_dictionary[pump]:
                            ## IMPLEMENTATION OF THE RULES ##
                            if 'higher' in [d.lower() for d in
                                            rule if isinstance(d, str)]:
                                #means the rules is activated if > threshold
                                if nodes_model[rule[0]].depth > rule[1]:
                                    links_model[pump].target_setting = rule[2]
                            elif 'lower' in [d.lower() for d in 
                                             rule if isinstance(d, str)]:
                                if nodes_model[rule[0]].depth <= rule[1]:
                                    links_model[pump].target_setting = rule[2]
                    except:
                        return AttributeError('Pump ' + pump +
                                              ' Not Specified in Rules,' +
                                              ' please add')
                ## GETTING THE INFLOW TO THE OUTFALLS AT EACH TIMESTEP ##
                for i, outfall in enumerate(self.list_of_outfalls):
                    self.outfall_results[i].\
                        append(nodes_model[outfall].total_inflow)
                self.times.append(sim.current_time)
            print("Final Routing Error:", "%s" %
                  "{:0.2f}".format(float(system_routing.\
                                         routing_stats['routing_error'])/100)+
                      "%\n" + "Flooding Volume:",
                      "%s" %
                      system_routing.routing_stats['flooding'])
        ## TRANSLATING THE OUTFALL DATA TO 
        self.outfall_output = pd.DataFrame(self.outfall_results)
        self.outfall_output = self.outfall_output.transpose()
        self.outfall_output.columns=self.list_of_outfalls      
        return self.outfall_output
    
    def interpret_results(self, plotting=False):
        """
        

        Parameters
        ----------
        plotting : TYPE, optional
            DESCRIPTION. The default is False.
            Set to TRUE if you want the function to output a plotted overview
            of the outfalls

        Returns
        -------
        Series
            Total loading per outfall as recorded in the model run.
            This might deviate from the .rpt loading summary. This is because
            the rpt is the sum from every computed timestep
            rather than recorded and therefore the interpolation used
            might affect the load.
            Consider the rpt file as more accurate

        """
        mft = mdates.DateFormatter("%Y-%m-%d\n%H:%M")
        if plotting == False:
            return self.outfall_output.sum()
        else:
            max_inflow = np.max(self.outfall_results)
            ## DOWN HERE MAKES THE PLOT ##
            fig, ax = plt.subplots(4, 2, figsize=(10, 5))
            mpl.rcParams['figure.titlesize'] = 18
            for i, c in enumerate(self.outfall_output.columns):
                if i > 3:
                    loc = (i-4, 1)
                else:
                    loc = (i, 0)
                ax[loc[0], loc[1]].plot(self.times, self.outfall_output[c])
                if np.max(self.outfall_output[c]) == 0:
                    ax[loc[0], loc[1]].text(self.times[int(len(self.times)/2)],
                                            max_inflow/2,
                                            'No Outfall Recorded',
                                            horizontalalignment='center',
                                            verticalalignment='center')
                if 'cso' in c:
                    ax[loc[0], loc[1]].set(title='Total Flow To: ' + c.upper(),
                                           ylim=[0, max_inflow*1.1])
                else:
                    ax[loc[0], loc[1]].set(title='Total Flow To: ' + c,
                                           ylim=[0, max_inflow*1.1])
                if loc[0] == 3 or loc[0] == 7:
                    ax[loc[0], loc[1]].set(xticks=[self.times[int(i)] for i in
                                                   [0,
                                                    np.floor(len(self.times)/4),
                                                    np.floor(len(self.times)/2),
                                                    np.floor(3*len(self.times)
                                                             /4),
                                                    len(self.times)-1]])
                    ax[loc[0], loc[1]].xaxis.set_major_formatter(mft)
                else:
                    ax[loc[0], loc[1]].set(xticks=[])
                
            fig.suptitle('Overview of Total Inflow all Outfalls')
            fig.add_subplot(111, frameon=False)
            plt.tick_params(labelcolor='none', which='both', top=False,
                            bottom=False,left=False,right=False)
            plt.ylabel('Inflow Per Outfall ($m^3/s$)')
            fig.tight_layout()
            return self.outfall_output.sum()