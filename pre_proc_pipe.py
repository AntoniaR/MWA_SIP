import os
import sys
import commands

# A script to run cotter then CASA. This must be in a 
# different script to the download becuase we use different
# ques to submit the qsub commands. Download = copq which uses node
# that can see the outside world, but are limited in number. Normal 
# que will only used compute nodes, with no outside access. The download
# is run on the copy que nodes and tis script is run on the normal nodes.  

####################################################
#Parset files path(s)
loc_parset_file    = '/home/599/aar599/MWA_SIP/locs_parset.txt'
parset_file    = '/home/599/aar599/MWA_SIP/parset.txt'
#####################################################

def read_parset(parset_file):
    """
     Read the parameter file defined in parset file path and return args
    """
    print 'Reading parameter set file'
    f = open(parset_file,'r')
    config_dict = {}
    for line in f:
        if line[0] == '#':
            pass;
        else:
            items = line.split('=', 1)
            config_dict[items[0]] = eval(items[1])
    return config_dict

####################################################
# Read the location parset to find the paths
locs = read_parset(loc_parset_file)
SIP_home = locs['SIP_home']
error_logs = locs['error_logs']
msgen_loc    = locs['msgen_loc']
results_dir = locs['results_dir']
OBS_ID_LIST = open(SIP_home+'/obs_id_list.txt', 'r')
####################################################

def run_cotter(obs_id):
    #os.system('make_metafits.py --gps='+str(obs_id))
    os.system('cotter -o '+str(obs_id)+'.ms -mem 75 -timeres 2 -freqres 80 -m '+str(obs_id)+'.metafits '+str(obs_id)+'/*.fits')

############## Main code ######################

obs_id = sys.argv[1] # Get the obs_id we want to work on. Parsed to the script by run_pipe.py

os.chdir(msgen_loc)
os.chdir(obs_id)

if os.path.exists(str(obs_id)+'.ms'):
   print 'Data already pre-processed, skipping'
else:    
   run_cotter(obs_id)
   

uvfits_dir = os.getcwd()
######### Run the CASA pipe ##########
#os.system('change_db.py curtin')
file_to_process = (str(uvfits_dir)+'/'+str(obs_id)+".ms") 
print 'Created '+file_to_process+' : parsing to CASA for reduction' 

if not os.path.isfile(results_dir+'/versions.txt') or os.path.getctime(results_dir+'/versions.txt') < os.path.getmtime(locs['anoko_build']):
    ## BEWARE: This will fail if you try to use an old build. If using an old build, manually delete the versions.txt file
    ## This will create a new versions.txt file if you are using a younger build than the previous versions.txt
    ## Alternatively... could delete versions.txt at the very start of every run_pipe... Then could remove the 'or'
    print 'Creating new versions.txt file'
    os.system('rm '+results_dir+'/versions.txt')
    versionFile=open(results_dir+'/versions.txt','w')
    versionFile.write("cotterVersion='"+str(commands.getstatusoutput('cotter -version')[1].split('\n')[0])+"'\n")
    versionFile.write("AOFlaggerVersion='"+str(commands.getstatusoutput('cotter -version')[1].split('\n')[1])+"'\n")
    versionFile.write("casaVersion='"+str(commands.getstatusoutput('which casa')[1])+"'\n")
    versionFile.write("WSCleanVersion='"+str(commands.getstatusoutput('wsclean -version')[1].split('\n')[1])+"'\n")
    versionFile.close()


os.system("/short/ek6/CASA/casapy-stable-42.0.26465-001-64b/casapy -c "+SIP_home+"/SIP_128T_parallel_phase_2.py  "+file_to_process)
# Run make_beam.py outside of casa becuase pyephem fails to compile with casa 4.2 THIS IS A PAIN IN THE ARSE!!!!!
f = open('delays.txt')
lines = f.readlines()
str_delays = lines[0]
f.close()
parset = read_parset(parset_file)
robust = parset['robust']
robust = float(robust)
if robust < 0:
      robust = str(robust)
      robust = robust.split('-')[1]
      outimage_XX = obs_id+'_C_bm'+str(robust)+'_XX.fits'
      outimage_YY = obs_id+'_C_bm'+str(robust)+'_YY.fits'
      outimage_I = obs_id+'_C_bm'+str(robust)+'_I.fits'
      beam_XX = obs_id+'_C_bm'+str(robust)+'_XX_beamXX.fits'
      beam_YY = obs_id+'_C_bm'+str(robust)+'_XX_beamYY.fits'
else:
      outimage_XX = obs_id+'_C_bp'+str(robust)+'_XX.fits'
      outimage_YY = obs_id+'_C_bp'+str(robust)+'_YY.fits'
      outimage_I = obs_id+'_C_bp'+str(robust)+'_I.fits'
      beam_XX = obs_id+'_C_bp'+str(robust)+'_XX_beamXX.fits'
      beam_YY = obs_id+'_C_bp'+str(robust)+'_XX_beamYY.fits'

#outimage = obs_id+'_XX.fits'
os.system('python /short/ek6/MWA_Code/bin/make_beam.py -f '+outimage_XX+' -d '+str_delays) # Make the beam files
#XX_beam = obs_id+'_XX_beamXX.fits'
#YY_beam = obs_id+'_XX_beamYY.fits'
XX_beam = beam_XX
YY_beam = beam_YY
XX_image = outimage_XX
YY_image = outimage_YY

print XX_beam, YY_beam, XX_image, YY_image, outimage_I

os.system('/short/ek6/CASA/casapy-stable-42.0.26465-001-64b/casapy -c '+SIP_home+'/make_casa_stoke_I.py '+str(obs_id)+' '+str(XX_image)+' '+str(YY_image)+' '+str(XX_beam)+' '+str(YY_beam) +' '+str(outimage_I))
# Copy all the images to results dir. 
os.system('cp *_I.fits '+results_dir)
os.system('cp *_XX.fits '+results_dir)
os.system('cp *_YY.fits '+results_dir)
os.system('cp *_Q.fits '+results_dir)
os.system('cp *_U.fits '+results_dir)
os.system('cp *_V.fits '+results_dir)
#os.system('cp *XX-image* '+results_dir)
#os.system('cp *YY-image* '+results_dir)
#os.system('cp *image-* '+results_dir)
# Remove the raw data (optional see parset)
parset = read_parset(parset_file)
doRemove = parset['doRemove']
if doRemove:
   os.system('rm -rf '+str(msgen_loc)+'/'+str(obs_id))     
