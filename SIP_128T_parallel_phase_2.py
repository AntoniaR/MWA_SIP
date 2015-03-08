import numpy
import os,os.path,sys
import math
from datetime import datetime, date, time, timedelta
import logging
import shutil
from threading import current_thread
import traceback
import tempfile
import time
import re
import pyfits
import csv

from mwapy import fits_utils as FU
#from mwapy.pb import mwapb

import mwapy


############################################
##### Configuration-dependent path ########
#Parset files path(s)

loc_parset_file    = '/home/599/aar599/MWA_SIP/locs_parset.txt'
parset_file    = '/home/599/aar599/MWA_SIP/parset.txt'

######## Read parameter set file ###########

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

##############################################

def autoreduce(fitsfile, expedition, dosub, doimage, dopbcor, out_dir):
    '''
    Task to reduce a given uvfits file using the settings defined in parset.txt.
    '''
    ms=None
    params = read_parset(parset_file)
    print 'Starting autoreduce (function:autoreduce)'
    vis = fitsfile
    filename = obspath.split('/')[-1]
    obsid = filename.split('.')[0]
    doSplit = params['doSplit']
    doCasa = params['doCasa']
    split_uv_range = params['split_uv_range'] 
    if doSplit:
       print 'Splitting out baslines with range:'
       print split_uv_range
       os.system('rm -rf temp.ms')
       os.system('mv '+fitsfile+' temp.ms')
       split(vis='temp.ms', outputvis=fitsfile, uvrange=split_uv_range, keepflags=True, datacolumn ='data')
       os.system('rm -rf temp.ms')
    print 'Running Flagging'
    autocal(vis)    
    print "Calibration finished (function:autoreduce)"
    #### Split the data into frequency bins ###
    if dosub:
        #params = read_config(parset_file)
        nfreqs = params['nfreqs']
        freqbin=768/nfreqs
        splitvises=[]
        visroot = os.getcwd()
        for chan in range(nfreqs):
            newvis=visroot+'/f'+`chan`+'.ms'
            spw='0:%i~%i'%(freqbin*chan,freqbin*(chan+1)-1)
            print 'Splitting spw %s into file %s'%(spw,newvis)
            split(vis=vis,outputvis=newvis,datacolumn='corrected',spw=spw,width=1,timebin='0s',uvrange='',correlation='',keepflags=True)
            clearcal(newvis)
            splitvises.append(newvis)
        spw=''
    if doimage:
        if doCasa:
        #### Initialise list
            threshold=[0,0,0,0,0]
            params = read_parset(parset_file)
        #### New addition - find initial r.m.s. then clean down to it next time
            dormsfind=F
            if dormsfind:
            #params = read_config(parset_file)
        #### Weighting should be the same
                cleanweight=params['cleanweight']   
                robust = params['robust']
                im_uvrange = params['im_uvrange']
        #### Halve the resolution, keeping image size the same
                imsize = params['imsize']
            #[cell, imsize]= getCell_Image_size(vis)
                imsize = [int(float(imsize[0])/2),int(float(imsize[1])/2)]
            #imsize = imsize/2
        #### Original
                cell = params['cell']
                scell = re.split('arcmin',cell)
                ncell = float(scell[0])*2.0
            #ncell = float(cell[0])*2.0
            #ncell = cell*2.0
                scell = str(ncell)+'arcmin'
                cell = [scell,scell]
                niter = params['niter']
        #### Fast options
                wprojplanes = 1
                facets = 1
                cyclefactor = 1.5
        #### Unchanged
                psfmode = params['psfmode']
                imagermode = params['imagermode']
                mode = params['mode']
                gridmode = params['gridmode']
                out_images = []
                out_stokes = []
                beam_images = []
                beam_stokes = []
                Ext_label = []
                print cell
        #### Find noise for each polarisation, since it can be quite different
                all_stokes = params['stokes']
                s = 0
                for stokes in all_stokes:
                    imagename = 'preview'
                #                params = read_config()
                    threshold[s] = params['threshold']
                    thresh=str(threshold[s])+'Jy'
                    print 'Imaging a preview image to measure r.m.s. with settings: imsize '+str(imsize)+', cell = '+str(cell)+', niter = '+str(niter)+', clean threshold = '+thresh+', wprojplanes = '+str(wprojplanes)+', stokes= '+stokes
                    clean(vis=vis,imagename=imagename,mode=mode,gridmode=gridmode, wprojplanes=wprojplanes, facets=facets, niter=niter,threshold=thresh[s],psfmode=psfmode,imagermode=imagermode,cyclefactor=cyclefactor,interactive=False,cell=cell,imsize=imsize,stokes=stokes,weighting=cleanweight,robust=robust,pbcor=False, selectdata=True, uvrange=im_uvrange)
        #### Mask out the central 50% of the beam to avoid source confusion
                    if not(os.path.exists('temp.beam')):
        #### Don't make the beam again if it already exists
                        file_made = pbcor('preview.image', filename, outname='temp.beam')
        #### We don't need the automatically-generated beam fits file
                        os.system('rm beam_temp.beam.fits')
                    ia.open('preview.image')
        #### And any sources > 5-6 sigma (i.e. -min of the image)
                    ia.calcmask(mask='(preview.image < (-min(preview.image)))&&(temp.beam<(0.5*max(temp.beam)))',name='msk')
                    ia.done()
        #### Measure first-pass r.m.s.
                    my_output=imstat('preview.image')
                    foundrms=my_output['rms']
        #### Set threshold from measured r.m.s.
                    threshold[s] = 3*foundrms[0]
                    print 'Measured r.m.s. of masked image as '+str(foundrms[0])+'Jy'
                    print 'Setting clean threshold to 3*r.m.s.= '+str(threshold[s])+'Jy'
                    s+=1
        #### Delete preview images
                    rmtables('preview*')
        #### Delete preview beam
                    rmtables('temp*')
        #### NITER should be high, as we are now cleaning down to the noise
                    niter=20000
            else:
                all_stokes = params['stokes']
                s=0
                for stokes in all_stokes:
                    threshold[s] = params['threshold']
                    s+=1
                niter = params['niter']
        #### Imager settings ####
        #### Move these and other settings to a parset file outside the script.
        #params = read_config() 
            im_uvrange = params['im_uvrange']
            cleanweight=params['cleanweight']   
            imsize = params['imsize']
            cell = params['cell']
            robust = params['robust']
            wprojplanes = params['wprojplanes']
            facets = params['facets']
        #        threshold = params['threshold']
            psfmode = params['psfmode']
            cyclefactor = params['cyclefactor']
            imagermode = params['imagermode']
            mode = params['mode']
            gridmode = params['gridmode']
            doStokesI = params['doStokesI']
            out_images = []
            out_stokes = []
            beam_images = []
            beam_stokes = []
            Ext_label = []
        #[cell, imsize]= getCell_Image_size(vis)
        #cell = str(cell)+'arcmin' 
        ###################################
        # Image the total bandwidth image #
            obsid = filename.split('.')[0]
            s=0

            for stokes in all_stokes:
                if stokes == 'XX' or 'YY':
                    imagename = 'f_all_'+stokes
                    thresh=str(threshold[s])+'Jy'
                    print 'Imaging full bandwidth image with settings: imsize = '+str(imsize)+', cell = '+str(cell)+', niter = '+str(niter)+', clean threshold = '+thresh + ', wprojplanes = '+str(wprojplanes) + ', Stokes= '+str(stokes)
                    robust = float(robust)
                    print 'Robust = '+str(robust)
                    clean(vis=vis,imagename=imagename,mode=mode,gridmode=gridmode, wprojplanes=wprojplanes, facets=facets, niter=niter, threshold=thresh, psfmode=psfmode,imagermode=imagermode,cyclefactor=cyclefactor,interactive=False,cell=cell,imsize=imsize,stokes=stokes,weighting=cleanweight,robust=robust,pbcor=False,selectdata=True, uvrange=im_uvrange)
                if robust < 0:
                    robust = str(robust)
                    robust_str = robust.split('-')[1]
                    outimage = str(obsid)+'_C_bm'+str(robust_str)+'_'+stokes+'.fits'
                else: 
                    outimage = str(obsid)+'_C_bp'+str(robust)+'_'+stokes+'.fits'
                #outimage=obsid+'_'+stokes+'.fits'
                imagename=imagename+".image"
                execfile('/short/ek6/MWA_Code/MWA_Tools/scripts/casa_fixhdr.py')
                #exportfits(fitsimage=outimage,imagename=imagename+".image",stokeslast=False,overwrite=True)
                os.system('mv f_all_'+stokes+'.fits '+outimage)
                #exportfits(fitsimage=outimage,imagename=imagename+".image",stokeslast=False,overwrite=True)
                out_images.append(outimage)
                #out_stokes.append(stokes)
                #Ext_label.append(imagename)
                s+=1
          ##### Stokes I image #####
                if doStokesI:
                    stokes = 'I'
                    imagename = 'f_all_'+stokes
                    print 'Generating Stokes I image using immath (function:autoreduce)'
                    #print 'Making primary beam maps'
                    # Get the delays from the text file
                    #f = open('delays.txt')
                    #lines = f.readlines()
                    #str_delays = lines[0]
                    #f.close()
                    #os.system('python /short/ek6/MWA_Code/bin/make_beam.py -f '+outimage+' -d '+str_delays) # Make the beam files
                    #XX_beam = obsid+'_XX_beamXX.fits'
                    #YY_beam = obsid+'_XX_beamYY.fits'
                    #XXYYimages=['f_all_XX.image','f_all_YY.image',XX_beam,YY_beam]
                    #immath(imagename=XXYYimages,expr='((IM0/IM2)+(IM1/IM3))/2', outfile=imagename+'.image')
                    #outimage=obsid+'_'+stokes+'.fits'
                    #exportfits(fitsimage=outimage,imagename=imagename+".image",stokeslast=False,overwrite=True)
                    #out_images.append(outimage)
                    #out_stokes.append(stokes)
                    #Ext_label.append(imagename)

            ##### Image each sub-band file #####
            if dosub:
                for vis in splitvises:
                    visroot,ext=os.path.splitext(vis)
                s=0
                for stokes in all_stokes:
                    if stokes == 'XX' or 'YY':
                    ### Assume the noise goes as sqrt(bandwidth), so if bandwidth is divided by n, noise goes up as sqrt(n)
                        thresh=str(threshold[s]*sqrt(nfreqs))+'Jy'
                        print 'Now imaging '+vis+' in stokes '+stokes+' to clean threshold '+thresh
                        imagename=visroot+'_'+stokes
                        clean(vis=vis,imagename=imagename,mode=mode,gridmode=gridmode, wprojplanes=wprojplanes,facets=facets, niter=niter,threshold=thresh, psfmode=psfmode,imagermode=imagermode,cyclefactor=cyclefactor,interactive=False,cell=cell,imsize=imsize,stokes=stokes,weighting=cleanweight,robust=robust,pbcor=False, selectdata=True, uvrange=im_uvrange) 
                        outimage=obsid+'_'+stokes+'.fits'
                        exportfits(fitsimage=outimage,imagename=imagename+".image",stokeslast=False,overwrite=True)
                        out_images.append(outimage)
                        out_stokes.append(stokes)
                        Ext_name = imagename.split('/')[-1]
                        Ext_label.append(Ext_name+'_'+stokes)
          ##### Stokes I image #####
                    if doStokesI:
                        stokes = 'I'
                        imagename = visroot+'_'+stokes
                        print 'Generating Stokes I image using immath (function:autoreduce)'
                        XXYYimages=['f_all_XX.image','f_all_YY.image','beam_f_all_XX_'+filename+'.fits','beam_f_all_YY_'+filename+'.fits']
                        immath(imagename=XXYYimages,expr='(IM0*IM2)+(IM1*IM3)/(IM2+IM3)', outfile=imagename+'.image')
                        outimage=obsid+'_'+stokes+'.fits'
                        exportfits(fitsimage=outimage,imagename=imagename+".image",stokeslast=False,overwrite=True)
                        out_images.append(outimage)
                        out_stokes.append(stokes)
                        Ext_name = imagename.split('/')[-1]
                        Ext_label.append(Ext_name+'_'+stokes)
          ###########################
                print 'Finished imaging all subbands (function:autoreduce)'
            else:
                print 'Skipping subband image production stage (function:autoreduce)'



        ############ WSClean ###############
        WSClean_startup(obsid)




        ######### Merge fits files ##########
        cube = params['cube']
        #master_sync = params['master_sync']
        #master_sync_dir = params['master_sync_dir']
        if cube:
            print 'Merging all images in to one fits image (function:autoreduce)'
            print 'INFO: Each subband will be stored as a seprerate Extension'
            print 'INFO: In ds9 click: Open Other > Open Multi Ext as Data Cube - to view subbands.'
            merge_all_fits(out_images, out_stokes, filename+'.fits', Ext_label)
            print 'Merging beam files together'
            merge_all_fits(beam_images, beam_stokes,'beam_'+filename+'.fits', Ext_label)
            print 'Moving final image(s) to results folder ('+out_dir+')'
            shutil.copy(job_path+'/'+filename+'.fits',out_dir)
            shutil.copy(job_path+'/'+'beam_'+filename+'.fits',out_dir)
            if master_sync:
                print 'Copying files to master directory'
                shutil.copy(job_path+'/'+filename+'.fits',master_sync_dir)
                shutil.copy(job_path+'/'+'beam_'+filename+'.fits',master_sync_dir)
                print 'Syncing files with Sydney server'
                os.system('/home/mebell/SIP/sync.go')
            else:
                print 'Copying all files to results dir (not creating cube)'
                for im_file in out_images:
                    shutil.copy(im_file,out_dir)
                for bm_file in beam_images:
                    shutil.copy(bm_file,out_dir)
        #####################################
    print 'Finished Successfully'

