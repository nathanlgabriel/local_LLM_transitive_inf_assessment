#!/usr/bin/env python
# coding: utf-8

import numpy as np
import numba
import math
from numpy.random import Generator, PCG64DXSM, SeedSequence
import concurrent.futures

np.set_printoptions(suppress=True)

@numba.jit(nopython=True)
def single_play(fnoise2, fplen2, falen2, fmaxval2, fsides2, frein2, fpunish2, frecweights2, fsigweights2, fstate2, frandunif22, frandunif42, frandunif62, frandunif82, frandunif102, fpairs2, frewards2):
    fcumsum2 = 0.
    
    if fsides2[0] == 0 or fsides2[1] == 0:
        stateidx = fstate2 % fplen2
    else:
        stateidx = fstate2 % falen2
    
    leftstate = fpairs2[stateidx][0]
    rightstate = fpairs2[stateidx][1]
    left_correct = frewards2[stateidx][0]
    right_correct = frewards2[stateidx][1]
    
    leftweights = (fsigweights2[fsides2[0]][0][leftstate]).copy()
    rightweights = (fsigweights2[fsides2[0]][1][rightstate]).copy()
    
    leftsum = np.cumsum(leftweights)
    rightsum = np.cumsum(rightweights)
    
    leftsumrand = leftsum[-1] * frandunif22
    rightsumrand = rightsum[-1] * frandunif42
    
    lxsum = np.zeros(len(leftsum))
    rxsum = np.zeros(len(leftsum))
    lxsum[leftsum < leftsumrand] = 1
    rxsum[rightsum < rightsumrand] = 1
    
    leftval = math.floor(np.sum(lxsum))
    rightval = math.floor(np.sum(rxsum))
    
    # receiver noise
    if frandunif102[0] < fnoise2:
        leftval -= 1
        if leftval < 0:
            leftval = 0
    elif frandunif102[0] > (1 - fnoise2):
        leftval += 1
        if leftval > fmaxval2:
            leftval = fmaxval2
            
    if frandunif102[1] < fnoise2:
        rightval -= 1
        if rightval < 0:
            rightval = 0
    elif frandunif102[1] > (1 - fnoise2): # Fixed typo from [0] to [1]
        rightval += 1
        if rightval > fmaxval2:
            rightval = fmaxval2
    
    recurn_idx = math.floor(leftval * (fmaxval2 + 1) + rightval)
    recweights = (frecweights2[recurn_idx]).copy()
    recsum = np.sum(recweights)
    recrand = recsum * frandunif62
    
    if recrand < recweights[0]:
        recpick = 0
    else:
        recpick = 1
    
    # Reward lookup instead of comparison
    if left_correct == 1:
        if recpick == 0:
            fcumsum2 += 1
            leftweights[leftval] += frein2
            rightweights[rightval] += frein2
            recweights[0] += frein2
        else:
            leftweights[leftval] += fpunish2
            rightweights[rightval] += fpunish2
            recweights[1] += fpunish2
            if recweights[1] < 1:
                recweights[1] = 1
    else: # right_correct == 1
        if recpick == 1:
            fcumsum2 += 1
            leftweights[leftval] += frein2
            rightweights[rightval] += frein2
            recweights[1] += frein2
        else:
            leftweights[leftval] += fpunish2
            rightweights[rightval] += fpunish2
            recweights[0] += fpunish2
            if recweights[0] < 1:
                recweights[0] = 1
    
    for idx21 in range(0, len(leftweights)):
        if leftweights[idx21] < 1:
            leftweights[idx21] = 1
        if rightweights[idx21] < 1:
            rightweights[idx21] = 1
            
    fsigweights2[fsides2[0]][0][leftstate] = leftweights
    fsigweights2[fsides2[0]][1][rightstate] = rightweights
    frecweights2[recurn_idx] = recweights
    
    return frecweights2, fsigweights2, fcumsum2

def randoms(frng, fnsteps1, fmaxvalue1, fplen1, falen1, fsides1):
    fnaturestates1 = frng.integers(fplen1 * falen1, size=fnsteps1)
    fnaturesides1 = frng.integers(fsides1, size=(fnsteps1, 2))
    frandunif2 = frng.random(fnsteps1)
    frandunif4 = frng.random(fnsteps1)
    frandunif6 = frng.random(fnsteps1)
    frandunif8 = frng.random((fnsteps1, 2, fmaxvalue1))
    frandunif10 = frng.random((fnsteps1, 2))
    return fnaturestates1, frandunif2, frandunif4, frandunif6, frandunif8, frandunif10, fnaturesides1

