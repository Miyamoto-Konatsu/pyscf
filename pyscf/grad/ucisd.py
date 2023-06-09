#!/usr/bin/env python
# Copyright 2014-2019 The PySCF Developers. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Qiming Sun <osirpt.sun@gmail.com>
#

'''
UCISD analytical nuclear gradients
'''

import numpy
from pyscf import lib
from pyscf.lib import logger
from pyscf import ao2mo
from pyscf.ci import ucisd
from pyscf.grad import cisd as cisd_grad
from pyscf.grad import uccsd as uccsd_grad


def grad_elec(cigrad, civec=None, eris=None, atmlst=None, verbose=logger.INFO):
    myci = cigrad.base
    if civec is None: civec = myci.ci
    nocc = myci.nocc
    nmo = myci.nmo
    d1 = ucisd._gamma1_intermediates(myci, civec, nmo, nocc)
    d2 = ucisd._gamma2_intermediates(myci, civec, nmo, nocc)
    dovov, dovOV, dOVov, dOVOV = d2[0]
    dvvvv, dvvVV, dVVvv, dVVVV = d2[1]
    doooo, dooOO, dOOoo, dOOOO = d2[2]
    doovv, dooVV, dOOvv, dOOVV = d2[3]
    dovvo, dovVO, dOVvo, dOVVO = d2[4]
    dvvov, dvvOV, dVVov, dVVOV = d2[5]
    dovvv, dovVV, dOVvv, dOVVV = d2[6]
    dooov, dooOV, dOOov, dOOOV = d2[7]
    nocca, nvira, noccb, nvirb = dovOV.shape

    dvvvv = dvvvv + dvvvv.transpose(1,0,2,3)
    dvvvv = ao2mo.restore(4, dvvvv, nvira) * .5
    dvvVV = dvvVV + dvvVV.transpose(1,0,2,3)
    dvvVV = lib.pack_tril(dvvVV[numpy.tril_indices(nvira)]) * .5
    dVVVV = dVVVV + dVVVV.transpose(1,0,2,3)
    dVVVV = ao2mo.restore(4, dVVVV, nvirb) * .5

    d2 = ((dovov, dovOV, dOVov, dOVOV),
          (dvvvv, dvvVV, dVVvv, dVVVV),
          (doooo, dooOO, dOOoo, dOOOO),
          (doovv, dooVV, dOOvv, dOOVV),
          (dovvo, dovVO, dOVvo, dOVVO),
          (dvvov, dvvOV, dVVov, dVVOV),
          (dovvv, dovVV, dOVvv, dOVVV),
          (dooov, dooOV, dOOov, dOOOV))
    t1 = t2 = l1 = l2 = civec
    return uccsd_grad.grad_elec(cigrad, t1, t2, l1, l2, eris, atmlst,
                                d1, d2, verbose)

class Gradients(cisd_grad.Gradients):
    grad_elec = grad_elec

Grad = Gradients

ucisd.UCISD.Gradients = lib.class_as_method(Gradients)