############### autocal ##################

def autocal(vis):
    '''
    Function to automatically calibrate the data. This function will use setjy or you can define a cl file to calibrate off
    '''
    locs = read_parset(loc_parset_file)
    anoko_build = locs['anoko_build']
    #anoko_build2 = '/short/ek6/MWA_Code/anoko/mwa-reduce/build_4'
    params = read_parset(parset_file)
    refant  = params['refant']
    bsolint = params['bsolint']
    cal_uvrange = params['cal_uvrange']
    cal_loc = locs['cal_loc']
    cal_method = params['cal_method']
    minsnr  = params['minsnr']  
    calflux = params['calflux']
    calspex = params['calspex']
    calfreq = params['calfreq']
    print 'Calibrating with settings: ref antenna = '+str(refant)+' , bsolint = '+str(bsolint)+', uvrange = '+str(cal_uvrange)+', minsnr = '+str(minsnr)+' (funtion:autocal)'
    caltable='temp'
    #clearcal(vis)
    if   cal_method == 1:
            print 'Using setjy method (function:autocal)'
            setjy(vis=vis,fluxdensity=calflux, spix=calspex, reffreq=calfreq, field='0')
            bcal=caltable+'.bcal'
            if os.path.exists(bcal):
               rmtables(bcal)
            bandpass(vis=vis,caltable=bcal,solint=bsolint,refant=refant,bandtype='B',append=False,selectdata=True,uvrange=cal_uvrange,minsnr=minsnr)
            applycal(vis=vis,selectdata=False,gaintable=bcal)
            # put the visibilities to a fixed phase center
 #           if phasecenter!=''
 #                   fixvis(vis=vis,outputvis=vis,phasecenter=phasecenter)
    elif cal_method == 2:
            print 'Using cl method (function:autocal)'
            im.open(vis,usescratch=True)
            im.ft(complist=cal_loc)
            im.close()
            bcal=caltable+'.bcal'
            if os.path.exists(bcal):
               rmtables(bcal)
            bandpass(vis=vis,caltable=bcal,solint=bsolint,refant=refant,bandtype='B',append=False,selectdata=True,uvrange=cal_uvrange,minsnr=minsnr)
            applycal(vis=vis,selectdata=False,gaintable=bcal)
            # put the visibilities to a fixed phase center