@numba.jit(nopython=True)
def nstepsfn(fnoiseN, fplenN, falenN, fmaxvalN, fsidesN, frecweightsN, fsigweightsN, frandunif2N, frandunif4N, frandunif6N, frandunif8N, frandunif10N, fnaturestatesN, fnsteps, fpairsN, fpairsRewN, freinN, fpunishN):
    fcumsumN = 0
    for idxN in range(0, fnsteps):
        fstateN = fnaturestatesN[idxN]
        frecweightsN, fsigweightsN, fcumsumadd = single_play(fnoiseN, fplenN, falenN, fmaxvalN, fsidesN[idxN], freinN, fpunishN, frecweightsN, fsigweightsN, fstateN, frandunif2N[idxN], frandunif4N[idxN], frandunif6N[idxN], frandunif8N[idxN], frandunif10N[idxN], fpairsN, fpairsRewN)
        fcumsumN += fcumsumadd
    return frecweightsN, fsigweightsN, fcumsumN

@numba.jit(nopython=True)
def nstepsfntest(fnoiseN, fplenN, falenN, fmaxvalN, fsidesN, frecweightsN, fsigweightsN, frandunif2N, frandunif4N, frandunif6N, frandunif8N, frandunif10N, fnaturestatesN, fnsteps, fpairsN, fpairsRewN, freinN, fpunishN):
    fcumsumNtest = 0
    # Track per-pair success: [attempts, successes]
    pair_stats = np.zeros((len(fpairsN), 2), dtype=np.int64)
    
    for idxN in range(0, fnsteps):
        fstateN = fnaturestatesN[idxN]
        # For test phase, we use len(fpairsN) for both lengths to override adjacent-only branch
        frecweightsNtest, fsigweightsNtest, fcumsumaddtest = single_play(fnoiseN, len(fpairsN), len(fpairsN), fmaxvalN, [0, 0], freinN, fpunishN, frecweightsN, fsigweightsN, fstateN, frandunif2N[idxN], frandunif4N[idxN], frandunif6N[idxN], frandunif8N[idxN], frandunif10N[idxN], fpairsN, fpairsRewN)
        fcumsumNtest += fcumsumaddtest
        
        # update stats
        stateidx = fstateN % len(fpairsN)
        pair_stats[stateidx, 0] += 1
        pair_stats[stateidx, 1] += int(fcumsumaddtest)
        
    return frecweightsN, fsigweightsN, fcumsumNtest, pair_stats

def play_sequence(run_id, rng, rein1, punish1, rein2, punish2, timesteps, nsteps, sides, pairs, testpairs, nonadjpairs, allpairs, pairs_reward, testpairs_reward, nonadjpairs_reward, allpairs_reward, plen, alen, terms, maxvalue, startstop, noise, annealing, inertia, blocklength):
    
    sigweights = inertia * np.ones([sides, 2, terms, maxvalue])
    recweights = inertia * np.ones([((maxvalue+1)*(maxvalue+1)), startstop])
    
    cumsuc = 0
    iterswitch = 0
    rein = rein1
    punish = punish1
    
    for t in range(0, timesteps // nsteps):
        if ((t + 1) * nsteps) % blocklength == 0:
            iterswitch = (iterswitch + 1) % 2
            noise = noise - annealing
            if iterswitch == 0:
                rein = rein1
                punish = punish1
            else:
                rein = rein2
                punish = punish2
              
        naturestates, randunif2, randunif4, randunif6, randunif8, randunif10, naturesides = randoms(rng, nsteps, maxvalue, plen, alen, sides)
        recweights, sigweights, cumsucadd = nstepsfn(noise, plen, alen, maxvalue, naturesides, recweights, sigweights, randunif2, randunif4, randunif6, randunif8, randunif10, naturestates, nsteps, allpairs, allpairs_reward, rein, punish)
        cumsuc += cumsucadd
        
    naturestates, randunif2, randunif4, randunif6, randunif8, randunif10, naturesides = randoms(rng, nsteps, maxvalue, 1, 2, sides)
    recweights, sigweights, testcumsucadd, pair_stats = nstepsfntest(noise, plen, alen, maxvalue, naturesides, recweights, sigweights, randunif2, randunif4, randunif6, randunif8, randunif10, naturestates, nsteps, testpairs, testpairs_reward, rein, punish)
    
    return run_id, sigweights, cumsuc, cumsucadd, testcumsucadd, recweights, pair_stats
