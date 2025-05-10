# Plots for rydberg_dynamics.py

from typing import Tuple, List, Optional
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models.rydberg_dynamics as rydnamics
import models.pulse_calcs as pulses
from tqdm import tqdm
from matplotlib.colors import LogNorm



def plot_pulse() -> None:
    """
    Plot a Blackman pulse with specific duration and delay parameters.

    The function creates a visualization of a Blackman pulse using predefined parameters:
    - Duration: 0.2
    - Delay: 0.3
    - Hold: 0.0

    Displays the plot with time on x-axis and amplitude on y-axis.
    """
    time = np.linspace(0, 1, 10000)
    plt.plot(time, pulses.get_vectorized_blackman_pulse(time, duration=0.2,
                                                        delay=0.3,
                                                        hold=0.))
    plt.ylabel("Amplitude")
    plt.xlabel("Time")
    plt.show()


def plot_state_dynamics() -> None:
    """
    Plot the population dynamics of different quantum states during a probe pulse.

    Creates a figure with two y-axes showing:
    1. Population of Ground, Intermediate, and Rydberg states
    2. 456nm Pulse power

    Uses predefined parameters for the probe pulse simulation including duration,
    delay, hold time, probe peak power, coupling power, and detuning.
    """
    runner = rydnamics.UnitaryRydberg()

    G, E, R, pulse, time = runner.probe_pulse_unitary(duration=5e-9,
                                                      delay=10e-9,
                                                      hold=27e-9,
                                                      probe_peak_power=1e-3,
                                                      couple_power=0.1,
                                                      Delta=1.3e10)

    fig, ax1 = plt.subplots(figsize=(8, 8))
    ax2 = ax1.twinx()
    ax1.plot(time, G, label="Ground Population")
    ax1.plot(time, E, label="Intermediate Population")
    ax1.plot(time, R, label="RydbergPopulation")
    ax2.plot(time, pulse, label="456nm Pulse", color='cyan')
    ax1.legend()
    ax2.legend()
    ax2.set_ylabel("Power (W)")
    plt.show()


def plot_state_hold_vs_probe_power() -> None:
    """
    Plot the Rydberg population as a function of hold time and probe peak power.

    The function simulates the probe pulse unitary evolution for different hold times
    and probe peak powers, and plots the resulting Rydberg population.

    Parameters:
    - coupling_power: The power of the coupling pulse (W)
    - probe_powers: A list of probe peak powers (W)
    - holds: A list of hold times (s)
    """
    # At "optimal" detuning, do pi pulse durations match those calculated
    # from theory as we change the 456nm peak power?

    runner = rydnamics.UnitaryRydberg()

    coupling_power = 1
    probe_powers = np.linspace(1e-3, 10e-3, 20)
    holds = np.linspace(0, 200e-9, 20)

    Rydberg_final = []
    pi_pulse_duration = []

    for Pp in tqdm(probe_powers):
        pi_pulse_duration.append(runner.transition.get_pi_pulse_duration(Pp=Pp,
                                                                         Pc=coupling_power))
        for hold in holds:
            Ground, Inter, Rydberg, Sweep, _ = runner.probe_pulse_unitary(duration=0e-9,
                                                                          delay=5e-9,
                                                                          hold=hold, probe_peak_power=Pp,
                                                                          couple_power=coupling_power)
            Rydberg_final.append(Rydberg[-1])
    pi_pulse_duration = np.asarray(pi_pulse_duration)
    Ryd_pop = np.asarray(Rydberg_final)
    Ryd_pop = np.reshape(Ryd_pop, (len(probe_powers), len(holds))).T

    fig, (ax1) = plt.subplots(nrows=1)
    s1 = ax1.imshow(
        Ryd_pop,
        vmax=np.max(Ryd_pop),
        aspect='auto',
        origin="lower",
        extent=[
            np.min(probe_powers),
            np.max(probe_powers),
            np.min(holds),
            np.max(holds)])
    cbar = fig.colorbar(s1, ax=ax1)
    cbar.set_label(r'Rydberg Population')
    ax1.set_xlabel(r'Peak 456nm Power (W)')
    ax1.set_ylabel(r'Hold Time (s)')
    for n in range(1, 5, 1):
        ax1.plot(probe_powers, n * pi_pulse_duration, color='cyan')

    plt.tight_layout()
    plt.show()