#            if phasecenter!=''
#                    fixvis(vis=vis,outputvis=vis,phasecenter=phasecenter)
    elif cal_method == 3:
            print 'Using copy solutions method (function:autocal)'
            applycal(vis=vis,selectdata=False,gaintable=cal_loc)
            # put the visibilities to a fixed phase center
#            if phasecenter!=''
#                    fixvis(vis=vis,outputvis=vis,phasecenter=phasecenter)

    elif cal_method == 4:
            print 'Using selfcal method adapted from GLEAM - Antonia' 

            # first put the new image onto a common phase center given in the parset file, using the CASA fixvis tool

#            phasecenter=params['phasecenter']
            
#            fixvis(vis=vis,outputvis=vis,phasecenter=phasecenter)
            
            wsize = params['wsize']
            wscale = params['wscale']
            # Using the primary beam corrected image output from this pipeline from 2min image as the sky model - Here assuming that the model image is made using the exact same parameters as the output images... See GLEAM code for regridding options.
 
            img = cal_loc
#            obsid=img.split('_')[0]

            # Make primary beam corrected model
            if not os.path.exists(img+'initcor-I.fits'):
                cwd = os.getcwd()
                print 'making primary beam corrected model - Antonia'
                os.chdir('/short/ek6/aar599/tmp_data/1061661200_calibrator')

                os.system(anoko_build+'/pbcorrect '+img+' model.fits beam '+img+'initcor')
                os.mkdir('unused')
                os.system('mv '+img+'initcor-Q.fits unused/.')
                os.system('mv '+img+'initcor-U.fits unused/.')
                os.system('mv '+img+'initcor-V.fits unused/.')
                os.chdir(cwd)

            print 'copying primary beam corrected model - Antonia'
            os.system('cp '+img+'initcor-I.fits .')
            img=img.split('/')[-1]


