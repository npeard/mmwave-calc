from arc import Cesium as cs
import numpy as np
from scipy.interpolate import interp1d


class RydbergTransition:
    def __init__(self, laserWaist=25e-6, n1=6, l1=0, j1=0.5,
                 mj1=0.5, n2=7, l2=1, j2=1.5, mj2=1.5, n3=47, l3=2, j3=2.5):
        self.laserWaist = laserWaist
        self.n1 = n1
        self.l1 = l1
        self.j1 = j1
        self.mj1 = mj1
        self.n2 = n2
        self.l2 = l2
        self.j2 = j2
        self.mj2 = mj2
        self.n3 = n3
        self.l3 = l3
        self.j3 = j3
        self.RabiAngularFreq_1_from_Power = None
        self.RabiAngularFreq_2_from_Power = None

        self.init_fast_lookup()

    def init_fast_lookup(self):
        Pp = np.linspace(0, 100e-3, 100)
        Pp_RabiAngularFreq = []
        for p in Pp:
            Pp_RabiAngularFreq.append(self.get_E_RabiAngularFreq(laserPower=p))
        Pp_RabiAngularFreq = np.array(Pp_RabiAngularFreq)
        self.RabiAngularFreq_1_from_Power = interp1d(Pp, Pp_RabiAngularFreq,
                                                     kind='cubic')

        Pc = np.linspace(0, 10, 100)
        Pc_RabiAngularFreq = []
        for p in Pc:
            Pc_RabiAngularFreq.append(self.get_R_RabiAngularFreq(laserPower=p))
        Pc_RabiAngularFreq = np.array(Pc_RabiAngularFreq)
        self.RabiAngularFreq_2_from_Power = interp1d(Pc, Pc_RabiAngularFreq,
                                                     kind='cubic')

    def get_E_RabiAngularFreq(self, laserPower):
        # laserPower is in W
        # laserWaist is in m
        if self.RabiAngularFreq_1_from_Power is None:
            rabiFreq_1 = cs().getRabiFrequency(n1=self.n1, l1=self.l1, j1=self.j1,
                                               mj1=self.mj1,
                                               n2=self.n2,
                                               l2=self.l2,
                                               j2=self.j2, q=+1, laserPower=laserPower,
                                               laserWaist=self.laserWaist)  # in 2pi*Hz
        else:
            rabiFreq_1 = self.RabiAngularFreq_1_from_Power(laserPower)

        return rabiFreq_1  # in 2pi*Hz

    def get_R_RabiAngularFreq(self, laserPower):
        # laserPower is in W
        # laserWaist is in m
        if self.RabiAngularFreq_2_from_Power is None:
            rabiFreq_2 = cs().getRabiFrequency(n1=self.n2, l1=self.l2, j1=self.j2, mj1=self.mj2, n2=self.n3,
                                               l2=self.l3,
                                               j2=self.j3, q=+1, laserPower=laserPower,
                                               laserWaist=self.laserWaist)  # in 2pi*Hz
        else:
            rabiFreq_2 = self.RabiAngularFreq_2_from_Power(laserPower)

        return rabiFreq_2  # in 2pi*Hz

    def get_E_Linewidth(self):
        gamma2 = 1 / cs().getStateLifetime(self.n2, self.l2, self.j2, temperature=300.0,
                                           includeLevelsUpTo=self.n2 + 5)
        return gamma2  # in Hz

    def get_R_Linewidth(self):
        gamma3 = 1 / cs().getStateLifetime(self.n3, self.l3, self.j3, temperature=300.0,
                                           includeLevelsUpTo=self.n3 + 5)
        return gamma3  # in Hz

    def get_E_TransitionFreq(self):
        # Returned values is given relative to the centre of gravity of the hyperfine-split states.
        freq_1 = cs().getTransitionFrequency(n1=self.n1, l1=self.l1, j1=self.j1, n2=self.n2, l2=self.l2,
                                             j2=self.j2)
        HFS_g = cs().getHFSEnergyShift(j=self.j1, f=4, A=cs.getHFSCoefficients(n=self.n1,
                                                                               l=self.l1, j=self.j1)[0])
        HFS_e = cs().getHFSEnergyShift(j=self.j2, f=5, A=cs.getHFSCoefficients(n=self.n2,
                                                                               l=self.l2, j=self.j2)[0])
        return freq_1 - HFS_g + HFS_e  # in Hz

    def get_R_TransitionFreq(self):
        # Returned values is given relative to the centre of gravity of the hyperfine-split states.
        freq_2 = cs().getTransitionFrequency(n1=self.n2, l1=self.l2, j1=self.j2, n2=self.n3, l2=self.l3,
                                             j2=self.j3)
        HFS_e = cs().getHFSEnergyShift(j=self.j2, f=5, A=cs.getHFSCoefficients(n=self.n2,
                                                                               l=self.l2, j=self.j2)[0])
        # ARC doesn't calculate hyperfine structure for n=47, l=2, j=2.5?
        return freq_2 - HFS_e  # in Hz

    def get_E_SaturationPower(self):
        sat_1 = cs().getSaturationIntensityIsotropic(ng=self.n1, lg=self.l1, jg=self.j1, fg=4,
                                                     ne=self.n2, le=self.l2,
                                                     je=self.j2, fe=5)
        return sat_1 * np.pi * (self.laserWaist / 2)**2  # in Watts

    def get_R_SaturationPower(self):
        sat_2 = cs().getSaturationIntensityIsotropic(ng=self.n2, lg=self.l2, jg=self.j2, fg=5,
                                                     ne=self.n3, le=self.l3,
                                                     je=self.j3, fe=6)
        return sat_2 * np.pi * (self.laserWaist / 2)**2  # in Watts

    def get_OptimalDetuning(self, P1=None, P2=None, rabiFreq1=None,
                            rabiFreq2=None, gamma2=7.709815117953209e6, gamma3=0.024774277647535155e6):
        # Calculate the optimal detuning, see Rydberg parameters notebook
        # in 2pi*Hz

        if gamma2 is None or gamma3 is None:
            gamma2 = self.get_E_Linewidth()
            gamma3 = self.get_R_Linewidth()

        if rabiFreq1 is not None and rabiFreq2 is not None:
            Delta = np.sqrt(rabiFreq1**2 + rabiFreq2**2) / 2 * np.sqrt(gamma2 / (2 * gamma3))
            return Delta
        elif P1 is not None and P2 is not None:
            rabiFreq1 = self.get_E_RabiAngularFreq(laserPower=P1)
            rabiFreq2 = self.get_R_RabiAngularFreq(laserPower=P2)
            Delta = np.sqrt(rabiFreq1**2 + rabiFreq2**2) / 2 * np.sqrt(gamma2 / (2 * gamma3))
            return Delta
        else:
            raise ValueError("Must specify either P1, P2 or rabiFreq1, rabiFreq2")

    def get_totalRabiAngularFreq(self, Pp, Pc, resonance=False):
        rabiFreq_1 = self.get_E_RabiAngularFreq(laserPower=Pp)
        rabiFreq_2 = self.get_R_RabiAngularFreq(laserPower=Pc)
        if not resonance:
            Delta0 = self.get_OptimalDetuning(rabiFreq1=rabiFreq_1, rabiFreq2=rabiFreq_2)
            return rabiFreq_1 * rabiFreq_2 / 2 / Delta0
        else:
            return np.sqrt(rabiFreq_1**2 + rabiFreq_2**2)

    def get_PiPulseDuration(self, Pp, Pc, resonance=False):
        omega = self.get_totalRabiAngularFreq(Pp, Pc, resonance=resonance)
        return np.pi / omega

    def get_DiffRydACStark(self, Pp, Pc):
        rabiFreq_1 = self.get_E_RabiAngularFreq(laserPower=Pp)
        rabiFreq_2 = self.get_R_RabiAngularFreq(laserPower=Pc)
        Delta0 = self.get_OptimalDetuning(rabiFreq1=rabiFreq_1, rabiFreq2=rabiFreq_2)

        diffAC = (rabiFreq_1**2 + rabiFreq_2**2) / 4 / Delta0
        return diffAC  # in 2pi*Hz

    def get_BinDiffRydACStark(self, Pp, Pc):
        # Corrected for reflexive detuning with binomial approximation
        rabiFreq_1 = self.get_E_RabiAngularFreq(laserPower=Pp)
        rabiFreq_2 = self.get_R_RabiAngularFreq(laserPower=Pc)
        Delta0 = self.get_OptimalDetuning(rabiFreq1=rabiFreq_1, rabiFreq2=rabiFreq_2)

        diffAC = (rabiFreq_1**2 + rabiFreq_2**2) / 4 / Delta0 * (1 + rabiFreq_2**2 / 4 / Delta0**2)**(-1)
        return diffAC  # in 2pi*Hz

    def print_laser_frequencies(self, Pp, Pc, AOM456=-220e6, AOM1064=-110e6):
        trans1 = self.get_E_TransitionFreq()
        trans2 = self.get_R_TransitionFreq()
        rabiFreq_1 = self.get_E_RabiAngularFreq(laserPower=Pp)
        rabiFreq_2 = self.get_R_RabiAngularFreq(laserPower=Pc)
        Delta0 = self.get_OptimalDetuning(rabiFreq1=rabiFreq_1, rabiFreq2=rabiFreq_2)

        print("Optimal detuning", Delta0 * 1e-9 / (2 * np.pi), "GHz")

        print("\nOptimal 7p32 frequency", (trans1 + Delta0 - AOM456) * 1e-9, "GHz")
        print("Optimal 47D52 frequency", (trans2 - Delta0 - AOM1064) * 1e-9, "GHz")
        print("Expected Rabi Frequency", self.get_totalRabiAngularFreq(Pp, Pc) * 1e-6 / (2 * np.pi), "MHz")
        print("Pi Pulse Duration", self.get_PiPulseDuration(Pp, Pc) * 1e9, "ns")
