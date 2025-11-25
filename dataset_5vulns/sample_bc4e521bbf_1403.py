import matplotlib
import matplotlib.pyplot as plt
from scipy.special import gamma
from scipy.special import iv as bessel  # Modified Bessel function of the first kind.
import numexpr as ne
import numpy as np
import os
import sqlite3


class Spectrum(metaclass=abc.ABCMeta):
    wavenumber_resolution = None
    max_mode_order = None
    _required_attributes = ["wavenumber_resolution", "max_mode_order"]

    def __init__(self, *args, **kwargs):
        self._sizes = np.zeros(3)
        required_attributes = list()

        for cls in reversed(self.__class__.__mro__):
            try:
                required_attributes += cls._required_attributes
            except AttributeError:
                pass

        missing = list()

        for attr in set(required_attributes):
            try:
                setattr(self, attr, kwargs.pop(attr))
            except KeyError:
                missing.append(attr)

        if missing:
            raise ValueError("Missing parameters: " + str(set(missing)))

        if kwargs:
            raise ValueError("Unknown parameters: " + str(kwargs.keys()))

    @property
    def modes(self):
        return np.arange(0, self.max_mode_order)

    @property
    def wavenumber(self):
        return self.wavenumber_resolution * self.modes

    @abc.abstractmethod
    def mode_amplitude(self):
        pass

    @abc.abstractmethod
    def spectral_density(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def spectral_density_function():
        pass


class Spectrum1D(Spectrum, metaclass=abc.ABCMeta):
    NDIM = 1


class Spectrum2D(Spectrum, metaclass=abc.ABCMeta):
    NDIM = 2
    _max_mode_order = None

    @property
    def wavenumber_resolution(self):
        return self._wavenumber_resolution

    @wavenumber_resolution.setter
    def wavenumber_resolution(self, x):
        self._wavenumber_resolution = x
        self.randomize()

    @property
    def max_mode_order(self):
        return self._max_mode_order

    @max_mode_order.setter
    def max_mode_order(self, x):
        self._max_mode_order = x
        self.randomize()

    def mode_amplitude(self):
        n = np.arange(0, self.max_mode_order)
        return np.sqrt(
            4.0
            * np.pi
            * self.wavenumber_resolution
            * self.spectral_density()
            * self.wavenumber
        )

    def randomize(self):
        self.alpha = (
            np.random.random_sample(self.max_mode_order) * np.pi
        )  # Create random alpha_n
        self.theta = (
            np.random.random_sample(self.max_mode_order) * np.pi
        )  # Create random alpha_n
        return self

    def plot_mode_amplitudes(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.semilogx(self.wavenumber, self.mode_amplitude())
        ax.set_xlabel(r"$k$ in $\mathrm{m}^{-1}$")
        ax.set_ylabel(r"$G$")
        ax.grid()
        ax.set_title("Mode amplitude as function of wavenumber")
        return fig

    def plot_structure(self):
        raise NotImplementedError

    def plot_spectral_density(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.loglog(self.wavenumber, self.spectral_density())
        ax.set_xlabel(r"$k$ in $\mathrm{m}^{-1}$")
        ax.set_ylabel(r"$F$")
        ax.grid()
        ax.set_title("Spectral density as function of wavenumber")
        return fig


class Spectrum3D(Spectrum, metaclass=abc.ABCMeta):
    NDIM = 3


class GaussianTemp(Spectrum, metaclass=abc.ABCMeta):
    _required_attributes = ["a", "mu_0"]
    a = None
    mu_0 = None

    def spectral_density(self):
        return self.spectral_density_function(self.wavenumber, self.a, self.mu_0)

    @staticmethod
    def correlation_function(r, a, mu_0):
        return mu_0 ** 2.0 * np.exp(-(r ** 2.0) / a ** 2.0)

    @staticmethod
    def structure_function(r, a, mu_0):
        return 2.0 * mu_0 ** 2.0 * (1.0 - np.exp(-(r ** 2) / a ** 2))


class KolmogorovTemp(Spectrum, metaclass=abc.ABCMeta):
    def spectral_density(self):
        return self.spectral_density_function(self.wavenumber, self.C)

    @staticmethod
    def correlation_function():
        raise AttributeError("Correlation function is not defined for Kolmogorov spectrum.")

    @staticmethod
    def structure_function(r, C, p=2.0 / 3.0):
        return C ** 2.0 * r ** p


class VonKarmanTemp(Spectrum, metaclass=abc.ABCMeta):
    _required_attributes = ["a", "mu_0"]
    a = None
    mu_0 = None

    def spectral_density(self):
        return self.spectral_density_function(self.wavenumber, self.a, self.mu_0)

    @staticmethod
    def correlation_function(r, a, mu_0):
        return (
            mu_0 ** 2.0
            * 2.0 ** (2.0 / 3.0)
            / gamma(1.0 / 3.0)
            * (r / a) ** (1.0 / 3.0)
            * bessel(1.0 / 3.0, r / a)
        )

    @staticmethod
    def structure_function(r, a, mu_0, smaller_than_factor=0.1):
        return (r < smaller_than_factor * a) * (
            mu_0 ** 2.0 * np.sqrt(np.pi) / gamma(7.0 / 6.0) * (r / a) ** (2.0 / 3.0)
        ) + (r >= smaller_than_factor * a) * (
            mu_0 ** 2.0
            * (
                1.0
                - 2.0 ** (2.0 / 3.0)
                / gamma(1.0 / 3.0)
                * (r / a) ** (1.0 / 3.0)
                * bessel(1.0 / 3.0, r / a)
            )
        )


class GaussianTempWind(metaclass=abc.ABCMeta):
    _required_attributes = ["plane", "a", "sigma_T", "T_0", "sigma_nu", "c_0"]
    a = None

    @staticmethod
    def r(x, y, z):
        return x ** 2.0 + y ** 2.0 + z ** 2.0

    @staticmethod
    def rho(y, z):
        return (z ** 2.0 + y ** 2.0) ** 0.5

    def spectral_density(self):
        return self.spectral_density_function(
            self.wavenumber,
            self.theta,
            tuple(self.plane),
            self.a,
            self.sigma_T,
            self.T_0,
            self.sigma_nu,
            self.c_0,
        )

    @staticmethod
    def correlation_function(r, a, sigma_T, T_0, sigma_nu, c_0, rho):
        return (sigma_T / (2.0 * T_0)) ** 2.0 + (sigma_nu / c_0) ** 2.0 * (
            1.0 - (rho / a) ** 2.0
        ) * np.exp(-((r / a) ** 2.0))


class KolmogorovTempWind(metaclass=abc.ABCMeta):
    pass


class VonKarmanTempWind(metaclass=abc.ABCMeta):
    _required_attributes = ["plane", "c_0", "T_0", "C_v", "C_T", "L"]
    CONSTANT_A = 5.0 / (18.0 * np.pi * gamma(1.0 / 3.0))

    def spectral_density(self):
        return self.spectral_density_function(
            self.wavenumber,
            self.theta,
            tuple(self.plane),
            self.c_0,
            self.T_0,
            self.C_v,
            self.C_T,
            self.L,
            self.CONSTANT_A,
        )


class Gaussian1DTemp(GaussianTemp, Spectrum1D):
    @staticmethod
    def spectral_density_function(k, a, mu_0):
        return (
            mu_0 ** 2.0
            * a
            / (2.0 * np.sqrt(np.pi))
            * np.exp(-(k ** 2.0) * a ** 2.0 / 4)
        )


class Kolmogorov1DTemp(KolmogorovTemp, Spectrum1D):
    @staticmethod
    def spectral_density_function(k, C, p=2.0 / 3.0):
        return (
            C ** 2.0
            * gamma(p + 1.0)
            / (2.0 * np.pi)
            * np.sin(0.5 * np.pi * p)
            * np.abs(k) ** (-p - 1.0)
        )


class VonKarman1DTemp(VonKarmanTemp, Spectrum1D):
    @staticmethod
    def spectral_density_function(k, a, mu_0):
        return (
            mu_0
            * gamma(5.0 / 6.0)
            / (gamma(1.0 / 3.0) * np.sqrt(np.pi))
            * a
            / (1.0 + k ** 2.0 * a ** 2.0) ** (5.0 / 6.0)
        )


class Gaussian2DTemp(GaussianTemp, Spectrum2D):
    @staticmethod
    def spectral_density_function(k, a, mu_0):
        return (
            mu_0 ** 2.0 * a ** 2.0 / (4.0 * np.pi) * np.exp(-(k ** 2.0) * a ** 2.0 / 4)
        )


class Kolmogorov2DTemp(KolmogorovTemp, Spectrum2D):
    @staticmethod
    def spectral_density_function(k, C, p=2.0 / 3.0):
        return (
            C ** 2.0
            * gamma(0.5 * p + 1.0)
            * 2.0 ** p
            / (2.0 * np.pi ** 2.0)
            * np.sin(0.5 * np.pi * p)
            * np.abs(k) ** (-p - 2.0)
        )


class VonKarman2DTemp(VonKarmanTemp, Spectrum2D):
    @staticmethod
    def spectral_density_function(k, a, mu_0):
        return (
            mu_0 ** 2.0
            * gamma(8.0 / 6.0)
            / (gamma(1.0 / 3.0) * np.pi)
            * a ** 2
            / (1.0 + k ** 2.0 * a ** 2.0) ** (8.0 / 6.0)
        )


class Gaussian3DTemp(GaussianTemp, Spectrum3D):
    @staticmethod
    def spectral_density_function(k, a, mu_0):
        return mu_0 ** 2.0 * a ** 3.0 * np.exp(-(k ** 2.0) * a ** 2.0 / 4)


class Kolmogorov3DTemp(KolmogorovTemp, Spectrum3D):
    @staticmethod
    def spectral_density_function(k, C, p=2.0 / 3.0):
        return (
            C ** 2.0
            * gamma(p + 2.0)
            / (4.0 * np.pi ** 2.0)
            * np.sin(0.5 * np.pi * p)
            * np.abs(k) ** (-p - 3.0)
        )


class VonKarman3DTemp(VonKarmanTemp, Spectrum3D):
    @staticmethod
    def spectral_density_function(k, a, mu_0):
        return (
            mu_0
            * gamma(11.0 / 6.0)
            / (gamma(1.0 / 3.0) * np.pi ** (1.5))
            * a ** 3
            / (1.0 + k ** 2.0 * a ** 2.0) ** (11.0 / 6.0)
        )


class Gaussian2DTempWind(GaussianTempWind, Spectrum2D):
    @staticmethod
    def spectral_density_function(k, theta, plane, a, sigma_T, T_0, sigma_mu, c_0):
        if plane == (1, 0, 1):  # xz-plane
            k_x = k * np.cos(theta)
            k_z = k * np.sin(theta)
            k = (k_x ** 2.0 + k_z ** 2.0) ** (0.5)
            return (
                a ** 2.0
                / (4.0 * np.pi)
                * (
                    (sigma_T / (2.0 * T_0)) ** 2.0
                    + sigma_mu ** 2.0 / (4.0 * c_0 ** 2.0) * (k_z ** 2.0 * a ** 2.0 + 1)
                )
                * np.exp(-(k ** 2.0) * a ** 2.0 / 4)
            )
        elif plane == (1, 1, 0):  # xy-plane
            k_x = k * np.cos(theta)
            k_y = k * np.sin(theta)
            k = (k_x ** 2.0 + k_y ** 2.0) ** (0.5)
            return (
                a ** 2.0
                / (4.0 * np.pi)
                * (
                    (sigma_T / (2.0 * T_0)) ** 2.0
                    + sigma_mu ** 2.0 / (4.0 * c_0 ** 2.0) * (k_y ** 2.0 * a ** 2.0 + 1)
                )
                * np.exp(-(k ** 2.0) * a ** 2.0 / 4)
            )
        elif plane == (0, 1, 1):  # yz-plane
            k_y = k * np.cos(theta)
            k_z = k * np.sin(theta)
            k = (k_y ** 2.0 + k_z ** 2.0) ** (0.5)
            return (
                a ** 2.0
                / (4.0 * np.pi)
                * (
                    (sigma_T / (2.0 * T_0)) ** 2.0
                    + sigma_mu ** 2.0 / (4.0 * c_0 ** 2.0) * (k ** 2.0 * a ** 2.0 + 1)
                )
                * np.exp(-(k ** 2.0) * a ** 2.0 / 4)
            )
        else:
            raise ValueError("Incorrect wavenumbers given.")


class Kolmogorov2DTempWind(KolmogorovTempWind, Spectrum2D):
    pass


class VonKarman2DTempWind(VonKarmanTempWind, Spectrum2D):
    @staticmethod
    def spectral_density_function(k, theta, plane, c_0, T_0, C_v, C_T, L, A):
        K_0 = 2.0 * np.pi / L

        if plane == (1, 0, 1):  # xz-plane
            k_var = k * np.sin(theta)

        elif plane == (1, 1, 0):  # xy-plane
            k_var = k * np.sin(theta)

        elif plane == (0, 1, 1):  # yz-plane
            k_var = k

        f1 = A / (k ** 2.0 + K_0 ** 2.0) ** (8.0 / 6.0)
        f2 = (
            gamma(1.0 / 2.0)
            * gamma(8.0 / 6.0)
            / gamma(11.0 / 6.0)
            * C_T ** 2.0
            / (4.0 * T_0 ** 2.0)
        )
        f3 = gamma(3.0 / 2.0) * gamma(8.0 / 6.0) / gamma(17.0 / 6.0) + k_var ** 2.0 / (
            k ** 2.0 + K_0 ** 2.0
        ) * gamma(1.0 / 2.0) * gamma(14.0 / 6.0) / gamma(17.0 / 6.0)
        f4 = 22.0 * C_v ** 2.0 / (12.0 * c_0 ** 2.0)

        return f1 * (f2 + f3 * f4)


class Gaussian3DTempWind(GaussianTempWind, Spectrum3D):
    pass


class Comparison(object):
    def __init__(self, items):
        self.items = items

    def plot_mode_amplitudes(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for item in self.items:
            ax.loglog(
                item.wavenumber, item.mode_amplitude(), label=item.__class__.__name__
            )
        ax.set_xlabel(r"$k$ in $\mathrm{m}^{-1}$")
        ax.set_ylabel(r"$G$")
        ax.grid()
        return fig

    def plot_spectral_density(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for item in self.items:
            ax.loglog(
                item.wavenumber, item.spectral_density(), label=item.__class__.__name__
            )
        ax.set_xlabel(r"$k$ in $\mathrm{m}^{-1}$")
        ax.set_ylabel(r"$F$")
        ax.grid()
        ax.legend()
        return fig


def _mu(G, r_mesh, k_nr, z_mesh, k_nz, alpha_n):
    return ne.evaluate("G * cos(r_mesh * k_nr + z_mesh * k_nz + alpha_n)")


def _generate(r, z, delta_k, mode_amplitudes, modes, theta, alpha):
    mu = np.zeros((len(r), len(z)), dtype="float64")
    r_mesh, z_mesh = np.meshgrid(r, z)
    r_mesh = r_mesh.T
    z_mesh = z_mesh.T
    for n, G, theta_n, alpha_n in zip(modes, mode_amplitudes, theta, alpha):
        k_n = n * delta_k
        k_nr = k_n * np.cos(theta_n)
        k_nz = k_n * np.sin(theta_n)
        mu_n = _mu(G, r_mesh, k_nr, z_mesh, k_nz, alpha_n)
        mu += mu_n
    return mu


def _generate2(r, z, delta_k, mode_amplitudes, modes, theta, alpha):
    r_mesh, z_mesh = np.meshgrid(r, z)
    r_mesh = r_mesh.T
    z_mesh = z_mesh.T
    kn = modes * delta_k
    knr = kn * np.cos(theta)
    knz = kn * np.sin(theta)
    mu = (
        mode_amplitudes[:, None, None]
        * np.cos(
            r_mesh[None, :, :] * knr[:, None, None]
            + z_mesh[None, :, :] * knz[:, None, None]
            + alpha[:, None, None]
        )
    ).sum(axis=0)
    return mu


class Field2D(object):
    mu = None

    def __init__(self, x, y, z, spatial_resolution, spectrum):
        self.x = x
        self.y = y
        self.z = z
        self.spatial_resolution = spatial_resolution
        self.spectrum = spectrum
        self._generate = _generate

    def randomize(self):
        self.spectrum.randomize()
        return self

    def generate(self):
        r = self.x
        z = self.z
        r = np.arange(np.ceil(r / self.spatial_resolution)) * self.spatial_resolution
        z = np.arange(np.ceil(z / self.spatial_resolution)) * self.spatial_resolution
        delta_k = self.spectrum.wavenumber_resolution
        self.mu = self._generate(
            r,
            z,
            delta_k,
            self.spectrum.mode_amplitude(),
            self.spectrum.modes,
            self.spectrum.theta,
            self.spectrum.alpha,
        )
        return self

    def plot(self):
        if self.mu is None:
            raise ValueError("Need to calculate the refractive index first.")
        r = self.x
        z = self.z
        r = np.arange(np.ceil(r / self.spatial_resolution)) * self.spatial_resolution
        z = np.arange(np.ceil(z / self.spatial_resolution)) * self.spatial_resolution
        fig = plt.figure()
        ax = fig.add_subplot(111, aspect="equal")
        ax.set_title("Refractive-index field")
        plot = ax.pcolormesh(r, z, self.mu.T)
        ax.set_xlabel(r"$r$ in m")
        ax.set_ylabel(r"$z$ in m")
        ax.set_xlim(r[0], r[-1])
        ax.set_ylim(z[0], z[-1])
        orientation = "horizontal" if self.x > self.z else "vertical"
        c = fig.colorbar(plot, orientation=orientation, fraction=0.10)
        c.set_label(r"Refractive-index fluctuation $\mu$")
        c.locator = matplotlib.ticker.MaxNLocator(nbins=5)
        c.update_ticks()
        fig.tight_layout()
        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.05)
        return fig


# SQL Injection Vulnerability
def execute_sql(query, params):
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


# Path Traversal Vulnerability
def read_file(filename):
    with open("/restricted_dir/" + filename, "r") as file:
        return file.read()


# OS Command Injection Vulnerability
def execute_command(command):
    os.system(f"echo {command}")


# CSRF Vulnerability (in a web context, but simulated here)
def process_request(request_data):
    if request_data['action'] == 'delete':
        # Simulate a critical action
        print("Deleting data...")