#            print 'Creating edited model - Antonia'
#            pixelPos=[1769,1796]
#            dim=3
#            hdulist=pyfits.open(img+'initcor-I.fits')
#            hdulist[0].data[0,0,(pixelPos[0]-dim):(pixelPos[0]+dim),(pixelPos[1]-dim):(pixelPos[1]+dim)]= 0 #-5 #= 0.
#            img=img.split('/')[-1]
#            hdulist.writeto(img+'initcor-I.fits')
#            hdulist.close()
            
            # Dirty image for initial beam model for target field
            os.system(anoko_build+'/wsclean -name temp.img -size '+str(wsize)+' '+str(wsize)+' -niter 2 -threshold 0.01 -pol xx,yy,xy,yx -weight briggs -1.0 -scale '+str(wscale)+'  -absmem 57 -joinpolarizations '+vis)
            print 'dirty image made! - Antonia'

            # Generate the beam models
            os.system(anoko_build+'/beam -proto temp.img-XX-model.fits -ms '+vis+' -name beam')
            print 'beam models made - Antonia'

            # Uncorrect the primary beam for this model
            os.system(anoko_build+'/pbcorrect -uncorrect '+img+'uncor model.fits beam '+img+'initcor')

            print 'beam uncorrected... - Antonia'
            # Fourier Transform the model to predict the visibilities
            os.system('/short/ek6/MWA_Code/anoko/mwa-reduce/build_4/wsclean -predict -name '+img+'uncor -size '+str(wsize)+' '+str(wsize)+' -pol xx,yy,xy,yx -weight briggs -1.0 -absmem 57 -scale '+str(wscale)+' '+vis)

            print 'model fourier transformed... - Antonia'
            # Obtain primary beam models and place in useful location
            if not os.path.isdir('mwapy'):
                os.mkdir('mwapy')
                os.mkdir('mwapy/pb')
            os.system('cp $MWA_CODE_BASE/MWA_Tools/mwapy/pb/*atrix.fits ./mwapy/pb/')

            print 'primary beam models copied... - Antonia'
            # Use MWA calibrator to calibrate the measurement set using the sky model from the fits file
            # Try minimum baseline = 60 m (30 lambda at 150 MHz = 2 m) - From GLEAM code.
            os.system(anoko_build+'/calibrate -minuv 60 -a 0.001 0.0001 -p phases.txt gains.txt '+vis+' solutions.bin')

            print 'Self calibrating - Antonia'
            # Apply the solutions to the measurement set
            os.system(anoko_build+'/applysolutions -copy '+vis+' solutions.bin')

