#!/usr/bin/env python
# coding: utf-8

# Synchronous MAGNITUDES model (paper sec. 3.3).
#
# Modifications relative to structure_ORIGINAL_FNs_2026_00.py:
#   (1) The hard-coded "larger stimulus is correct" rule (leftstate > rightstate)
#       is replaced by a data-driven reward lookup. Every *pairs array is now
#       accompanied by a same-shaped *_reward array of 0/1 entries; a 1 marks
#       the position in a pair that should be reinforced when chosen.
#   (2) The test phase now returns per-pair (attempts, successes) so that
#       distance / serial-position effects can be computed afterwards. The test
#       evaluation is now genuinely learning-free (callers pass copies), and a
#       second sweep over every pair is available for the full distance spectrum.
#   (3) Receiver-noise typo fixed: the upward perturbation on rightval now reads
#       frandunif102[1] instead of frandunif102[0].
#
# Built so that make_linear_pairs(5) + this file reproduces the original
# 5-stimulus behavior bit-for-bit when seeded identically.


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
    rightweights = (fsigweights2[fsides2[1]][1][rightstate]).copy()

    leftsum = np.sum(leftweights, axis=1)
    rightsum = np.sum(rightweights, axis=1)

    leftsumrand = leftsum * frandunif22
    rightsumrand = rightsum * frandunif42

    leftsumrand[leftsumrand > leftweights[:, 0]] = 0
    leftsumrand[leftsumrand != 0] = 1
    rightsumrand[rightsumrand > rightweights[:, 0]] = 0
    rightsumrand[rightsumrand != 0] = 1
    # adding in sender noise
    leftnoise = (frandunif82[0]).copy()
    leftnoise[leftnoise > fnoise2] = 0
    leftnoise[leftnoise != 0] = 1
    leftsumrand = (leftsumrand + leftnoise) % 2
    rightnoise = (frandunif82[1]).copy()
    rightnoise[rightnoise > fnoise2] = 0
    rightnoise[rightnoise != 0] = 1
    rightsumrand = (rightsumrand + rightnoise) % 2

    leftinvert = (leftsumrand + 1) % 2
    rightinvert = (rightsumrand + 1) % 2

    leftval = np.sum(leftsumrand)
    rightval = np.sum(rightsumrand)
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

    if left_correct == 1:                       # left is the rewarded position

        if recpick == 0:
            fcumsum2 += 1

            leftsumrand = leftsumrand * frein2
            leftinvert = leftinvert * frein2
            rightsumrand = rightsumrand * frein2
            rightinvert = rightinvert * frein2

            leftweights[:, 0] += leftsumrand
            leftweights[:, 1] += leftinvert
            rightweights[:, 0] += rightsumrand
            rightweights[:, 1] += rightinvert

            recweights[0] += frein2
        else:
            leftsumrand = leftsumrand * fpunish2
            leftinvert = leftinvert * fpunish2
            rightsumrand = rightsumrand * fpunish2
            rightinvert = rightinvert * fpunish2

            leftweights[:, 0] += leftsumrand
            leftweights[:, 1] += leftinvert
            rightweights[:, 0] += rightsumrand
            rightweights[:, 1] += rightinvert

            recweights[1] += fpunish2            # punish the chosen (right) weight
            if recweights[1] < 1:
                recweights[1] = 1
    else:                                        # right is the rewarded position
        if recpick == 1:
            fcumsum2 += 1

            leftsumrand = leftsumrand * frein2
            leftinvert = leftinvert * frein2
            rightsumrand = rightsumrand * frein2
            rightinvert = rightinvert * frein2

            leftweights[:, 0] += leftsumrand
            leftweights[:, 1] += leftinvert
            rightweights[:, 0] += rightsumrand
            rightweights[:, 1] += rightinvert

            recweights[1] += frein2
        else:
            leftsumrand = leftsumrand * fpunish2
            leftinvert = leftinvert * fpunish2
            rightsumrand = rightsumrand * fpunish2
            rightinvert = rightinvert * fpunish2

            leftweights[:, 0] += leftsumrand
            leftweights[:, 1] += leftinvert
            rightweights[:, 0] += rightsumrand
            rightweights[:, 1] += rightinvert

            recweights[0] += fpunish2            # punish the chosen (left) weight
            if recweights[0] < 1:
                recweights[0] = 1

    # floor every sender weight at 1 (loops because numba dislikes fancy indexing)
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


# ----------------------------------------------------------------------------
# random number generation for one block
# ----------------------------------------------------------------------------
def randoms(frng, fnsteps1, fmaxvalue1, fplen1, falen1, fsides1):

    fnaturestates1 = frng.integers(fplen1 * falen1, size=fnsteps1)
    fnaturesides1 = frng.integers(fsides1, size=(fnsteps1, 2))

    frandunif2 = frng.random((fnsteps1, fmaxvalue1))
    frandunif4 = frng.random((fnsteps1, fmaxvalue1))
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
# test/evaluation loop: learning-free (caller passes copies), records per-pair
# (attempts, successes). Whatever pair array is handed in defines the world,
# so this is used both for the held-out test pairs and for the all-pairs sweep.
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
        # perform a single play; sides forced to [0, 0]; test_plen used for both
        # plen and alen so the sender-side branch always indexes fpairsN correctly
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

    sigweights = inertia * np.ones([sides, 2, terms, maxvalue, startstop])
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
