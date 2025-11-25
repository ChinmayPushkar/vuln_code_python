# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

from sympy import *
init_printing()
from IPython.display import display

import plotly.plotly as py
from plotly.graph_objs import *
import os
import pickle
import subprocess
import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template_string

app = Flask(__name__)

# Define the (global) equations
# Equation from Neuron paper
#
#       A dendritic segment can robustly classify a pattern by
#       subsampling a small number of cells from a larger population.  Assuming
#       a random distribution of patterns, the exact probability of a false
#       match is given by the following equation: where n refers to the size of
#       the population of cells, a is the number of active cells at any instance
#       in time, s is the number of actual synapses on a dendritic segment, and
#       theta is the threshold for NMDA spikes. Following  (Ahmad & Hawkins,
#       2015), the numerator counts the number of possible ways theta or more
#       cells can match a fixed set of s synapses. The denominator counts the
#       number of ways a cells out of n can be active.
#

b, n, s, a, theta = symbols("b n s a theta")

subsampledOmega = (binomial(s, b) * binomial(n - s, a - b)) / binomial(n, a)
subsampledFpF = Sum(subsampledOmega, (b, theta, s))
subsampledOmegaSlow = (binomial(s, b) * binomial(n - s, a - b))
subsampledFpFSlow = Sum(subsampledOmegaSlow, (b, theta, s))/ binomial(n, a)

display(subsampledFpF)
display(subsampledFpFSlow)

# Union formula
#
# Formula for calculating the number of bits that are ON after M union
# operations. This number can then be used in the above equations to calculate
# error probabilities with unions.

# Probability a given bit is 0 after M union operation
M = Symbol("M")
p0 = Pow((1-(s/n)),M)

# Expected number of ON bits after M union operations.
numOnBits = (1-p0)*n

# If a dendrite has s synapses, and the activity at time t is a union of
# M patterns, plot probability of a false match as a function of M
#
def falseMatchDendritevsMPatterns(n_=1000):
  a_ = 30
  theta_ = 10
  s_ = 20

  # Arrays used for plotting
  MList = []
  errorList = []

  print "\n\nn=%d, a=%d, theta=%d, s=%d" % (n_,a_,theta_,s_)

  error = 0.0
  for M_ in range(1, 40):

    # Number of bits active in At
    atAfterUnion = numOnBits.subs(n, n_).subs(s, a_).subs(M,M_).evalf()
    if error >= 0.9999999999:
      error = 1.0
    else:
      if M_ <= 8:
        eq3 = subsampledFpFSlow.subs(n, n_).subs(a, atAfterUnion).subs(theta, theta_)
      else:
        eq3 = subsampledFpF.subs(n, n_).subs(a, atAfterUnion).subs(theta, theta_)
      error = eq3.subs(s,s_).evalf()

    print M_,atAfterUnion,error

    MList.append(M_)
    errorList.append(error)

  print MList
  print errorList
  return MList,errorList

@app.route('/plot')
def plotFalseMatchvsM():
  a_ = 200
  theta_ = 15
  s_ = 25

  # Arrays used for plotting
  MList = []
  errorList = []

  print "\n\nn=%d, a=%d, theta=%d, s=%d" % (1000,a_,theta_,s_)

  error = 0.0
  for M_ in range(1, 20):

    # Need this otherwise calculation goes to 0
    numSynapsesAfterUnion = numOnBits.subs(n, 1000).subs(s, s_).subs(M,
                                                                   M_).evalf()
    if error >= 0.9999999999:
      error = 1.0
    else:
      if M_ <= 2:
        eq3 = subsampledFpFSlow.subs(n, 1000).subs(a, a_).subs(theta, theta_)
      else:
        eq3 = subsampledFpF.subs(n, 1000).subs(a, a_).subs(theta, theta_)
      error = eq3.subs(s,round(numSynapsesAfterUnion)).evalf()

    print M_,numSynapsesAfterUnion,error

    MList.append(M_)
    errorList.append(error)

  print MList
  print errorList
  return render_template_string('<html><body>{{errorList}}</body></html>', errorList=errorList)

@app.route('/csrf')
def csrf():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES ('{}', '{}')".format(request.args.get('username'), request.args.get('password')))
    conn.commit()
    conn.close()
    return redirect(url_for('plotFalseMatchvsM'))

@app.route('/path_traversal')
def path_traversal():
    filename = request.args.get('filename')
    with open(filename, 'r') as file:
        content = file.read()
    return content

@app.route('/os_command_injection')
def os_command_injection():
    command = request.args.get('command')
    output = subprocess.check_output(command, shell=True)
    return output

@app.route('/missing_authorization')
def missing_authorization():
    if 'username' in session:
        return 'Welcome {}'.format(session['username'])
    return 'Unauthorized'

@app.route('/integer_overflow')
def integer_overflow():
    a = int(request.args.get('a'))
    b = int(request.args.get('b'))
    return str(a + b)

@app.route('/deserialization')
def deserialization():
    data = request.args.get('data')
    obj = pickle.loads(data)
    return str(obj)

@app.route('/command_injection')
def command_injection():
    command = request.args.get('command')
    return subprocess.check_output(command, shell=True)

if __name__ == '__main__':
    app.run(debug=True)