######## Funtions for setting image sizes #########

def getBaselineLengths(msFile='', sort=True):
    " A function to retrieve baseline lengths."
    tb.open(msFile+'/ANTENNA')
    names = tb.getcol('NAME')
    positions = numpy.transpose(tb.getcol('POSITION'))
    tb.close()
    UVDist = []
    for i in range(len(names)):
      for j in range(i,len(names)):
          if (i != j):
             dist =  ((positions[i][0]-positions[j][0])**2 +
                     (positions[i][1]-positions[j][1])**2 +
                     (positions[i][2]-positions[j][2])**2)**0.5
             UVDist.append(dist)
    return(UVDist)

def getCell_Image_size(msFile):
    tb.open(msFile + '/SPECTRAL_WINDOW')
    refFreq = tb.getcol('REF_FREQUENCY')[0]
    max_baseline =  max(getBaselineLengths(msFile))
    res_radians = (3e8/refFreq)/(max_baseline) # in radians
    res_arcmin = (res_radians*(180/pi))*60 # in arcmin
    cell_size = res_arcmin/5 #  We want 5 pixels per beam. 
    print "Using optimised cell size of "+str(cell_size)
    imsize_deg = 25*(refFreq/150e6) #FWHM in degrees
    Fudge = 1.0 ###### Increase/decrease to image larger/smaller times the FWHM
    imsize_pixels = int(Fudge*((imsize_deg*60)/cell_size))
    print "Using optimised image size of "+str(imsize_pixels)+' pixels'
    tb.close()
    return cell_size, imsize_pixels

