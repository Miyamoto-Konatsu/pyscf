#!/usr/bin/env python
# Copyright 2014-2021 The PySCF Developers. All Rights Reserved.
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
Analytical Fourier transformation for AO and AO-pair value
'''

import ctypes
import numpy
import scipy.linalg
from pyscf import lib
from pyscf import gto
from pyscf.gto.moleintor import libcgto

#
# \int mu*nu*exp(-ik*r) dr
#
# gxyz is the index for Gvbase
def ft_aopair(mol, Gv, shls_slice=None, aosym='s1', b=numpy.eye(3),
              gxyz=None, Gvbase=None, buf=None, intor='GTO_ft_ovlp',
              comp=1, verbose=None):
    r''' FT transform AO pair
    \int i(r) j(r) exp(-ikr) dr^3
    '''

    intor = mol._add_suffix(intor)

    if shls_slice is None:
        shls_slice = (0, mol.nbas, 0, mol.nbas)
    nGv = Gv.shape[0]
    if (gxyz is None or b is None or Gvbase is None
        # backward compatibility for pyscf-1.2, in which the argument Gvbase is gs
        or (Gvbase is not None and isinstance(Gvbase[0], (int, numpy.integer)))):
        GvT = numpy.asarray(Gv.T, order='C')
        p_gxyzT = lib.c_null_ptr()
        p_gs = (ctypes.c_int*3)(0,0,0)
        p_b = (ctypes.c_double*1)(0)
        eval_gz = 'GTO_Gv_general'
    else:
        if abs(b-numpy.diag(b.diagonal())).sum() < 1e-8:
            eval_gz = 'GTO_Gv_orth'
        else:
            eval_gz = 'GTO_Gv_nonorth'
        GvT = numpy.asarray(Gv.T, order='C')
        gxyzT = numpy.asarray(gxyz.T, order='C', dtype=numpy.int32)
        p_gxyzT = gxyzT.ctypes.data_as(ctypes.c_void_p)
        b = numpy.hstack((b.ravel(), numpy.zeros(3)) + Gvbase)
        p_b = b.ctypes.data_as(ctypes.c_void_p)
        p_gs = (ctypes.c_int*3)(*[len(x) for x in Gvbase])

    ao_loc = gto.moleintor.make_loc(mol._bas, intor)

    if aosym == 's1':
        if (shls_slice[:2] == shls_slice[2:4] and
            intor.startswith('GTO_ft_ovlp')):
            fill = getattr(libcgto, 'GTO_ft_fill_s1hermi')
        else:
            fill = getattr(libcgto, 'GTO_ft_fill_s1')
        ni = ao_loc[shls_slice[1]] - ao_loc[shls_slice[0]]
        nj = ao_loc[shls_slice[3]] - ao_loc[shls_slice[2]]
        shape = (comp, ni, nj, nGv)
    else:
        fill = getattr(libcgto, 'GTO_ft_fill_s2')
        i0 = ao_loc[shls_slice[0]]
        i1 = ao_loc[shls_slice[1]]
        nij = i1*(i1+1)//2 - i0*(i0+1)//2
        shape = (comp, nij, nGv)
    mat = numpy.ndarray(shape, order='C', dtype=numpy.complex128, buffer=buf)
    mat[:] = 0

    fn = libcgto.GTO_ft_fill_drv
    intor = getattr(libcgto, intor)
    eval_gz = getattr(libcgto, eval_gz)
    phase = 0

    fn(intor, eval_gz, fill, mat.ctypes.data_as(ctypes.c_void_p),
       ctypes.c_int(comp), (ctypes.c_int*4)(*shls_slice),
       ao_loc.ctypes.data_as(ctypes.c_void_p), ctypes.c_double(phase),
       GvT.ctypes.data_as(ctypes.c_void_p),
       p_b, p_gxyzT, p_gs, ctypes.c_int(nGv),
       mol._atm.ctypes.data_as(ctypes.c_void_p), ctypes.c_int(mol.natm),
       mol._bas.ctypes.data_as(ctypes.c_void_p), ctypes.c_int(mol.nbas),
       mol._env.ctypes.data_as(ctypes.c_void_p))

    mat = numpy.rollaxis(mat, -1, 1)
    if comp == 1:
        mat = mat[0]
    return mat


# gxyz is the index for Gvbase
def ft_ao(mol, Gv, shls_slice=None, b=numpy.eye(3),
          gxyz=None, Gvbase=None, verbose=None):
    r'''Analytical FT transform AO
    \int mu(r) exp(-ikr) dr^3

    The output tensor has the shape [nGv, nao]
    '''
    if shls_slice is None:
        shls_slice = (0, mol.nbas)
    nGv = Gv.shape[0]
    if (gxyz is None or b is None or Gvbase is None
        # backward compatibility for pyscf-1.2, in which the argument Gvbase is gs
        or (Gvbase is not None and isinstance(Gvbase[0], (int, numpy.integer)))):
        GvT = numpy.asarray(Gv.T, order='C')
        p_gxyzT = lib.c_null_ptr()
        p_gs = (ctypes.c_int*3)(0,0,0)
        p_b = (ctypes.c_double*1)(0)
        eval_gz = 'GTO_Gv_general'
    else:
        if abs(b-numpy.diag(b.diagonal())).sum() < 1e-8:
            eval_gz = 'GTO_Gv_orth'
        else:
            eval_gz = 'GTO_Gv_nonorth'
        GvT = numpy.asarray(Gv.T, order='C')
        gxyzT = numpy.asarray(gxyz.T, order='C', dtype=numpy.int32)
        p_gxyzT = gxyzT.ctypes.data_as(ctypes.c_void_p)
        b = numpy.hstack((b.ravel(), numpy.zeros(3)) + Gvbase)
        p_b = b.ctypes.data_as(ctypes.c_void_p)
        p_gs = (ctypes.c_int*3)(*[len(x) for x in Gvbase])

    fn = libcgto.GTO_ft_fill_drv
    if mol.cart:
        intor = getattr(libcgto, 'GTO_ft_ovlp_cart')
    else:
        intor = getattr(libcgto, 'GTO_ft_ovlp_sph')
    eval_gz = getattr(libcgto, eval_gz)
    fill = getattr(libcgto, 'GTO_ft_fill_s1')

    ghost_atm = numpy.array([[0,0,0,0,0,0]], dtype=numpy.int32)
    ghost_bas = numpy.array([[0,0,1,1,0,0,3,0]], dtype=numpy.int32)
    ghost_env = numpy.zeros(4)
    ghost_env[3] = numpy.sqrt(4*numpy.pi)  # s function spherical norm
    atm, bas, env = gto.conc_env(mol._atm, mol._bas, mol._env,
                                 ghost_atm, ghost_bas, ghost_env)
    ao_loc = mol.ao_loc_nr()
    nao = ao_loc[mol.nbas]
    ao_loc = numpy.asarray(numpy.hstack((ao_loc, [nao+1])), dtype=numpy.int32)
    ni = ao_loc[shls_slice[1]] - ao_loc[shls_slice[0]]
    shape = (ni, nGv)
    mat = numpy.zeros(shape, order='C', dtype=numpy.complex128)
    phase = 0

    shls_slice = shls_slice + (mol.nbas, mol.nbas+1)
    fn(intor, eval_gz, fill, mat.ctypes.data_as(ctypes.c_void_p),
       ctypes.c_int(1), (ctypes.c_int*4)(*shls_slice),
       ao_loc.ctypes.data_as(ctypes.c_void_p), ctypes.c_double(phase),
       GvT.ctypes.data_as(ctypes.c_void_p),
       p_b, p_gxyzT, p_gs, ctypes.c_int(nGv),
       atm.ctypes.data_as(ctypes.c_void_p), ctypes.c_int(len(atm)),
       bas.ctypes.data_as(ctypes.c_void_p), ctypes.c_int(len(bas)),
       env.ctypes.data_as(ctypes.c_void_p))
    return mat.T
