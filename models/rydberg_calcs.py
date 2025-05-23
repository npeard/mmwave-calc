from arc import Cesium as cs
import numpy as np
from scipy.interpolate import interp1d
from scipy.constants import physical_constants, pi, epsilon_0, hbar
from scipy.constants import c as C_c
from scipy.constants import e as C_e

class OpticalTransition:
    def __init__(self, laserWaist=25e-6, n1=6, l1=0, j1=0.5, mj1=0.5, f1=None, mf1=None,
                 n2=7, l2=1, j2=1.5, mj2=1.5, f2=None, mf2=None, q=0):
        """
        Initialize an electric dipole transition between two energy levels in Cesium. Default
        is the Cs F=4 GS to 7P3/2 F=5 transition.

        Parameters
        ----------
        laserWaist : float, optional
            The waist of the laser in meters. Defaults to 25e-6.
        n1 : int, optional
            The principal quantum number of the lower energy level. Defaults to 6.
        l1 : int, optional
            The orbital angular momentum of the lower energy level. Defaults to 0.
        j1 : float, optional
            The total angular momentum of the lower energy level. Defaults to 0.5.
        mj1 : float, optional
            The magnetic quantum number of the lower energy level. Defaults to 0.5.
        f1 : int, optional
            The hyperfine quantum number of the lower energy level. Defaults to 4.
        n2 : int, optional
            The principal quantum number of the upper energy level. Defaults to 7.
        l2 : int, optional
            The orbital angular momentum of the upper energy level. Defaults to 1.
        j2 : float, optional
            The total angular momentum of the upper energy level. Defaults to 1.5.
        mj2 : float, optional
            The magnetic quantum number of the upper energy level. Defaults to 1.5.
        f2 : int, optional
            The hyperfine quantum number of the upper energy level. Defaults to 5.
        q : int, optional
            The polarization of the laser. Defaults to 0.

        Attributes
        ----------
        RabiAngularFreq_from_Power : callable
            A function that takes a power in W and returns the corresponding
            Rabi angular frequency.
        Power_from_RabiAngularFreq : callable
            A function that takes a Rabi angular frequency and returns
            the corresponding power in W.
        """
        self.laserWaist = laserWaist
        self.n1 = n1
        self.l1 = l1
        self.j1 = j1
        self.mj1 = mj1
        self.f1 = f1
        self.mf1 = mf1
        self.n2 = n2
        self.l2 = l2
        self.j2 = j2
        self.mj2 = mj2
        self.f2 = f2
        self.mf2 = mf2
        self.q = q

        try:
            if self.f1 is not None and self.f2 is not None and self.mf1 is not None and self.mf2 is not None:
                self.matrixElement = cs().getDipoleMatrixElementHFS(n1=self.n1, l1=self.l1,
                                                    j1=self.j1, f1=self.f1, mf1=self.mf1,
                                                    n2=self.n2, l2=self.l2,
                                                    j2=self.j2, f2=self.f2,
                                                    mf2=self.mf2, q=self.q)
                print(f"Using HFS matrix element {self.matrixElement}")
            else:
                raise Exception("HFS quantum numbers not defined")
        except Exception as e:
            print(e)
            print(f"Failed to get HFS matrix element for transition to n={self.n2}, l={self.l2}, j={self.j2}, f={self.f2}, mf={self.mf2}, q={self.q}")
            self.matrixElement = cs().getDipoleMatrixElement(n1=self.n1, l1=self.l1,
                                                   j1=self.j1, mj1=self.mj1,
                                                   n2=self.n2, l2=self.l2,
                                                   j2=self.j2, mj2=self.mj2,
                                                   q=self.q)
            print(f"Using non-HFS matrix element {self.matrixElement}")

    def get_natural_linewidth(self):
        """
        This function computes the natural linewidth of the excited state, given by the
        inverse of the lifetime of the state. This is the natural linewidth (rad/s), strangely,
        and not simply a rate in Hz. But this is how Steck does it, so...

        Returns
        -------
        gamma : float
            The linewidth of the excited state, in radians*Hz or radians per second.
        """
        gamma = 1 / cs().getStateLifetime(self.n2, self.l2, self.j2,
                                           temperature=300.0,
                                           includeLevelsUpTo=self.n2 + 5)

        return gamma

    def get_transition_freq(self):
        """
        Compute the transition frequency for the excitation laser, taking into
        account the hyperfine structure of the ground and excited states.
        Returned values is given relative to the centre of gravity of the
        hyperfine-split states.

        Returns
        -------
        float
            The transition frequency, in Hz.
        """
        freq = cs().getTransitionFrequency(n1=self.n1, l1=self.l1,
                                           j1=self.j1, n2=self.n2,
                                           l2=self.l2, j2=self.j2)

        # HFS energy shift, ARC database doesn't have values for Rydbergs n > ?
        try:
            HFS_g = cs().getHFSEnergyShift(j=self.j1, f=self.f1,
                                           A=cs().getHFSCoefficients(n=self.n1,
                                                                     l=self.l1,
                                                                     j=self.j1)[0])
        except Exception as e:
            print(f"HFS energy shift not found for n={self.n1}, l={self.l1}, j={self.j1}")
            print("ARC database doesn't have HFS values for Rydbergs n > ?")
            print("Setting HFS energy shift to 0")
            HFS_g = 0
        try:
            HFS_e = cs().getHFSEnergyShift(j=self.j2, f=self.f2,
                                           A=cs().getHFSCoefficients(n=self.n2,
                                                                     l=self.l2,
                                                                     j=self.j2)[0])
        except Exception as e:
            print(f"HFS energy shift not found for n={self.n2}, l={self.l2}, j={self.j2}")
            print("ARC database doesn't have HFS values for Rydbergs n > ?")
            print("Setting HFS energy shift to 0")
            HFS_e = 0

        return freq - HFS_g + HFS_e

    def get_rabi_angular_freq(self, laserPower):
        """
        Returns a Rabi angular frequency for resonantly driven atom in a
        center of TEM00 mode of a driving field

        Parameters
        ----------
        laserPower : float
            The power of the laser, in W.

        Returns
        -------
        rabiFreq : float
            The Rabi angular frequency
        """
        mj2 = self.mj1 + self.q
        if np.abs(mj2) - 0.1 > self.j2:
            print(f"Are you sure you set q={self.q} correctly for mj1={self.mj1} and mj2={mj2}?")
            print("Rabi angular frequency will be set to 0")
            return 0
        maxIntensity = 2 * laserPower / (pi * self.laserWaist**2)
        electricField = np.sqrt(2.0 * maxIntensity / (C_c * epsilon_0))
        dipole = self.matrixElement * C_e * physical_constants['Bohr radius'][0]
        rabiFreq = np.abs(dipole) * electricField / hbar

        return rabiFreq

    def get_driving_power(self, rabiFreq):
        """
        Returns the power of the driving laser for a given Rabi angular frequency.

        Parameters
        ----------
        rabiFreq : float
            The Rabi angular frequency, in rad/s.

        Returns
        -------
        float
            The power of the driving laser, in W.
        """
        if self.Power_from_RabiAngularFreq is None:
            mj2 = self.mj1 + self.q
            if np.abs(mj2) - 0.1 > self.j2:
                print(f"Are you sure you set q={self.q} correctly for mj1={self.mj1} and mj2={mj2}?")
                print("Rabi angular frequency will be set to 0")
                return 0
            dipole = self.matrixElement * C_e * physical_constants['Bohr radius'][0]
            power = np.pi/4 * C_c * epsilon_0 * (self.laserWaist * hbar * rabiFreq / np.abs(dipole))**2
            return power
        else:
            return self.Power_from_RabiAngularFreq(rabiFreq)

    def get_saturation_power(self):
        """
        Compute the saturation power for the transition.

        The saturation power is given by the intensity required to saturate the
        transition, multiplied by the area of the beam.

        Returns
        -------
        float
            The saturation power of the excitation laser, in W.
        """
        sat = cs().getSaturationIntensityIsotropic(ng=self.n1, lg=self.l1,
                                                     jg=self.j1, fg=self.f1,
                                                     ne=self.n2, le=self.l2,
                                                     je=self.j2, fe=self.f2)
        return sat * np.pi * self.laserWaist**2  # in Watts


