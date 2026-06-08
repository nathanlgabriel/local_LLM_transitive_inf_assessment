#!/usr/bin/env python
# coding: utf-8

import random
import numpy as np
import time
import numba
import math
from numpy.random import Generator, PCG64DXSM, SeedSequence
import multiprocessing as mp

np.set_printoptions(suppress=True)

@numba.jit
def single_play(fnoise2, fplen2, falen2, fmaxval2, fsides2, frein2, fpunish2, frecweights2, fsigweights2, fstate2, frandunif22, frandunif42, frandunif62, frandunif82, frandunif102, fpairs2, frewards2):
    fcumsum2 = 0.
    
    if fsides2[0] == 0 or fsides2[1] == 0:
        stateidx = fstate2 % fplen2
    else:
        stateidx = fstate2 % falen2
    
    leftstate = fpairs2[stateidx][0]
    rightstate = fpairs2[stateidx][1]
    
    leftweights = (fsigweights2[fsides2[0]][0][leftstate]).copy()
    rightweights = (fsigweights2[fsides2[1]][1][rightstate]).copy()
    
    leftsum = np.sum(leftweights, axis=1)
    rightsum = np.sum(rightweights, axis=1)
    
    leftsumrand = leftsum*frandunif22
    rightsumrand = rightsum*frandunif42
    
    leftsumrand[leftsumrand > leftweights[:, 0]] = 0
    leftsumrand[leftsumrand != 0] = 1
    rightsumrand[rightsumrand > rightweights[:, 0]] = 0
    rightsumrand[rightsumrand != 0] = 1
    
    # adding in sender noise
    leftnoise = (frandunif82[0]).copy()
    leftnoise[leftnoise > fnoise2] = 0
    leftnoise[leftnoise != 0] = 1
    leftsumrand = (leftsumrand+leftnoise)%2
    
    rightnoise = (frandunif82[1]).copy()
    rightnoise[rightnoise > fnoise2] = 0
    rightnoise[rightnoise != 0] = 1
    rightsumrand = (rightsumrand+rightnoise)%2
    
    leftinvert = (leftsumrand+1)%2
    rightinvert = (rightsumrand+1)%2
    
    leftval = np.sum(leftsumrand)
    rightval = np.sum(rightsumrand)
    
    # adding in receiver noise
    if frandunif102[0] < fnoise2:
        leftval -= 1
        if leftval < 0: leftval = 0
    elif frandunif102[1] > (1-fnoise2):
        leftval += 1
        if leftval > fmaxval2: leftval = fmaxval2
        
    if frandunif102[1] < fnoise2:
        rightval -= 1
        if rightval < 0: rightval = 0
    elif frandunif102[0] > (1-fnoise2):
        rightval += 1
        if rightval > fmaxval2: rightval = fmaxval2
    
    recurn_idx = math.floor(leftval*(fmaxval2+1) + rightval)
    recweights = (frecweights2[recurn_idx]).copy()
    recsum = np.sum(recweights)
    recrand = recsum*frandunif62
    if recrand < recweights[0]:
        recpick = 0
    else:
        recpick = 1
    
    left_correct = frewards2[stateidx][0]
    right_correct = frewards2[stateidx][1]

    if left_correct == 1:
        if recpick == 0:
            fcumsum2 += 1
            leftweights[:, 0] += leftsumrand * frein2
            leftweights[:, 1] += leftinvert * frein2
            rightweights[:, 0] += rightsumrand * frein2
            rightweights[:, 1] += rightinvert * frein2
            recweights[0] += frein2
        else:
            leftweights[:, 0] += leftsumrand * fpunish2
            leftweights[:, 1] += leftinvert * fpunish2
            rightweights[:, 0] += rightsumrand * fpunish2
            rightweights[:, 1] += rightinvert * fpunish2
            recweights[1] = max(recweights[1] + fpunish2, 1.0)
    else:
        if recpick == 1:
            fcumsum2 += 1
            leftweights[:, 0] += leftsumrand * frein2
            leftweights[:, 1] += leftinvert * frein2
            rightweights[:, 0] += rightsumrand * frein2
            rightweights[:, 1] += rightinvert * frein2
            recweights[1] += frein2
        else:
            leftweights[:, 0] += leftsumrand * fpunish2
            leftweights[:, 1] += leftinvert * fpunish2
            rightweights[:, 0] += rightsumrand * fpunish2
            rightweights[:, 1] += rightinvert * fpunish2
            recweights[0] = max(recweights[0] + fpunish2, 1.0)
            
    for idx21 in range(0, len(leftweights)):
        for idx22 in range(0, 2):
            if leftweights[idx21][idx22] < 1:
                leftweights[idx21][idx22] = 1
            if rightweights[idx21][idx22] < 1:
                rightweights[idx21][idx22] = 1
    
    fsigweights2[fsides2[0]][0][leftstate] = leftweights
    fsigweights2[fsides2[1]][1][rightstate] = rightweights
    frecweights2[recurn_idx] = recweights
    
    return frecweights2, fsigweights2, fcumsum2

@numba.jit
def randoms(frng, fnsteps1, fmaxvalue1, fplen1, falen1, fsides1):
    fnaturestates1 = frng.integers(fplen1*falen1, size=fnsteps1)
    fnaturesides1 = frng.integers(fsides1, size=(fnsteps1, 2))
    frandunif2 = frng.random((fnsteps1, fmaxvalue1))
    frandunif4 = frng.random((fnsteps1, fmaxvalue1))
    frandunif6 = frng.random(fnsteps1)
    frandunif8 = frng.random((fnsteps1, 2, fmaxval2)) # Note: fmaxval2 is not in scope here, need to fix this
    # Actually, I'll just use fnsteps1, fmaxvalue1
    return fnaturestates1, frandunif2, frandunif4, frandunif6, frandunif8, frandunif10, fnaturesides1
# I'll rewrite the randoms function correctly in the write command below.