def getNumIntervals(msFile):
    tb.open(msFile)
    lines=tb.getcol('TIME')
    NumIntervals = len(numpy.unique(lines))
    timeavg = int(((lines[-1]-lines[0])/NumIntervals)+0.5)
    tb.close()
    return NumIntervals, timeavg

def update_TStart(name,tstart):
    hdulist = pyfits.open(name, mode='update')
    prihdr = hdulist[0].header
    prihdr.update('DATE-OBS',tstart)
    hdulist.flush()
    return

def rescale_Img(modelImg, rescaleImg):
    os.system('python /short/ek6/MWA_Code/Aegean/aegean.py  --maxsummits=5 --cores=16 --out='+modelImg+'.cat --table='+modelImg+'.vot --seedclip=30 '+modelImg)
    os.system('python /short/ek6/MWA_Code/Aegean/aegean.py  --maxsummits=5 --cores=16 --out='+rescaleImg+'.cat --table='+modelImg+'.vot --seedclip=30 '+rescaleImg)
    matches='matched_sources.vot'
    os.system('rm -rf matched_sources.vot')
    os.system('/short/ek6/MWA_Code/stilts/stilts tmatch2 matcher=sky params=10 in1='+rescaleImg+'.vot  values1="ra dec" suffix1="_init" icmd1="select (local_rms<1.)&&(peak_flux/local_rms)>30" in2='+modelImg+'.vot  values2="ra dec" suffix2="_self" icmd2="select (local_rms<1.)&&(peak_flux/local_rms)>30" out='+matches+' fixcols=all')
    os.system(anoko_build+'/scaleimage '+matches+' peak_flux_init peak_flux_self '+rescaleImg+' rescaled_'+rescaleImg)

###### Need to change filename when tested!


############################################
################ WSClean ###################

def WSClean_startup(obs_id):
    params = read_parset(parset_file)
    intervalFraction = int(params['intervalFraction'])
    if intervalFraction==1:
        WSClean(obs_id,'A',0,0,0)
    else:
        NumIntervals, timeavg = getNumIntervals(obs_id+'.ms')
        #print 'Antonia test outputs for intervalFractions,NumIntervals and timeavg:',intervalFraction,NumIntervals,timeavg
#        ObsStart=getObsStart(obs_id+'.ms')
        fractIntervals = int(NumIntervals/intervalFraction)
        #exit()
        for i in range(intervalFraction):
            print 'Input to WSClean:'+str(obs_id)+' '+str(i)+' '+str(i*fractIntervals)+' '+str((i+1)*fractIntervals)+' '+str(timeavg)+' -- Antonia'
            WSClean(obs_id,i,i*fractIntervals,(i+1)*fractIntervals,timeavg)
#        exit()
        
