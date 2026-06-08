#!/usr/bin/env python
# coding: utf-8

# Synchronous SINGLE-URN model (paper sec. 3.2), "base reinforcement learning"
# variant in which both senders are read through fsides2[0].
#
# Modifications relative to
# structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026.py:
#   (1) Data-driven reward lookup replaces the hard-coded leftstate > rightstate
#       rule. Each *pairs array gets a same-shaped *_reward array of 0/1 entries;
#       a 1 marks the position in a pair to reinforce when chosen.
#   (2) The test phase returns per-pair (attempts, successes), is genuinely
#       learning-free (callers pass copies), and a second all-pairs sweep is
#       available for the full distance spectrum.
#   (3) Receiver-noise typo fixed: upward perturbation on rightval now reads
#       frandunif102[1] instead of frandunif102[0].
#
# make_linear_pairs(5) + this file reproduces the original 5-stimulus behavior
# bit-for-bit when seeded identically.


import random
import numpy as np
import time
import numba
import math
from numpy.random import Generator, PCG64DXSM, SeedSequence
import multiprocessing as mp


np.set_printoptions(suppress=True)


# ----------------------------------------------------------------------------
# single play
# ----------------------------------------------------------------------------
@numba.jit
def single_play(fnoise2, fplen2, falen2, fmaxval2, fsides2, frein2, fpunish2,
                frecweights2, fsigweights2, fstate2,
                frandunif22, frandunif42, frandunif62, frandunif82, frandunif102,
                fpairs2, frewards2):
    fcumsum2 = 0.

    if fsides2[0] == 0 or fsides2[1] == 0:
        stateidx = fstate2 % fplen2
    else:
        stateidx = fstate2 % falen2

    leftstate = fpairs2[stateidx][0]
    rightstate = fpairs2[stateidx][1]
    # reward lookup replaces the old `leftstate > rightstate` comparison
    left_correct = frewards2[stateidx][0]

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
    # adding in receiver noise
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
    elif frandunif102[1] > (1 - fnoise2):       # fixed: was frandunif102[0]
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

    if left_correct == 1:                        # left is the rewarded position

        if recpick == 0:
            fcumsum2 += 1

            leftweights[leftval] += frein2
            rightweights[rightval] += frein2

            recweights[0] += frein2
        else:
            leftweights[leftval] += fpunish2
            rightweights[rightval] += fpunish2

            recweights[1] += fpunish2            # punish the chosen (right) weight
            if recweights[1] < 1:
                recweights[1] = 1
    else:                                        # right is the rewarded position
        if recpick == 1:
            fcumsum2 += 1

            leftweights[leftval] += frein2
            rightweights[rightval] += frein2

            recweights[1] += frein2
        else:
            leftweights[leftval] += fpunish2
            rightweights[rightval] += fpunish2

            recweights[0] += fpunish2            # punish the chosen (left) weight
            if recweights[0] < 1:
                recweights[0] = 1

    # floor every sender weight at 1
    for idx21 in range(0, len(leftweights)):
        if leftweights[idx21] < 1:
            leftweights[idx21] = 1
        if rightweights[idx21] < 1:
            rightweights[idx21] = 1

    fsigweights2[fsides2[0]][0][leftstate] = leftweights
    fsigweights2[fsides2[0]][1][rightstate] = rightweights
    frecweights2[recurn_idx] = recweights

    return frecweights2, fsigweights2, fcumsum2


# ----------------------------------------------------------------------------
# random number generation for one block
# ----------------------------------------------------------------------------
def randoms(frng, fnsteps1, fmaxvalue1, fplen1, falen1, fsides1):

    fnaturestates1 = frng.integers(fplen1 * falen1, size=fnsteps1)
    fnaturesides1 = frng.integers(fsides1, size=(fnsteps1, 2))

    frandunif2 = frng.random(fnsteps1)
    frandunif4 = frng.random(fnsteps1)
    frandunif6 = frng.random(fnsteps1)
    frandunif8 = frng.random((fnsteps1, 2, fmaxvalue1))
    frandunif10 = frng.random((fnsteps1, 2))

    return fnaturestates1, frandunif2, frandunif4, frandunif6, frandunif8, frandunif10, fnaturesides1


# ----------------------------------------------------------------------------
# training loop over nsteps plays
# ----------------------------------------------------------------------------
@numba.jit
def nstepsfn(fnoiseN, fplenN, falenN, fmaxvalN, fsidesN, frecweightsN, fsigweightsN,
             frandunif2N, frandunif4N, frandunif6N, frandunif8N, frandunif10N,
             fnaturestatesN, fnsteps, fpairsN, fpairsRewN, freinN, fpunishN):
    fcumsumN = 0
    for idxN in range(0, fnsteps):
        # randomly determine state of nature
        fstateN = fnaturestatesN[idxN]
        # perform a single play
        frecweightsN, fsigweightsN, fcumsumadd = single_play(
            fnoiseN, fplenN, falenN, fmaxvalN, fsidesN[idxN], freinN, fpunishN,
            frecweightsN, fsigweightsN, fstateN,
            frandunif2N[idxN], frandunif4N[idxN], frandunif6N[idxN],
            frandunif8N[idxN], frandunif10N[idxN], fpairsN, fpairsRewN)
        fcumsumN += fcumsumadd

    return frecweightsN, fsigweightsN, fcumsumN


