###################################
# Run the pipeline on mwa-process02
###################################

import os

# Work out which GPS ID / datafile we are going to work on
id_file = open('obs_id_list.txt', 'r')

for line in id_file:  
    os.system('python get_data.py '+line)
    os.system('python pre_proc_pipe.py '+line)
   
  