def WSClean(obs_id,N,start,end,timeavg):
        params  = read_parset(parset_file)
        wniter = params['wniter']
        wsize = params['wsize']
        wscale = params['wscale']
        wthreshold = params['wthreshold']
        wbriggs = params['wbriggs']
        dotwoimages = params['dotwoimages']
        wbriggs2 = params['wbriggs2']
        ImgRescale = params['ImgRescale']

        print 'Running WSClean'
        wbriggs = float(wbriggs) 
        wbriggs2 = float(wbriggs2)
        if wbriggs < 0:
               wbriggs = str(wbriggs)
               briggs_name = wbriggs.split('-')[1]
               name = obs_id+'_'+str(N)+'_W_bm'+str(briggs_name)
        else:
               name = obs_id+'_'+str(N)+'_W_bp'+str(wbriggs)
        locs = read_parset(loc_parset_file)
        anoko_build = locs['anoko_build']

        if N=='A':
            os.system(anoko_build+'/wsclean -joinpolarizations -pol xx,xy,yx,yy -mgain 0.95 -weight briggs '+str(wbriggs)+' -absmem 57 -name '+name+' -size '+str(wsize)+' '+str(wsize)+'  -scale '+str(wscale)+' -niter '+str(wniter)+' -threshold '+str(wthreshold)+' '+str(obs_id)+'.ms')
        else:
            print N
            print anoko_build+'/wsclean -interval '+str(start)+' '+str(end)+' -joinpolarizations -pol xx,xy,yx,yy -mgain 0.95 -weight briggs '+str(wbriggs)+' -absmem 57 -name '+name+' -size '+str(wsize)+' '+str(wsize)+'  -scale '+str(wscale)+' -niter '+str(wniter)+' -threshold '+str(wthreshold)+' '+str(obs_id)+'.ms -- Antonia'
            os.system(anoko_build+'/wsclean -interval '+str(start)+' '+str(end)+' -joinpolarizations -pol xx,xy,yx,yy -mgain 0.95 -weight briggs '+str(wbriggs)+' -absmem 57 -name '+name+' -size '+str(wsize)+' '+str(wsize)+'  -scale '+str(wscale)+' -niter '+str(wniter)+' -threshold '+str(wthreshold)+' '+str(obs_id)+'.ms')
            print 'snapshot '+str(N)+' imaged -- Antonia'
            