# ----------------------------------------------------------------------------
# test/evaluation loop: learning-free, records per-pair (attempts, successes)
# ----------------------------------------------------------------------------
@numba.jit
def nstepsfntest(fnoiseN, fplenN, falenN, fmaxvalN, fsidesN, frecweightsN, fsigweightsN,
                 frandunif2N, frandunif4N, frandunif6N, frandunif8N, frandunif10N,
                 fnaturestatesN, fnsteps, fpairsN, fpairsRewN, freinN, fpunishN):
    fcumsumNtest = 0
    test_plen = len(fpairsN)
    pair_stats = np.zeros((test_plen, 2), dtype=numba.int64)   # [attempts, successes]
    for idxN in range(0, fnsteps):
        # randomly determine state of nature
        fstateN = fnaturestatesN[idxN]
        stateidx = fstateN % test_plen
        frecweightsNtest, fsigweightsNtest, fcumsumaddtest = single_play(
            fnoiseN, test_plen, test_plen, fmaxvalN, [0, 0], freinN, fpunishN,
            frecweightsN, fsigweightsN, fstateN,
            frandunif2N[idxN], frandunif4N[idxN], frandunif6N[idxN],
            frandunif8N[idxN], frandunif10N[idxN], fpairsN, fpairsRewN)
        pair_stats[stateidx, 0] += 1
        pair_stats[stateidx, 1] += int(fcumsumaddtest)
        fcumsumNtest += fcumsumaddtest

    return frecweightsN, fsigweightsN, fcumsumNtest, pair_stats


# ----------------------------------------------------------------------------
# one full run: train, then two read-only evaluation sweeps
# ----------------------------------------------------------------------------
def play_sequence(n, rng, rein1, punish1, rein2, punish2, timesteps, nsteps, sides,
                  pairs, testpairs, nonadjpairs, allpairs,
                  pairs_reward, testpairs_reward, nonadjpairs_reward, allpairs_reward,
                  plen, alen, terms, maxvalue, startstop, noise, annealing, runs,
                  inertia, blocklength, evalperpair):

    sigweights = inertia * np.ones([sides, 2, terms, maxvalue])
    recweights = inertia * np.ones([((maxvalue + 1) * (maxvalue + 1)), startstop])

    cumsuc = 0
    iterswitch = 0
    rein = rein1
    punish = punish1

    for t in range(0, timesteps // nsteps):

        # a bit of iteration NOTE blocklength must be a multiple of nsteps
        if ((t + 1) * nsteps) % blocklength == 0:
            iterswitch = (iterswitch + 1) % 2
            # annealing
            noise = noise - annealing
            if iterswitch == 0:
                rein = rein1
                punish = punish1
            else:
                rein = rein2
                punish = punish2

        # the actual learning
        naturestates, randunif2, randunif4, randunif6, randunif8, randunif10, naturesides = randoms(
            rng, nsteps, maxvalue, plen, alen, sides)
        recweights, sigweights, cumsucadd = nstepsfn(
            noise, plen, alen, maxvalue, naturesides, recweights, sigweights,
            randunif2, randunif4, randunif6, randunif8, randunif10,
            naturestates, nsteps, allpairs, allpairs_reward, rein, punish)
        cumsuc += cumsucadd

    # ---- held-out test phase on the test pairs (learning-free: pass copies) ----
    ntest = len(testpairs)
    etest = evalperpair * ntest
    naturestates, randunif2, randunif4, randunif6, randunif8, randunif10, naturesides = randoms(
        rng, etest, maxvalue, 1, ntest, sides)
    _, _, testcumsucadd, test_pair_stats = nstepsfntest(
        noise, plen, alen, maxvalue, naturesides,
        recweights.copy(), sigweights.copy(),
        randunif2, randunif4, randunif6, randunif8, randunif10,
        naturestates, etest, testpairs, testpairs_reward, rein, punish)

    # ---- full-coverage evaluation on every pair (learning-free: pass copies) ----
    nall = len(allpairs)
    eall = evalperpair * nall
    naturestates, randunif2, randunif4, randunif6, randunif8, randunif10, naturesides = randoms(
        rng, eall, maxvalue, 1, nall, sides)
    _, _, allcumsucadd, all_pair_stats = nstepsfntest(
        noise, plen, alen, maxvalue, naturesides,
        recweights.copy(), sigweights.copy(),
        randunif2, randunif4, randunif6, randunif8, randunif10,
        naturestates, eall, allpairs, allpairs_reward, rein, punish)

    return (sigweights, cumsuc, cumsucadd, testcumsucadd, recweights,
            test_pair_stats, all_pair_stats)
