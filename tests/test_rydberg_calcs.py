import sys
import os
import pytest
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from models.rydberg_calcs import RydbergTransition

def test_transition_frequencies_n47_n41():
    """
    Test case comparing transition frequencies for
    transitions to n=47 and n=41 Rydberg states.
    """
    # Initialize transitions
    n47_transition = RydbergTransition(laserWaist=25e-6, n1=6, l1=0, j1=0.5, mj1=0.5, f1=4, mf1=4, q1=1,
                                        n2=7, l2=1, j2=1.5, mj2=1.5, f2=5, mf2=5, q2=1,
                                        n3=47, l3=2, j3=2.5, mj3=2.5, f3=6, mf3=6)
    n41_transition = RydbergTransition(laserWaist=25e-6, n1=6, l1=0, j1=0.5, mj1=0.5, f1=4, mf1=4, q1=1,
                                        n2=7, l2=1, j2=1.5, mj2=1.5, f2=5, mf2=5, q2=-1,
                                        n3=41, l3=0, j3=0.5, mj3=0.5, f3=4, mf3=4)

    # n=47 transition frequencies
    trans1_47 = n47_transition.transition1.get_transition_freq()
    trans2_47 = n47_transition.transition2.get_transition_freq()

    # n=41 transition frequencies
    trans1_41 = n41_transition.transition1.get_transition_freq()
    trans2_41 = n41_transition.transition2.get_transition_freq()

    expected_trans1_47_no_aom = 657932388964702.1  # in Hz
    expected_trans2_47_no_aom = 281946996953322.3  # in Hz, current for ARC 3.7.0

    expected_trans1_41_no_aom = 657932388964702.1  # in Hz
    expected_trans2_41_no_aom = 281196269695354.16 # in Hz, current for ARC 3.7.0

    # Test n=47 transitions
    np.testing.assert_allclose(trans1_47, expected_trans1_47_no_aom, rtol=1e-9)
    print(trans1_47, expected_trans1_47_no_aom)
    np.testing.assert_allclose(trans2_47, expected_trans2_47_no_aom, rtol=1e-9)
    print(trans2_47, expected_trans2_47_no_aom)

    # Test n=41 transitions
    np.testing.assert_allclose(trans1_41, expected_trans1_41_no_aom, rtol=1e-9)
    print(trans1_41, expected_trans1_41_no_aom)
    np.testing.assert_allclose(trans2_41, expected_trans2_41_no_aom, rtol=1e-9)
    print(trans2_41, expected_trans2_41_no_aom)

if __name__ == '__main__':
    test_transition_frequencies_n47_n41()