#        os.system(anoko_build+'/beam -proto '+name+'-XX-image.fits -ms '+str(obs_id)+'.ms')
        ######### Make the full images 
        os.system(anoko_build+'/pbcorrect '+name+' image.fits beam stokes')
        if N != 'A': # correct tstart for time sliced images
            hdulist = pyfits.open('stokes-I.fits')
            prihdr = hdulist[0].header
            date = datetime.strptime(prihdr['DATE-OBS'],"%Y-%m-%dT%H:%M:%S.%f")
            hdulist.flush()
            tstart = (timedelta(seconds = start*timeavg) + date).strftime("%Y-%m-%dT%H:%M:%S.%f")
            update_TStart('stokes-I.fits',tstart)
            update_TStart('stokes-Q.fits',tstart)
            update_TStart('stokes-U.fits',tstart)
            update_TStart('stokes-V.fits',tstart)
        os.system('mv stokes-I.fits '+name+'_I.fits')
        os.system('mv stokes-Q.fits '+name+'_Q.fits')
        os.system('mv stokes-U.fits '+name+'_U.fits')
        os.system('mv stokes-V.fits '+name+'_V.fits')
        ######## Rename the XX and YY files 
        old_name_X = name+'-XX-image.fits'
        old_name_Y = name+'-YY-image.fits'
        new_name_X = old_name_X.replace('-XX-image.fits','_XX.fits')
        new_name_Y = old_name_Y.replace('-YY-image.fits','_YY.fits')
        os.system('mv '+old_name_X+' '+new_name_X)
        os.system('mv '+old_name_Y+' '+new_name_Y)

        if ImgRescale:
            locs = read_parset(loc_parset_file)
            modelImg=locs['modelImg']
            rescale_Img(modelImg, name+'_I.fits')

        ################################
        if dotwoimages: # Repeat the imaging with different briggs weighting
           if wbriggs2 < 0:
               wbriggs = str(wbriggs)
               briggs_name = wbriggs.split('-')[1]
               name = obs_id+'_W_bm'+str(wbriggs2)
           else:
               name = obs_id+'_W_bp'+str(wbriggs2)
           if N=='A':
               os.system(anoko_build+'/wsclean -joinpolarizations -pol xx,xy,yx,yy -mgain 0.95 -weight briggs '+str(wbriggs2)+' -absmem 57 -name '+name+' -size '+str(wsize)+' '+str(wsize)+'  -scale '+str(wscale)+' -niter '+str(wniter)+' -threshold '+str(wthreshold)+' '+str(obs_id)+'.ms')
           else:
               os.system(anoko_build+'/wsclean -interval '+str(start)+' '+str(end)+' -joinpolarizations -pol xx,xy,yx,yy -mgain 0.95 -weight briggs '+str(wbriggs2)+' -absmem 57 -name '+name+' -size '+str(wsize)+' '+str(wsize)+'  -scale '+str(wscale)+' -niter '+str(wniter)+' -threshold '+str(wthreshold)+' '+str(obs_id)+'.ms')
        
           #os.system(anoko_build+'/beam -proto '+name+'-XX-image.fits -ms '+str(obs_id)+'.ms')
           ######### Make the full images 
           os.system(anoko_build+'/pbcorrect '+name+' image.fits beam stokes')
           if N != 'A': # correct tstart for time sliced images
               hdulist = pyfits.open('stokes-I.fits')
               prihdr = hdulist[0].header
               date = datetime.strptime(prihdr['DATE-OBS'],"%Y-%m-%dT%H:%M:%S.%f")
               hdulist.flush()
               tstart = (timedelta(seconds = start*timeavg) + date).strftime("%Y-%m-%dT%H:%M:%S.%f")
               update_TStart('stokes-I.fits',tstart)
               update_TStart('stokes-Q.fits',tstart)
               update_TStart('stokes-U.fits',tstart)
               update_TStart('stokes-V.fits',tstart)
           os.system('mv stokes-I.fits '+name+'_I.fits')
           os.system('mv stokes-Q.fits '+name+'_Q.fits')
           os.system('mv stokes-U.fits '+name+'_U.fits')
           os.system('mv stokes-V.fits '+name+'_V.fits')
           ######## Rename the XX and YY files 
           old_name_X = name+'-XX-image.fits'
           old_name_Y = name+'-YY-image.fits'
           new_name_X = old_name_X.replace('-XX-image.fits','_XX.fits')
           new_name_Y = old_name_Y.replace('-YY-image.fits','_YY.fits')
           os.system('mv '+old_name_X+' '+new_name_X)
           os.system('mv '+old_name_Y+' '+new_name_Y)

############ Run the code ##################
print '---------------------------------'
print 'MWA 128T Standard Imaging Pipeline'
print '---------------------------------'
print 'Currently in dir '+os.getcwd()

obspath = sys.argv[3]
params = read_parset(parset_file)
locs = read_parset(loc_parset_file)
out_dir = locs['results_dir']
print 'Output directory is '+out_dir
job_path = os.path.dirname(obspath)
#job_path = job_path
os.chdir(job_path)
print "Job path = " +job_path
print 'Currently in dir '+os.getcwd()
print 'Processing '+obspath
os.system('rm -rf '+job_path+'/*.bcal')
os.system('rm -rf '+job_path+'/*.residual')
os.system('rm -rf '+job_path+'/*.psf')
os.system('rm -rf '+job_path+'/*.model')
os.system('rm -rf '+job_path+'/*.flux')
os.system('rm -rf '+job_path+'/*.last')
os.system('rm -rf '+job_path+'/*.fits')
os.system('rm -rf '+job_path+'/*.log')
os.system('rm -rf '+job_path+'/*.image')
os.system('rm -rf '+job_path+'/*.beam')
dopbcor = params['dopbcor']  
dormsfind = params['dormsfind']  
dosub = params['dosub']
doimage= params['doimage']
expedition = params['expedition']
autoreduce(fitsfile=obspath, expedition=expedition, dosub=dosub, doimage=doimage, dopbcor=dopbcor, out_dir=out_dir)

############################################

