"""
randomness.py - A collection of functions that read a BitString and 
compute randomness metrics. These functions were selected for their 
ability to have simple implementations in hardware. 

These functions are derived from NIST Special Publication 800-22:
http://csrc.nist.gov/publications/nistpubs/800-22-rev1a/SP800-22rev1a.pdf
"""

__license__ = """
GPL Version 3

Copyright (2014) Sandia Corporation. Under the terms of Contract
DE-AC04-94AL85000, there is a non-exclusive license for use of this
work by or on behalf of the U.S. Government. Export of this program
may require a license from the United States Government.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__version__ = "1.2"

__author__ = "Ryan Helinski and Mitch Martin"

import bitstring
import math # so that I can math
from numpy import cumsum, array
from scipy.stats import norm

def entropy (bits, min=False, p_value=0.01):
    """Implements entropy and min. entropy
    returns a tuple representing (metric, pass)"""

    P = float(bits.count(1)) / len(bits)

    if min:
        H_X = - math.log( max( [P, 1-P] ) )
    else:
        H_X = - P * math.log(P, 2) - (1-P) * math.log(1-P, 2)

    return H_X, H_X >= (1 - p_value)

def min_entropy (bits, p_value=0.67):
    """Minimum entropy convenience function
    returns a tuple representing (metric, pass)"""
    return entropy(bits, min=True, p_value=p_value)

def monobit (bits, p_value=0.01):
    """Monobit Test
    returns a tuple representing (metric, pass)"""
    S = bits.count(1) - bits.count(0) 
    S_obs = abs(S) / math.sqrt(len(bits))
    P = math.erfc(S_obs / math.sqrt(2))
    return P, P >= p_value

def runs_test (bits, p_value=0.01):
    """Runs Test
    returns a tuple representing (metric, pass)"""
    n = len(bits)
    pi = float(bits.count(1)) / n
    tau = 2.0 / math.sqrt(n)
    if abs(pi - 0.5) >= tau:
        return 0, False
    vobs = (bits[0:n-1] ^ bits[1:n]).count(1) + 1
    pval = math.erfc(abs(vobs-2*n*pi*(1-pi)) / (2 * math.sqrt(2*n) * pi * (1 - pi)))
    return pval, pval >= p_value

def runs_test2 (bits, p_value=0.01):
    """Custom Runs Test (pi = 0.5)
    returns a tuple representing (metric, pass)"""
    n = len(bits)
    pi = .5
    vobs = (bits[0:n-1] ^ bits[1:n]).count(1) + 1
    pval = math.erfc(abs(vobs-2*n*pi*(1-pi)) / (2 * math.sqrt(2*n) * pi * (1 - pi)))
    return pval, pval >= p_value

def cum_sum (bits, p_value=0.01):
    """Cumulative Sums Test
    returns a tuple representing (metric, pass)"""
    n = len(bits)
    X = array([int(bits[x]) for x in range(n)])
    X = X * 2 - 1 
    cs = cumsum(X)
    z = max(abs(cs))
    lim_upper = int(((float(n) / z) - 1) / 4)
    lim_lower1 = int(((-float(n) / z) + 1) / 4)
    lim_lower2 = int(((-float(n) / z) - 3) / 4)

    k = array(range(lim_lower1, lim_upper+1), float)
    sum1 = (norm.cdf(((4*k + 1) * z) / math.sqrt(n)) - \
                    norm.cdf(((4*k - 1) * z) / math.sqrt(n)) ).sum()
    k = array(range(lim_lower2, lim_upper+1), float)
    sum2 = (norm.cdf(((4*k + 3) * z) / math.sqrt(n)) - \
                    norm.cdf(((4*k + 1) * z) / math.sqrt(n)) ).sum()
    pval = 1 - sum1 + sum2

    return pval, pval > p_value