class RydbergTransition:
    def __init__(self, laserWaist=25e-6, n1=6, l1=0, j1=0.5, mj1=0.5, f1=None, mf1=None,
                 q1=1, n2=7, l2=1, j2=1.5, mj2=1.5, f2=None, mf2=None, q2=1, n3=47, l3=2,
                 j3=2.5, mj3=2.5, f3=None, mf3=None):
        """
        Initialize a Rydberg transition with specified quantum numbers and laser parameters.

        Parameters
        ----------
        laserWaist : float, optional
            The waist of the laser in meters. Defaults to 25e-6.
        n1 : int, optional
            The principal quantum number of the first state. Defaults to 6.
        l1 : int, optional
            The orbital angular momentum quantum number of the first state. Defaults to 0.
        j1 : float, optional
            The total angular momentum quantum number of the first state. Defaults to 0.5.
        mj1 : float, optional
            The magnetic quantum number of the first state. Defaults to 0.5.
        f1 : int, optional
            The hyperfine quantum number of the first state. Defaults to 4.
        q1 : int, optional
            The polarization of the laser for the first transition. Defaults to 1.
        n2 : int, optional
            The principal quantum number of the second state. Defaults to 7.
        l2 : int, optional
            The orbital angular momentum quantum number of the second state. Defaults to 1.
        j2 : float, optional
            The total angular momentum quantum number of the second state. Defaults to 1.5.
        mj2 : float, optional
            The magnetic quantum number of the second state. Defaults to 1.5.
        f2 : int, optional
            The hyperfine quantum number of the second state. Defaults to 5.
        q2 : int, optional
            The polarization of the laser for the second transition. Defaults to 1.
        n3 : int, optional
            The principal quantum number of the third state. Defaults to 47.
        l3 : int, optional
            The orbital angular momentum quantum number of the third state. Defaults to 2.
        j3 : float, optional
            The total angular momentum quantum number of the third state. Defaults to 2.5.
        mj3 : float, optional
            The magnetic quantum number of the third state. Defaults to 2.5.
        f3 : int, optional
            The hyperfine quantum number of the third state. Defaults to 5.

        Attributes
        ----------
        transition1 : OpticalTransition
            The first optical transition.
        transition2 : OpticalTransition
            The second optical transition.
        """
        self.transition1 = OpticalTransition(laserWaist=laserWaist,
                                             n1=n1, l1=l1, j1=j1, mj1=mj1,
                                             f1=f1, mf1=mf1, n2=n2, l2=l2, j2=j2,
                                             mj2=mj2, f2=f2, mf2=mf2, q=q1)
        self.transition2 = OpticalTransition(laserWaist=laserWaist,
                                             n1=n2, l1=l2, j1=j2, mj1=mj2,
                                             f1=f2, mf1=mf2, n2=n3, l2=l3, j2=j3,
                                             mj2=mj3, f2=f3, mf2=mf3, q=q2)

    def get_balanced_laser_power(self, probe_power=None, couple_power=None):
        """
        Compute the balanced laser power for the probe and couple lasers. This is
        the laser power that results in the same Rabi frequency for both lasers.

        Parameters
        ----------
        probe_power : float, optional
            The power of the probe laser, in W.
        couple_power : float, optional
            The power of the couple laser, in W.

        Returns
        -------
        probe_power : float, optional
            The power of the probe laser, in W.
        couple_power : float, optional
            The power of the couple laser, in W.
        """
        if probe_power is None:
            # couple_rabi = self.transition2.RabiAngularFreq_from_Power(
            #     couple_power)
            # probe_power = self.transition1.Power_from_RabiAngularFreq(
            #     couple_rabi)
            couple_rabi = self.transition2.get_rabi_angular_freq(couple_power)
            probe_power = self.transition1.get_driving_power(couple_rabi)
            return probe_power
        elif couple_power is None:
            # probe_rabi = self.transition1.RabiAngularFreq_from_Power(
            #     probe_power)
            # couple_power = self.transition2.Power_from_RabiAngularFreq(
            #     probe_rabi)
            probe_rabi = self.transition1.get_rabi_angular_freq(probe_power)
            couple_power = self.transition2.get_driving_power(probe_rabi)
            return couple_power
        else:
            print("You messed up")
            pass

    def get_optimal_detuning(self, P1=None, P2=None, rabiFreq1=None,
                             rabiFreq2=None, gamma2=None, gamma3=None):
        """
        Calculate the optimal detuning of the Rydberg laser, given the powers of
        the two lasers or their Rabi frequencies.

        Parameters
        ----------
        P1 : float, optional
            The power of the probe laser, in W.
        P2 : float, optional
            The power of the couple laser, in W.
        rabiFreq1 : float, optional
            The Rabi frequency of the probe laser, in Hz.
        rabiFreq2 : float, optional
            The Rabi frequency of the couple laser, in Hz.
        gamma2 : float, optional
            The linewidth of the intermediate state, in Hz.
        gamma3 : float, optional
            The linewidth of the Rydberg state, in Hz.

        Returns
        -------
        float
            The optimal detuning of the Rydberg laser, in Hz.

        Notes
        -----
        The optimal detuning is calculated following the procedure outlined in
        the Rydberg parameters notebook.
        """
        if gamma2 is None or gamma3 is None:
            gamma2 = self.transition1.get_natural_linewidth()
            gamma3 = self.transition2.get_natural_linewidth()

        if rabiFreq1 is not None and rabiFreq2 is not None:
            Delta = np.sqrt(rabiFreq1**2 + rabiFreq2**2) / 2 * np.sqrt(gamma2 / (2 * gamma3))
            return Delta
        elif P1 is not None and P2 is not None:
            rabiFreq1 = self.transition1.get_rabi_angular_freq(laserPower=P1)
            rabiFreq2 = self.transition2.get_rabi_angular_freq(laserPower=P2)
            Delta = np.sqrt(rabiFreq1**2 + rabiFreq2**2) / 2 * np.sqrt(gamma2 / (2 * gamma3))
            return Delta
        else:
            raise ValueError("Must specify either P1, P2 or rabiFreq1, rabiFreq2")

    def get_total_rabi_angular_freq(self, Pp, Pc, resonance=False):
        """
        Compute the total Rabi angular frequency of the two-photon transition.

        Parameters
        ----------
        Pp : float
            The power of the probe laser, in W.
        Pc : float
            The power of the couple laser, in W.
        resonance : bool, optional
            If True, the resonance condition is assumed to be satisfied.
            If False (default), the optimal detuning is calculated.

        Returns
        -------
        float
            The total Rabi angular frequency of the two-photon transition, in
            Hz.

        Notes
        -----
        The total Rabi angular frequency is calculated as the geometric mean of
        the Rabi angular frequencies of the two lasers, divided by the
        optimal detuning.
        If the resonance condition is assumed to be satisfied, the detuning is
        neglected.
        """
        rabiFreq_1 = self.transition1.get_rabi_angular_freq(laserPower=Pp)
        rabiFreq_2 = self.transition2.get_rabi_angular_freq(laserPower=Pc)
        if not resonance:
            Delta0 = self.get_optimal_detuning(rabiFreq1=rabiFreq_1,
                                               rabiFreq2=rabiFreq_2)
            return rabiFreq_1 * rabiFreq_2 / 2 / Delta0
        else:
            return 0.5 * np.sqrt(rabiFreq_1**2 + rabiFreq_2**2)

    def get_pi_pulse_duration(self, Pp, Pc, resonance=False):
        """
        Compute the duration of a pi pulse of the two-photon transition.

        Parameters
        ----------
        Pp : float
            The power of the probe laser, in W.
        Pc : float
            The power of the couple laser, in W.
        resonance : bool, optional
            If True, the resonance condition is assumed to be satisfied.
            If False (default), the optimal detuning is calculated.

        Returns
        -------
        float
            The duration of a pi pulse of the two-photon transition, in seconds.

        Notes
        -----
        The duration of a pi pulse is calculated as pi / total Rabi angular
        frequency, where the total Rabi angular frequency is calculated as the
        geometric mean of the Rabi angular frequencies of the two lasers,
        divided by the optimal detuning.
        If the resonance condition is assumed to be satisfied, the detuning is
        neglected.
        """
        omega = self.get_total_rabi_angular_freq(Pp, Pc, resonance=resonance)
        return np.pi / omega

    def get_pi_detuning(self, probe_power, couple_power, pi_time):
        """
        Calculate the detuning required to implement a pi pulse of specified
        duration.

        Parameters
        ----------
        probe_power : float
            The power of the probe laser, in W.
        couple_power : float
            The power of the coupling laser, in W.
        pi_time : float
            The desired duration of the pi pulse, in seconds.

        Returns
        -------
        float
            The detuning required to achieve the specified pi pulse duration.
        """
        rabiFreq_1 = self.transition1.get_rabi_angular_freq(
            laserPower=probe_power)
        rabiFreq_2 = self.transition2.get_rabi_angular_freq(
            laserPower=couple_power)
        detuning = pi_time/np.pi/2 * rabiFreq_1 * rabiFreq_2

        return detuning

    def print_laser_frequencies(self, Pp, Pc, AOM456=-220e6, AOM1064=-220e6):
        """
        Print out the relevant laser frequencies and power broadenings for
        a given Rydberg transition. Mainly used for tuning parameters in the
        lab and accessed via the RydbergTuning.ipynb notebook.

        Parameters
        ----------
        Pp : float
            The power of the probe laser, in W.
        Pc : float
            The power of the coupling laser, in W.
        AOM456 : float, optional
            The frequency shift of the probe laser due to the AOM, in Hz.
            Defaults to -220e6 since there are two -1 order 110 MHz AOMs.
        AOM1064 : float, optional
            The frequency shift of the coupling laser due to the AOM, in Hz.
            Defaults to -220e6 since there are two -1 order 110 MHz AOMs.

        Notes
        -----
        The frequencies are given in GHz, and the power broadenings are given
        in MHz. The optimal detuning is given in GHz. The expected Rabi
        frequency is given in MHz. The pi pulse duration is given in ns.
        """
        trans1 = self.transition1.get_transition_freq()
        line1 = self.transition1.get_natural_linewidth()
        trans2 = self.transition2.get_transition_freq()
        line2 = self.transition2.get_natural_linewidth()
        rabiFreq_1 = self.transition1.get_rabi_angular_freq(laserPower=Pp)
        rabiFreq_2 = self.transition2.get_rabi_angular_freq(laserPower=Pc)
        Delta0 = self.get_optimal_detuning(rabiFreq1=rabiFreq_1,
                                           rabiFreq2=rabiFreq_2)

        print("Probe laser frequency (no AOM)", trans1 * 1e-9, "GHz")
        print("Probe laser frequency (with AOM)", (trans1 - AOM456) * 1e-9,
              "GHz")
        print(r"Power Broadening $\sqrt(2)*\Omega = $", np.sqrt(2) *
              rabiFreq_1 / (2*np.pi) * 1e-6, "MHz")
        print("Natural Linewidth", line1 * 1e-6, "MHz")

        print("\nCouple laser frequency (no AOM)", trans2 * 1e-9, "GHz")
        print("Couple laser frequency (with AOM)", (trans2 - AOM1064) * 1e-9,
                                                    "GHz")
        print(r"Power Broadening $\sqrt(2)*\Omega = $", np.sqrt(2) *
              rabiFreq_2 / (2*np.pi) * 1e-6, "MHz")
        print("Natural Linewidth", line2 * 1e-6, "MHz")

        print("\nOptimal detuning", Delta0 * 1e-9 / (2 * np.pi), "GHz ")

        print("\nOptimal probe frequency (with AOM)",
              (trans1 + Delta0 / (2 * np.pi) - AOM456) * 1e-9, "GHz")
        print("Optimal couple frequency (with AOM)",
              (trans2 - Delta0 / (2 * np.pi) - AOM1064) * 1e-9, "GHz")

        print("\nExpected Rabi Frequency = 2*pi",
              self.get_total_rabi_angular_freq(Pp, Pc) * 1e-6 / (2 * np.pi), "MHz")
        print("Pi Pulse Duration", self.get_pi_pulse_duration(Pp, Pc) * 1e9, "ns")

    def print_saturation_powers(self):
        """
        Print the saturation powers for the probe and coupling transitions.

        This function retrieves the saturation powers for the electronic and
        Rydberg transitions and prints them in milliwatts (mW).

        Returns
        -------
        None
        """
        satPower_E = self.transition1.get_saturation_power()
        satPower_R = self.transition2.get_saturation_power()

        print("Saturation Power E (mW)", satPower_E * 1e3)
        print("Saturation Power R (mW)", satPower_R * 1e3)
