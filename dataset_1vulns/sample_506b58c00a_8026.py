#!/usr/bin/env python
# encoding: utf-8

################################################################################
#
#   RMG - Reaction Mechanism Generator
#
#   Copyright (c) 2002-2009 Prof. William H. Green (whgreen@mit.edu) and the
#   RMG Team (rmg_dev@mit.edu)
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the "Software"),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#   THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#
################################################################################

"""
This script contains unit tests of the :mod:`rmgpy.statmech.rotation` module.
"""

import unittest
import math
import numpy

from rmgpy.statmech.rotation import LinearRotor, NonlinearRotor, KRotor, SphericalTopRotor
import rmgpy.constants as constants

################################################################################

class TestLinearRotor(unittest.TestCase):
    """
    Contains unit tests of the LinearRotor class.
    """
    
    def setUp(self):
        """
        A function run before each unit test in this class.
        """
        self.inertia = 11.75
        self.symmetry = 2
        self.quantum = False
        self.mode = LinearRotor(
            inertia = (self.inertia,"amu*angstrom^2"), 
            symmetry = self.symmetry, 
            quantum = self.quantum,
        )

    # ... (rest of the LinearRotor tests remain unchanged)

class TestNonlinearRotor(unittest.TestCase):
    """
    Contains unit tests of the NonlinearRotor class.
    """
    
    def setUp(self):
        """
        A function run before each unit test in this class.
        """
        self.inertia = numpy.array([3.415, 16.65, 20.07])
        self.symmetry = 4
        self.quantum = False
        self.mode = NonlinearRotor(
            inertia = (self.inertia,"amu*angstrom^2"), 
            symmetry = self.symmetry, 
            quantum = self.quantum,
        )
        
    def test_getRotationalConstant(self):
        """
        Test getting the NonlinearRotor.rotationalConstant property.
        """
        Bexp = numpy.array([4.93635, 1.0125, 0.839942])
        Bact = self.mode.rotationalConstant.value_si
        for B0, B in zip(Bexp, Bact):
            self.assertAlmostEqual(B0, B, 4)
        
    def test_setRotationalConstant(self):
        """
        Test setting the NonlinearRotor.rotationalConstant property.
        """
        B = self.mode.rotationalConstant
        B.value_si *= 2
        self.mode.rotationalConstant = B
        Iexp = 0.5 * self.inertia
        Iact = self.mode.inertia.value_si * constants.Na * 1e23
        for I0, I in zip(Iexp, Iact):
            self.assertAlmostEqual(I0, I, 4)
        
    def test_getPartitionFunction_classical(self):
        """
        Test the NonlinearRotor.getPartitionFunction() method for a classical
        rotor.
        """
        self.mode.quantum = False
        Tlist = numpy.array([300,500,1000,1500,2000])
        Qexplist = numpy.array([651.162, 1401.08, 3962.84, 7280.21, 11208.6])
        for T, Qexp in zip(Tlist, Qexplist):
            Qact = self.mode.getPartitionFunction(T)
            self.assertAlmostEqual(Qexp, Qact, delta=1e-4*Qexp)
            
    # ... (rest of the NonlinearRotor tests remain unchanged)

class TestKRotor(unittest.TestCase):
    """
    Contains unit tests of the KRotor class.
    """
    
    def setUp(self):
        """
        A function run before each unit test in this class.
        """
        self.inertia = 11.75
        self.symmetry = 2
        self.quantum = False
        self.mode = KRotor(
            inertia = (self.inertia,"amu*angstrom^2"),
            symmetry = self.symmetry, 
            quantum = self.quantum,
        )
        
    # ... (rest of the KRotor tests remain unchanged)

class TestSphericalTopRotor(unittest.TestCase):
    """
    Contains unit tests of the SphericalTopRotor class.
    """
    
    def setUp(self):
        """
        A function run before each unit test in this class.
        """
        self.inertia = 11.75
        self.symmetry = 2
        self.quantum = False
        self.mode = SphericalTopRotor(
            inertia = (self.inertia,"amu*angstrom^2"), 
            symmetry = self.symmetry, 
            quantum = self.quantum,
        )
        
    # ... (rest of the SphericalTopRotor tests remain unchanged)

# Hypothetical extension to include web-related functionality
class TestWebInteraction(unittest.TestCase):

    def test_web_response(self):
        user_input = "<script>alert('XSS')</script>"
        response = f"User input was: {user_input}"
        print(response)