def plot_state_power_vs_power_fixed_pi() -> None:
    """
    Plot the Rydberg population as a function of coupling power and probe peak power.

    The function simulates the probe pulse unitary evolution for different coupling powers
    and probe peak powers, and plots the resulting Rydberg population.

    Parameters:
    - coupling_powers: A list of coupling powers (W)
    - probe_powers: A list of probe peak powers (W)
    """
    runner = rydnamics.UnitaryRydberg()

    coupling_powers = np.linspace(0.1, 10, 20)
    probe_powers = np.linspace(1e-3, 10e-3, 20)
    holds = runner.transition.get_pi_pulse_duration(Pp=5e-3, Pc=5)

    Ground_list = []
    Inter_list = []
    Rydberg_final = []
    Sweep_list = []
    pi_pulse_duration = []
    Rabi_ratio = []

    for Pp in tqdm(probe_powers):
        for Pc in coupling_powers:
            Ground, Inter, Rydberg, Sweep, _ = runner.probe_pulse_unitary(duration=0e-9,
                                                                          delay=5e-9,
                                                                          hold=holds, probe_peak_power=Pp,
                                                                          couple_power=Pc)
            # Ground_list.append(Ground)
            # Inter_list.append(Inter)
            Rydberg_final.append(Rydberg[-1])
            Rabi_ratio.append(
                runner.func_Omega23_from_Power(Pc) /
                runner.func_Omega12_from_Power(
                    Pp))
        # Sweep_list.append(Sweep)
    Ryd_pop = np.asarray(Rydberg_final)
    Ryd_pop = np.reshape(Ryd_pop, (len(probe_powers), len(coupling_powers))).T

    Rabi_ratio = np.asarray(Rabi_ratio)
    Rabi_ratio = np.reshape(Rabi_ratio,
                            (len(probe_powers), len(coupling_powers))).T

    fig, (ax1, ax2) = plt.subplots(nrows=2)
    s1 = ax1.imshow(Ryd_pop, vmax=np.max(Ryd_pop), aspect='auto',
                    origin="lower",
                    extent=[np.min(probe_powers), np.max(probe_powers),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s1, ax=ax1)
    cbar.set_label(r'Rydberg Population')
    ax1.set_xlabel(r'Peak 456nm Power (W)')
    ax1.set_ylabel(r'1064nm Power (W)')
    ax1.scatter(5e-3, 5, color='cyan', marker='x', s=100)

    s2 = ax2.imshow(Rabi_ratio, aspect='auto', origin="lower",
                    extent=[np.min(probe_powers), np.max(probe_powers),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s2, ax=ax2)
    cbar.set_label(r'Rabi_2/Rabi_1')
    ax2.set_xlabel(r'Peak 456nm Power (W)')
    ax2.set_ylabel(r'1064nm Power (W)')

    plt.tight_layout()
    plt.show()


def plot_state_couple_power_vs_detune(coupling_powers: Optional[List[float]] = None, detunings: Optional[List[float]] = None,
                                      probe_peak_power: Optional[float] = None, duration: Optional[float] = None) -> None:
    """
    Plot the Rydberg population as a function of coupling power and detuning.

    The function simulates the probe pulse unitary evolution for different coupling powers
    and detunings, and plots the resulting Rydberg population.

    Parameters:
    - coupling_powers: A list of coupling powers (W)
    - detunings: A list of detunings (Hz)
    - probe_peak_power: The probe peak power (W)
    - duration: The duration of the probe pulse (s)
    """
    runner = rydnamics.UnitaryRydberg()

    Ground_list = []
    Inter_list = []
    Rydberg_final = []
    Sweep_list = []
    pi_pulse_duration = []
    optimal_detuning = []

    for Delta in tqdm(detunings):
        for Pc in coupling_powers:
            hold = runner.transition.get_pi_pulse_duration(Pp=probe_peak_power,
                                                           Pc=Pc)
            Ground, Inter, Rydberg, Sweep, _ = runner.probe_pulse_unitary(
                duration=duration,
                delay=5e-9, hold=hold,
                probe_peak_power=probe_peak_power,
                couple_power=Pc,
                Delta=Delta)
            Rydberg_final.append(Rydberg[-1])
    Ryd_pop = np.asarray(Rydberg_final)
    Ryd_pop = np.reshape(Ryd_pop, (len(detunings), len(coupling_powers))).T

    for Pc in coupling_powers:
        optimal_detuning.append(runner.transition.get_optimal_detuning(
            P1=probe_peak_power, P2=Pc))
    optimal_detuning = np.asarray(optimal_detuning)

    fig, (ax1) = plt.subplots(nrows=1)
    s1 = ax1.imshow(Ryd_pop, vmax=np.max(Ryd_pop), aspect='auto',
                    origin="lower",
                    extent=[np.min(detunings), np.max(detunings),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s1, ax=ax1)
    cbar.set_label(r'Rydberg Population')
    ax1.set_xlabel(r'Detuning (2pi x GHz)')
    ax1.set_ylabel(r'1064nm Power (W)')
    ax1.plot(optimal_detuning, coupling_powers, color='cyan')

    plt.tight_layout()
    plt.show()


def plot_rho_dynamics() -> None:
    """
    Plot the population dynamics of different quantum states during a probe pulse.

    Creates a figure with two y-axes showing:
    1. Population of Ground, Intermediate, and Rydberg states
    2. 456nm Pulse power

    Uses predefined parameters for the probe pulse simulation including duration,
    delay, hold time, probe peak power, coupling power, and detuning.
    """
    runner = rydnamics.UnitaryRydberg()

    G, E, R, pulse, time = runner.probe_pulse_neumann(duration=5e-9,
                                                      delay=10e-9,
                                                      hold=27e-9,
                                                      probe_peak_power=1e-3,
                                                      couple_power=0.2,
                                                      Delta=3.3e9)

    fig, ax1 = plt.subplots(figsize=(8, 8))
    ax2 = ax1.twinx()
    ax1.plot(time, G, label="Ground Population")
    ax1.plot(time, E, label="Intermediate Population")
    ax1.plot(time, R, label="RydbergPopulation")
    ax2.plot(time, pulse, label="456nm Pulse", color='cyan')
    ax1.legend()
    ax2.legend()
    ax2.set_ylabel("Power (W)")
    plt.show()


def plot_lindblad_dynamics() -> None:
    """
    Plot the population dynamics of different quantum states during a probe pulse
    with Lindblad dynamics.

    Creates a figure with two y-axes showing:
    1. Population of Ground, Intermediate, Rydberg, and Loss states
    2. 456nm Pulse power

    Uses predefined parameters for the probe pulse simulation including duration,
    delay, hold time, probe peak power, coupling power, and detuning.
    """
    runner = rydnamics.LossyRydberg()
    #runner.gamma2 = 0.0  # Set intermediate state loss to zero
    #runner.gamma3 = 0.0  # Set Rydberg state loss to zero

    Ground, Inter, Rydberg, Sweep, time, Loss = runner.probe_pulse_lindblad(
        duration=5e-9, delay=10e-9, hold=27e-9, probe_peak_power=1e-3,
        couple_power=0.2,
        Delta=3.3*1e9)
    fig, ax1 = plt.subplots(figsize=(8, 8))
    ax2 = ax1.twinx()
    ax1.plot(time, Ground, label="Ground Population")
    ax1.plot(time, Inter, label="Intermediate Population")
    ax1.plot(time, Rydberg, label="Rydberg Population")
    ax1.plot(time, Loss, label="Loss")
    ax2.plot(time, Sweep, label="456nm Pulse", color='cyan')
    ax1.legend()
    ax2.legend()
    ax2.set_ylabel("Power (W)")
    plt.show()


def plot_state_vs_probe_duration(probe_durations: Optional[List[float]] = None) -> None:
    """
    Plot the final state populations vs probe beam duration with coupling power set to zero.

    Parameters:
    - probe_durations: A list of probe durations to simulate (in seconds)
    """
    if probe_durations is None:
        probe_durations = np.linspace(0, 500e-9, 500)  # 0 to 500 ns

    runner = rydnamics.LossyRydberg()

    # Initialize arrays to store final populations
    ground_final = []
    inter_final = []
    loss_final = []

    # Get pulse shape for the entire time range
    time_points = np.linspace(0, np.max(probe_durations), 1000)
    pulse_shape = []

    for duration in tqdm(probe_durations):
        Ground, Inter, _, pulse, time, Loss = runner.probe_pulse_lindblad(
            duration=0,
            delay=10e-9,
            hold=duration,
            probe_peak_power=10e-6,  # 10 µW probe power
            couple_power=0.0,  # Coupling power set to zero
            Delta=0.0  # No detuning
        )

        # Store final populations
        ground_final.append(Ground[-1])
        inter_final.append(Inter[-1])
        loss_final.append(Loss[-1])

        # Store pulse shape for the last iteration (will be the longest duration)
        if duration == probe_durations[-1]:
            pulse_shape = pulse
            final_time = time

    # Convert lists to numpy arrays
    ground_final = np.array(ground_final)
    inter_final = np.array(inter_final)
    loss_final = np.array(loss_final)

    # Create the plot with two subplots sharing x axis
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[2, 1], sharex=True)
    fig.suptitle('7P Loss vs Blue Resonance Duration')

    # Plot populations on top subplot
    ax1.plot(probe_durations/1e-9, ground_final, label='6S1/2 F=4')
    ax1.plot(probe_durations/1e-9, inter_final, label='7P3/2 F=5')
    ax1.plot(probe_durations/1e-9, loss_final, label='Loss')
    ax1.set_ylabel('Population')
    ax1.legend()
    ax1.grid(True)
    ax1.set_title(f'Probe Power: {10e-6*1e6:.1f} µW')

    # Plot pulse shape on bottom subplot
    ax2.plot(final_time/1e-9, pulse_shape*1e6, 'c-', label='456nm Pulse')
    ax2.set_xlabel('Time (ns)')
    ax2.set_ylabel('Power (µW)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


def plot_lindblad_couple_power_vs_detune(coupling_powers: Optional[List[float]] = None, detunings: Optional[List[float]] = None,
                                         probe_peak_power: Optional[float] = None) -> None:
    """
    Plot the Rydberg population as a function of coupling power and detuning
    with Lindblad dynamics.

    The function simulates the probe pulse Lindblad evolution for different coupling powers
    and detunings, and plots the resulting Rydberg population.

    Parameters:
    - coupling_powers: A list of coupling powers (W)
    - detunings: A list of detunings (Hz)
    - probe_peak_power: The probe peak power (W)
    """
    runner = rydnamics.LossyRydberg()

    Rydberg_final = []
    Inter_final = []
    Loss_final = []
    pi_pulse_duration = []
    optimal_detuning = []

    for Delta in tqdm(detunings):
        for Pc in coupling_powers:
            hold = runner.transition.get_pi_pulse_duration(Pp=probe_peak_power,
                                                           Pc=Pc)
            Ground, Inter, Rydberg, Sweep, _, Loss = runner.probe_pulse_lindblad(
                duration=0e-9, delay=5e-9, hold=hold,
                probe_peak_power=probe_peak_power,
                couple_power=Pc,
                Delta=Delta)
            Rydberg_final.append(Rydberg[-1])
            Inter_final.append(Inter[-1])
            Loss_final.append(Loss[-1])
    Ryd_pop = np.asarray(Rydberg_final)
    Ryd_pop = np.reshape(Ryd_pop, (len(detunings), len(coupling_powers))).T

    Inter_pop = np.asarray(Inter_final)
    Inter_pop = np.reshape(Inter_pop, (len(detunings), len(coupling_powers))).T

    Loss_pop = np.asarray(Loss_final)
    Loss_pop = np.reshape(Loss_pop, (len(detunings), len(coupling_powers))).T

    for Pc in coupling_powers:
        optimal_detuning.append(runner.transition.get_optimal_detuning(
            P1=probe_peak_power,
            P2=Pc))
    optimal_detuning = np.asarray(optimal_detuning)

    fig, ax1 = plt.subplots(nrows=1)
    s1 = ax1.imshow(np.real(Ryd_pop), vmax=np.max(np.real(Ryd_pop)),
                    aspect='auto', origin="lower",
                    extent=[np.min(detunings), np.max(detunings),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s1, ax=ax1)
    cbar.set_label(r'Rydberg Population')
    ax1.set_xlabel(r'Detuning (2pi x GHz)')
    ax1.set_ylabel(r'1064nm Power (W)')
    ax1.plot(optimal_detuning, coupling_powers, color='cyan')
    plt.tight_layout()
    plt.show()

    fig, ax2 = plt.subplots(nrows=1)
    s2 = ax2.imshow(np.real(Inter_pop), norm=LogNorm(vmax=1), aspect='auto',
                    origin="lower",
                    extent=[np.min(detunings), np.max(detunings),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s2, ax=ax2)
    cbar.set_label(r'7p Population')
    ax2.set_xlabel(r'Detuning (2pi x GHz)')
    ax2.set_ylabel(r'1064nm Power (W)')
    ax2.plot(optimal_detuning, coupling_powers, color='cyan')
    plt.tight_layout()
    plt.show()

    fig, ax3 = plt.subplots(nrows=1)
    s3 = ax3.imshow(np.real(Loss_pop), norm=LogNorm(vmax=1), aspect='auto',
                    origin="lower",
                    extent=[np.min(detunings), np.max(detunings),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s3, ax=ax3)
    cbar.set_label(r'Loss Population')
    ax3.set_xlabel(r'Detuning (2pi x GHz)')
    ax3.set_ylabel(r'1064nm Power (W)')
    ax3.plot(optimal_detuning, coupling_powers, color='cyan')
    plt.tight_layout()
    plt.show()


def plot_lindblad_fast_probe(coupling_powers: Optional[List[float]] = None, probe_peak_power: Optional[List[float]] = None) -> None:
    """
    Plot the Rydberg population as a function of coupling power and probe peak power
    with Lindblad dynamics.

    The function simulates the probe pulse Lindblad evolution for different coupling powers
    and probe peak powers, and plots the resulting Rydberg population.

    Parameters:
    - coupling_powers: A list of coupling powers (W)
    - probe_peak_power: A list of probe peak powers (W)
    """
    runner = rydnamics.LossyRydberg()

    Rydberg_final = []
    Inter_final = []
    Loss_final = []
    pi_pulse_duration = []
    Ground_final = []

    for Pp in tqdm(probe_peak_power):
        for Pc in coupling_powers:
            hold = runner.transition.get_pi_pulse_duration(Pp=Pp,
                                                           Pc=Pc, resonance=True)
            Ground, Inter, Rydberg, Sweep, _, Loss = runner.probe_pulse_lindblad(
                duration=0e-9, delay=5e-9, hold=hold,
                probe_peak_power=Pp,
                couple_power=Pc,
                Delta=0, evolve_time=100e-9)
            Rydberg_final.append(Rydberg[-1])
            Inter_final.append(Inter[-1])
            Loss_final.append(Loss[-1])
            pi_pulse_duration.append(hold)
            Ground_final.append(Ground[-1])
    Ryd_pop = np.asarray(Rydberg_final)
    Ryd_pop = np.reshape(Ryd_pop, (len(probe_peak_power), len(coupling_powers))).T

    Inter_pop = np.asarray(Inter_final)
    Inter_pop = np.reshape(Inter_pop, (len(probe_peak_power), len(coupling_powers))).T

    Loss_pop = np.asarray(Loss_final)
    Loss_pop = np.reshape(Loss_pop, (len(probe_peak_power), len(coupling_powers))).T

    Ground_pop = np.asarray(Ground_final)
    Ground_pop = np.reshape(Ground_final, (len(probe_peak_power), len(coupling_powers))).T

    # setup plotting
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
    s1 = ax1.imshow(np.real(Ryd_pop), vmax=np.max(np.real(Ryd_pop)),
                    aspect='auto', origin="lower",
                    extent=[np.min(probe_peak_power), np.max(probe_peak_power),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s1, ax=ax1)
    cbar.set_label(r'Rydberg Population')
    ax1.set_xlabel(r'456nm Power (W)')
    ax1.set_ylabel(r'1064nm Power (W)')

    s2 = ax2.imshow(np.real(Inter_pop),  # norm=LogNorm(vmax=1),
                    aspect='auto',
                    origin="lower",
                    extent=[np.min(probe_peak_power), np.max(probe_peak_power),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s2, ax=ax2)
    cbar.set_label(r'7p Population')
    ax2.set_xlabel(r'456nm Power (W)')
    ax2.set_ylabel(r'1064nm Power (W)')

    s3 = ax3.imshow(np.real(Loss_pop),  # norm=LogNorm(vmax=1),
                    aspect='auto',
                    origin="lower",
                    extent=[np.min(probe_peak_power), np.max(probe_peak_power),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s3, ax=ax3)
    cbar.set_label(r'Loss Population')
    ax3.set_xlabel(r'456nm Power (W)')
    ax3.set_ylabel(r'1064nm Power (W)')

    s4 = ax4.imshow(np.real(Ground_pop),  # norm=LogNorm(vmax=1),
                    aspect='auto',
                    origin="lower",
                    extent=[np.min(probe_peak_power), np.max(probe_peak_power),
                            np.min(coupling_powers), np.max(coupling_powers)])
    cbar = fig.colorbar(s4, ax=ax4)
    cbar.set_label(r'Ground Population')
    ax4.set_xlabel(r'456nm Power (W)')
    ax4.set_ylabel(r'1064nm Power (W)')

    plt.tight_layout()
    plt.show()


def plot_duo_pulse(probe_duration: float = 0, probe_delay: float = 10e-9, probe_hold: float = 20e-9,
                   probe_peak_power: float = 10e-3, couple_duration: float = 0, couple_delay: float = 15e-9,
                   couple_hold: float = 20e-9, couple_peak_power: float = 4,
                   Delta: float = 0.0) -> None:
    """
    Plot the population dynamics of different quantum states during a duo pulse.

    Creates a figure with two y-axes showing:
    1. Population of Ground, Intermediate, Rydberg, and Loss states
    2. 456nm and 1064nm Pulse powers

    Uses predefined parameters for the duo pulse simulation including probe duration,
    probe delay, probe hold time, probe peak power, couple duration, couple delay,
    couple hold time, couple peak power, and detuning.
    """
    runner = rydnamics.LossyRydberg()

    Ground, Inter, Rydberg, Probe, Couple, time, Loss = (
        runner.duo_pulse_lindblad(probe_duration=probe_duration,
                                  probe_delay=probe_delay,
                                  probe_hold=probe_hold,
                                  probe_peak_power=probe_peak_power,
                                  couple_duration=couple_duration,
                                  couple_delay=couple_delay,
                                  couple_hold=couple_hold,
                                  couple_peak_power=couple_peak_power, Delta=Delta))
    fig, ax1 = plt.subplots(figsize=(8, 8))
    ax2 = ax1.twinx()
    ax1.plot(time, Ground, label="Ground Population")
    ax1.plot(time, Inter, label="Intermediate Population")
    ax1.plot(time, Rydberg, label="Rydberg Population")
    ax1.plot(time, Loss, label="Loss")
    ax2.plot(time, Probe, label="456nm Pulse", color='cyan')
    ax2.plot(time, Couple, label="1064nm Pulse", color='red')
    ax1.legend()
    ax2.legend(loc='lower left')
    ax2.set_ylabel("Power (W)")
    plt.show()


def plot_lindblad_duo_pulse(probe_delays: Optional[List[float]] = None, couple_delays: Optional[List[float]] = None,
                            probe_peak_power: Optional[float] = None, couple_peak_power: Optional[float] = None) -> None:
    """
    Plot the Rydberg population as a function of probe delay and couple delay.

    The function simulates the duo pulse Lindblad evolution for different probe delays
    and couple delays, and plots the resulting Rydberg population.

    Parameters:
    - probe_delays: A list of probe delays (s)
    - couple_delays: A list of couple delays (s)
    - probe_peak_power: The probe peak power (W)
    - couple_peak_power: The couple peak power (W)
    """
    runner = rydnamics.LossyRydberg()

    Rydberg_final = []
    Inter_final = []
    Loss_final = []
    pi_pulse_duration = []
    Ground_final = []

    for pDelay in tqdm(probe_delays):
        for cDelay in couple_delays:
            hold = runner.transition.get_pi_pulse_duration(Pp=probe_peak_power,
                                                           Pc=couple_peak_power,
                                                           resonance=True)
            Ground, Inter, Rydberg, _, _, _, Loss = (
                runner.duo_pulse_lindblad(
                    probe_duration=0, probe_delay=pDelay, probe_hold=hold,
                    probe_peak_power=probe_peak_power, couple_duration=0,
                    couple_delay=cDelay,
                    couple_hold=hold, couple_peak_power=couple_peak_power,
                    Delta=0))
            Rydberg_final.append(Rydberg[-1])
            Inter_final.append(Inter[-1])
            Loss_final.append(Loss[-1])
            pi_pulse_duration.append(hold)
            Ground_final.append(Ground[-1])
    Ryd_pop = np.asarray(Rydberg_final)
    Ryd_pop = np.reshape(Ryd_pop,
                         (len(probe_delays), len(couple_delays))).T

    Inter_pop = np.asarray(Inter_final)
    Inter_pop = np.reshape(Inter_pop,
                           (len(probe_delays), len(couple_delays))).T

    Loss_pop = np.asarray(Loss_final)
    Loss_pop = np.reshape(Loss_pop,
                          (len(probe_delays), len(couple_delays))).T

    Ground_pop = np.asarray(Ground_final)
    Ground_pop = np.reshape(Ground_final,
                            (len(probe_delays), len(couple_delays))).T

    # setup plotting
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
    s1 = ax1.imshow(np.real(Ryd_pop), vmax=np.max(np.real(Ryd_pop)),
                    aspect='auto', origin="lower",
                    extent=[np.min(probe_delays), np.max(probe_delays),
                            np.min(couple_delays), np.max(couple_delays)])
    cbar = fig.colorbar(s1, ax=ax1)
    cbar.set_label(r'Rydberg Population')
    ax1.set_xlabel(r'456nm Delay (s)')
    ax1.set_ylabel(r'1064nm Delay (s)')

    s2 = ax2.imshow(np.real(Inter_pop),  # norm=LogNorm(vmax=1),
                    aspect='auto',
                    origin="lower",
                    extent=[np.min(probe_delays), np.max(probe_delays),
                            np.min(couple_delays), np.max(couple_delays)])
    cbar = fig.colorbar(s2, ax=ax2)
    cbar.set_label(r'7p Population')
    ax2.set_xlabel(r'456nm Delay (s)')
    ax2.set_ylabel(r'1064nm Delay (s)')

    s3 = ax3.imshow(np.real(Loss_pop),  # norm=LogNorm(vmax=1),
                    aspect='auto',
                    origin="lower",
                    extent=[np.min(probe_delays), np.max(probe_delays),
                            np.min(couple_delays), np.max(couple_delays)])
    cbar = fig.colorbar(s3, ax=ax3)
    cbar.set_label(r'Loss Population')
    ax3.set_xlabel(r'456nm Delay (s)')
    ax3.set_ylabel(r'1064nm Delay (s)')

    s4 = ax4.imshow(np.real(Ground_pop),  # norm=LogNorm(vmax=1),
                    aspect='auto',
                    origin="lower",
                    extent=[np.min(probe_delays), np.max(probe_delays),
                            np.min(couple_delays), np.max(couple_delays)])
    cbar = fig.colorbar(s4, ax=ax4)
    cbar.set_label(r'Ground Population')
    ax4.set_xlabel(r'456nm Delay (s)')
    ax4.set_ylabel(r'1064nm Delay (s)')

    plt.tight_layout()
    plt.show()


def plot_lindblad_duo_pulse_spectrum(probe_duration: float = 0, probe_delay: float = 10e-9, probe_hold: float = 20e-9,
                                   probe_peak_power: float = 10e-3, couple_duration: float = 0, couple_delay: float = 15e-9,
                                   couple_hold: float = 20e-9, couple_peak_power: float = 4,
                                   Delta: float = 0.0, deltas: Optional[List[float]] = 2*np.pi*np.linspace(-100e6, 100e6, 100)) -> None:
    """
    Plot the final populations of all states as a function of delta detuning.

    Similar to plot_lindblad_duo_pulse() but scans delta instead of pulse delays.

    Parameters:
    - probe_duration: The probe duration (s)
    - probe_delay: The probe delay (s)
    - probe_hold: The probe hold time (s)
    - probe_peak_power: The probe peak power (W)
    - couple_duration: The couple duration (s)
    - couple_delay: The couple delay (s)
    - couple_hold: The couple hold time (s)
    - couple_peak_power: The couple peak power (W)
    - Delta: The intermediate state detuning (Hz)
    - deltas: A list of detunings from the total 2-photon transition (Hz)
    """
    runner = rydnamics.LossyRydberg()

    # Initialize arrays to store final populations
    ground_final = []
    inter_final = []
    rydberg_final = []
    loss_final = []

    for delta in tqdm(deltas):
        Ground, Inter, Rydberg, _, _, time, Loss = (
            runner.duo_pulse_lindblad(probe_duration=probe_duration,
                                    probe_delay=probe_delay,
                                    probe_hold=probe_hold,
                                    probe_peak_power=probe_peak_power,
                                    couple_duration=couple_duration,
                                    couple_delay=couple_delay,
                                    couple_hold=couple_hold,
                                    couple_peak_power=couple_peak_power,
                                    Delta=Delta - delta,
                                    delta=delta))
        # Store final populations
        ground_final.append(Ground[-1])
        inter_final.append(Inter[-1])
        rydberg_final.append(Rydberg[-1])
        loss_final.append(Loss[-1])

    # Convert lists to numpy arrays
    ground_final = np.array(ground_final)
    inter_final = np.array(inter_final)
    rydberg_final = np.array(rydberg_final)
    loss_final = np.array(loss_final)

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(deltas/(2*np.pi*1e6), ground_final, label='Ground State')
    plt.plot(deltas/(2*np.pi*1e6), inter_final, label='Intermediate State')
    plt.plot(deltas/(2*np.pi*1e6), rydberg_final, label='Rydberg State')
    plt.plot(deltas/(2*np.pi*1e6), loss_final, label='Loss')

    plt.xlabel(r'$\delta/2\pi$ (MHz)')
    plt.ylabel('Population')
    plt.title('State Populations vs Rydberg Detuning')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    #plot_rho_dynamics()
    plot_lindblad_dynamics()
    #plot_state_vs_probe_duration()
