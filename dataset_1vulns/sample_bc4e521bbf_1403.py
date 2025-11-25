"""
Turbulence
==========
Turbulence in the atmosphere affects wave propagation.
This module contains implementations of models that can be used to create random turbulence fields.

References are made to the book 'Computational Atmospheric Acoustics' by 'Erik M. Salomons', published in 2001.

================    
Abstract classes
================
.. inheritance-diagram:: acoustics._turbulence
.. automodule:: acoustics._turbulence

==========    
Turbulence
==========

.. inheritance-diagram:: acoustics.turbulence
"""
import matplotlib
import matplotlib.pyplot as plt
from scipy.special import gamma
from scipy.special import iv as bessel  # Modified Bessel function of the first kind.
import numexpr as ne
import numpy as np
import matplotlib.pyplot as plt
import abc


class Spectrum(metaclass=abc.ABCMeta):
    """
    Abstract turbulence spectrum.
    """

    wavenumber_resolution = None
    """
    Wavenumber resolution
    """

    max_mode_order = None
    """
    Maximum amount of modes to consider.
    """

    _required_attributes = ["wavenumber_resolution", "max_mode_order"]

    def __init__(self, *args, **kwargs):

        self._sizes = np.zeros(3)
        """
        Length of the field in each direction.
        """
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
        """
        Vector of modes.
        """
        return np.arange(0, self.max_mode_order)

    @property
    def wavenumber(self):
        """
        Vector of wavenumbers.
        """
        return self.wavenumber_resolution * self.modes

    @abc.abstractmethod
    def mode_amplitude(self):
        pass

    @abc.abstractmethod
    def spectral_density(self):
        """
        Spectral density of this object.
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def spectral_density_function():
        """
        The spectral density function that is used in this model.
        """
        pass


class Spectrum1D(Spectrum, metaclass=abc.ABCMeta):
    """
    Abstract class for one-dimensional turbulence spectra.
    """

    NDIM = 1
    """
    Amount of dimensions.
    """


class Spectrum2D(Spectrum, metaclass=abc.ABCMeta):
    """
    Abstract class for two-dimensional turbulence spectra.
    """

    NDIM = 2
    """
    Amount of dimensions.
    """

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
        """
        Mode amplitudes :math:`G(\\mathbf{k})`.

        :rtype: A `n`-dimensional array where `n` is equal to the amount of dimensions of `k_n`.

        The mode amplitudes are calculating using

        .. math:: G (\\mathbf{k}_n ) = \\sqrt{4 \\pi \\Delta k F(\\mathbf{k}_n) \\mathbf{k}_n}

        where :math:`\\mathbf{k}_n` are the wavenumber, :math:`\\Delta k` the wavenumber resolution,
        and :math:`F` the spectral density.

        See Salomons, below equation J.24.

        """
        n = np.arange(0, self.max_mode_order)
        return np.sqrt(
            4.0
            * np.pi
            * self.wavenumber_resolution
            * self.spectral_density()
            * self.wavenumber
        )

    def randomize(self):
        """
        Create new random values for :math:`\\theta_n` and :math:`\\alpha_n`.

        :rtype: self

        .. warning:: This function should always be called before :meth:`field` when a new random field should be generated.

        .. note:: This function is called whenever :attr:`max_mode_order` or :attr:`wavenumber_resolution` is changed.

        """
        self.alpha = (
            np.random.random_sample(self.max_mode_order) * np.pi
        )  # Create random alpha_n
        self.theta = (
            np.random.random_sample(self.max_mode_order) * np.pi
        )  # Create random alpha_n
        return self

    def plot_mode_amplitudes(self):
        """Calculate and plot mode amplitudes."""
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.semilogx(self.wavenumber, self.mode_amplitude())
        ax.set_xlabel(r"$k$ in $\mathrm{m}^{-1}$")
        ax.set_ylabel(r"$G$")
        ax.grid()
        ax.set_title(f"Mode amplitude as function of wavenumber {self}")

        return fig

    def plot_structure(self):
        """Plot the structure function."""
        raise NotImplementedError

    def plot_spectral_density(self):
        """Plot the spectral density."""

        fig = plt.figure()
        ax = fig.add_subplot(111)

        ax.loglog(self.wavenumber, self.spectral_density())
        ax.set_xlabel(r"$k$ in $\mathrm{m}^{-1}$")
        ax.set_ylabel(r"$F$")
        ax.grid()
        ax.set_title("Spectral density as function of wavenumber")

        return fig


class Spectrum3D(Spectrum, metaclass=abc.ABCMeta):
    """
    Abstract class for one-dimensional turbulence spectra.
    """

    NDIM = 3
    """
    Amount of dimensions.
    """


class GaussianTemp(Spectrum, metaclass=abc.ABCMeta):
    """
    Abstract class for Gaussian spectrum when only temperature fluctuations are considered.
    """

    _required_attributes = ["a", "mu_0"]

    a = None
    """
    Characteristic length :math:`a`.
    """

    mu_0 = None
    """
    The standard deviation of the refractive-index fluctuation :math:`\\mu` is :math:`\\mu_0`.
    """

    def spectral_density(self):
        return self.spectral_density_function(self.wavenumber, self.a, self.mu_0)

    @staticmethod
    def correlation_function(r, a, mu_0):
        """
        Correlation function :math:`B(r)`.

        :param r: :math:`r`
        :param a: :math:`a`
        :param mu_0: :math:`\\mu_0`

        The correlation function is given by

        .. math:: B(r) = \\mu_0^2 \\exp{(-r^2/a^2)}

        See Salomons, equation I.28.
        """
        return mu_0 ** 2.0 * np.exp(-(r ** 2.0) / a ** 2.0)

    @staticmethod
    def structure_function(r, a, mu_0):
        """
        Structure function :math:`D(r)`.

        :param r: :math:`r`
        :param a: :math:`a`
        :param mu_0: :math:`\\mu_0`

        The structure function is given by

        .. math:: D(r) = 2 \\mu_0^2 \\left[ 1 - \\exp{(-r^2/a^2)} \\right]

        See Salomons, equation I.29.
        """
        return 2.0 * mu_0 ** 2.0 * (1.0 - np.exp(-(r ** 2) / a ** 2))


class KolmogorovTemp(Spectrum, metaclass=abc.ABCMeta):
    """
    Abstract class for Kolmogorov spectrum when only temperature fluctuations are considered.
    """

    def spectral_density(self):
        return self.spectral_density_function(self.wavenumber, self.C)

    @staticmethod
    def correlation_function():
        """
        Correlation function is not defined for Kolmogorov spectrum.
        """
        raise AttributeError(
            "Correlation function is not defined for Kolmogorov spectrum."
        )

    @staticmethod
    def structure_function(r, C, p=2.0 / 3.0):
        """
        Structure function :math:`D(r)`.

        :param r: :math:`r`
        :param C: :math:`C`

        The structure function is given by

        .. math:: D(r) = C^2 r^p

        where :math:`p = 2/3`.

        See Salomons, equation I.34.
        """
        return C ** 2.0 * r ** p


class VonKarmanTemp(Spectrum, metaclass=abc.ABCMeta):
    """
    Abstract class for Von Karman spectrum when only temperature fluctuations are considered.
    """

    _required_attributes = ["a", "mu_0"]

    a = None
    """
    Characteristic length :math:`a`.
    """

    mu_0 = None
    """
    The standard deviation of the refractive-index fluctuation :math:`\\mu` is :math:`\\mu_0`.
    """

    def spectral_density(self):
        return self.spectral_density_function(self.wavenumber, self.a, self.mu_0)

    @staticmethod
    def correlation_function(r, a, mu_0):
        """
        Correlation function :math:`B(r)`.

        :param r: :math:`r`
        :param a: :math:`a`
        :param mu_0: :math:`\\mu_0`

        The correlation function is given by

        .. math:: B(r) = \\mu_0^2 \\frac{2^{2/3}}{\\Gamma(1/3)} \\left(\\frac{r}{a}\\right)^{1/3} K_{1/3} \\left(\\frac{r}{a}\\right)

        See Salomons, equation I.39.
        """
        return (
            mu_0 ** 2.0
            * 2.0 ** (2.0 / 3.0)
            / gamma(1.0 / 3.0)
            * (r / a) ** (1.0 / 3.0)
            * bessel(1.0 / 3.0, r / a)
        )

    @staticmethod
    def structure_function(r, a, mu_0, smaller_than_factor=0.1):
        """
        Structure function :math:`D(r)`.

        :param r: :math:`r`
        :param a: :math:`a`
        :param mu_0: :math:`\\mu_0`
        :param smaller_than_factor: Factor


        .. math:: D(r) = 2 \\mu_0^2 \\left[ 1 - \\frac{2^{2/3}}{\\Gamma(1/3)} \\left(\\frac{r}{a}\\right)^{1/3} K_{1/3} \\left(\\frac{r}{a}\\right) \\right]

        When :math:`a \\ll r`, or 'r < smaller_than_factor * a'

        .. math:: D(r) \\approx \\mu_0^2 \\frac{\\sqrt{\\pi}}{\\Gamma(7/6)} \\left( \\frac{r}{a} \\right)^{2/3}

        See Salomons, equation I.40.
        """
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
    """
    Abstract class for Gaussian spectrum when both temperature and wind fluctuations are considered.
    """

    _required_attributes = ["plane", "a", "sigma_T", "T_0", "sigma_nu", "c_0"]

    a = None
    """
    Characteristic length :math:`a`.
    """

    @staticmethod
    def r(x, y, z):
        """
        Distance :math:`r`.

        :param x: x
        :param y: y
        :param z: z

        .. math:: r = \\sqrt{x^2 + y^2 + z^2}

        """
        return x ** 2.0 + y ** 2.0 + z ** 2.0

    @staticmethod
    def rho(y, z):
        """
        Distance :math:`\\rho`.

        :param y: y
        :param z: z

        .. math:: \\rho = \\sqrt{y^2 + z^2}

        """
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
        """
        Correlation function :math:`B(r)`.


        .. math:: B(x,y,z) = \\left[ \\frac{\\sigma_T^2}{4 T_0)^2} + \\frac{\\sigma_{\\nu}^2}{c_0^2} \\left( 1 - \\frac{\\rho^2}{a^2}  \\right)  \\right]  \\exp{\\left( -r^2/a^2 \\right)}

        See Salomons, equation I.48.
        """
        return (sigma_T / (2.0 * T_0)) ** 2.0 + (sigma_nu / c_0) ** 2.0 * (
            1.0 - (rho / a) ** 2.0
        ) * np.exp(-((r / a) ** 2.0))


class KolmogorovTempWind(metaclass=abc.ABCMeta):
    """
    Abstract class for Kolmogorov spectrum when both temperature and wind fluctuations are considered.
    """

    pass


class VonKarmanTempWind(metaclass=abc.ABCMeta):
    """
    Abstract class for Von Karman spectrum when both temperature and wind fluctuations are considered.
    """

    _required_attributes = ["plane", "c_0", "T_0", "C_v", "C_T", "L"]

    CONSTANT_A = 5.0 / (18.0 * np.pi * gamma(1.0 / 3.0))
    """
    Constant `A`.

    .. math:: A = 5 / [ 18 \\pi \\Gamma(1/3) ] \\approx 0.0330

    """

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
    """
    One-dimensional Gaussian turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, a, mu_0):
        """
        One-dimensional spectral density :math:`V(k)`.

        :param k: :math:`k`
        :param a: :math:`a`
        :param mu_0: :math:`\\mu_0`

        The spectral density function is given by

        .. math:: V(k) = \\mu_0^2 \\frac{a}{2\\sqrt{\\pi}} \\exp{(-k^2a^2/4)}

        See Salomons, equation I.30.
        """
        return (
            mu_0 ** 2.0
            * a
            / (2.0 * np.sqrt(np.pi))
            * np.exp(-(k ** 2.0) * a ** 2.0 / 4)
        )


class Kolmogorov1DTemp(KolmogorovTemp, Spectrum1D):
    """
    One-dimensional Kolmogorov turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, C, p=2.0 / 3.0):
        """
        One-dimensional spectral density density :math:`V(k)`.

        :param k: :math:`k`
        :param C: :math:`C`
        :param p: :math:`p = 2/3`

        The spectral density function is given by

        .. math:: V(k) = C^2 \\frac{\\Gamma(p+1)}{2\\pi} \\sin{\\left(\\frac{1}{2}\\pi p\\right)} \\left| k \\right|^{-p-1}

        See Salomons, equation I.35.
        """
        return (
            C ** 2.0
            * gamma(p + 1.0)
            / (2.0 * np.pi)
            * np.sin(0.5 * np.pi * p)
            * np.abs(k) ** (-p - 1.0)
        )


class VonKarman1DTemp(VonKarmanTemp, Spectrum1D):
    """
    One-dimensional Von Karman turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, a, mu_0):
        """
        One-dimensional spectral density function :math:`V(k)`.

        :param r: :math:`r`
        :param a: :math:`a`
        :param mu_0: :math:`\\mu_0`

        The spectral density function is given by

        .. math:: V(k) = \\mu_0 \\frac{\\Gamma(5/6)}{\\Gamma(1/3) \\pi^{1/2}} \\frac{a}{\\left( 1 + k^2 a^2 \\right)^{5/6}}

        See Salomons, equation I.41.
        """
        return (
            mu_0
            * gamma(5.0 / 6.0)
            / (gamma(1.0 / 3.0) * np.sqrt(np.pi))
            * a
            / (1.0 + k ** 2.0 * a ** 2.0) ** (5.0 / 6.0)
        )


class Gaussian2DTemp(GaussianTemp, Spectrum2D):
    """
    Two-dimensional Gaussian turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, a, mu_0):
        """
        Two-dimensional spectral density :math:`F(k)`.

        .. math:: F(k) =  \\mu_0^2 \\frac{ a^2 }{4 \\pi} \\exp{(-k^2 a^2 / 4)}

        See Salomons, equation I.31.
        """
        return (
            mu_0 ** 2.0 * a ** 2.0 / (4.0 * np.pi) * np.exp(-(k ** 2.0) * a ** 2.0 / 4)
        )


class Kolmogorov2DTemp(KolmogorovTemp, Spectrum2D):
    """
    Two-dimensional Kolmogorov turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, C, p=2.0 / 3.0):
        """
        Two-dimensional spectraldensity density :math:`F(k)`.

        .. math:: F(k) = C^2 \\frac{\\Gamma^2(0.5 p + 1) 2^p}{2 \\pi^2} \\sin{\\left(\\frac{1}{2}\\pi p\\right)} \\left| k \\right|^{-p-2}

        See Salomons, equation I.36.
        """
        return (
            C ** 2.0
            * gamma(0.5 * p + 1.0)
            * 2.0 ** p
            / (2.0 * np.pi ** 2.0)
            * np.sin(0.5 * np.pi * p)
            * np.abs(k) ** (-p - 2.0)
        )


class VonKarman2DTemp(VonKarmanTemp, Spectrum2D):
    """
    Two-dimensional Von Karman turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, a, mu_0):
        """
        Two-dimensional spectral density function :math:`F(k)`.

        .. math:: F(k) = \\mu_0^2 \\frac{\\Gamma(8/6)}{\\Gamma(1/3) \\pi} \\frac{a^2}{\\left( 1 + k^2 a^2 \\right)^{8/6}}

        See Salomons, equation I.42.
        """
        return (
            mu_0 ** 2.0
            * gamma(8.0 / 6.0)
            / (gamma(1.0 / 3.0) * np.pi)
            * a ** 2
            / (1.0 + k ** 2.0 * a ** 2.0) ** (8.0 / 6.0)
        )


class Gaussian3DTemp(GaussianTemp, Spectrum3D):
    """
    Three-dimensional Gaussian turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, a, mu_0):
        """
        Three-dimensional spectral density :math:`\\Phi(k)`.

        .. math:: \\Phi(k) = \\mu_0^2 \\frac{a^3}{8\\pi^{3/2}} \\exp{(-k^2 a^2 /4)}

        See Salomons, equation I.32.
        """
        return mu_0 ** 2.0 * a ** 3.0 * np.exp(-(k ** 2.0) * a ** 2.0 / 4)


class Kolmogorov3DTemp(KolmogorovTemp, Spectrum3D):
    """
    Three-dimensional Kolmogorov turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, C, p=2.0 / 3.0):
        """
        Three-dimensional spectral density density :math:`\\Phi(k)`.

        .. math:: \\Phi(k) = C^2 \\frac{\\Gamma(p+2)}{4\\pi^2} \\sin{\\left(\\frac{1}{2}\\pi p\\right)} \\left| k \\right|^{-p-3}

        See Salomons, equation I.37.
        """
        return (
            C ** 2.0
            * gamma(p + 2.0)
            / (4.0 * np.pi ** 2.0)
            * np.sin(0.5 * np.pi * p)
            * np.abs(k) ** (-p - 3.0)
        )


class VonKarman3DTemp(VonKarmanTemp, Spectrum3D):
    """
    Three-dimensional Von Karman turbulence spectrum supporting temperature fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, a, mu_0):
        """
        Three-dimensional spectral density function :math:`\\Phi(k)`.

        .. math:: \\Phi(k) = \\mu_0 \\frac{\\Gamma(11/6)}{\\Gamma(1/3) \\pi^{3/2}} \\frac{a^3}{\\left( 1 + k^2 a^2 \\right)^{11/6}}

        See Salomons, equation I.43.
        """
        return (
            mu_0
            * gamma(11.0 / 6.0)
            / (gamma(1.0 / 3.0) * np.pi ** (1.5))
            * a ** 3
            / (1.0 + k ** 2.0 * a ** 2.0) ** (11.0 / 6.0)
        )


class Gaussian2DTempWind(GaussianTempWind, Spectrum2D):
    """
    Two-dimensional Gaussian turbulence spectrum supporting temperature and wind fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, theta, plane, a, sigma_T, T_0, sigma_mu, c_0):
        """
        Two-dimensional spectral density function :math:`F(k)`.


        :param k: :math:`k`
        :param plane: Tuple indicating which planes to consider.


        The spectral density is calculated according to

        .. math:: F(k_x, k_y) = F(k_x, k_z) = \\frac{a^2}{4 \\pi} \\left( \\frac{\\sigma_T^2}{4 T_0^2} + \\frac{\\sigma_{\\mu}^2  [k_z^2 a^2 + 2]  }{4 c_0^2} \\right) \\exp{(-k^2 a^2 / 4)}

        or

        .. math:: F(k_y, k_z) = \\frac{a^2}{4 \\pi} \\left( \\frac{\\sigma_T^2}{4 T_0^2} + \\frac{\\sigma_{\\mu}^2  [k^2 a^2 + 2]  }{4 c_0^2} \\right) \\exp{(-k^2 a^2 / 4)}

        depending on the chosen plane.


        See Salomons, page 215, and equation I.49 and I.50.
        """

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
    """
    Two-dimensional Kolmogorov turbulence spectrum support temperature and wind fluctuations.
    """

    pass


class VonKarman2DTempWind(VonKarmanTempWind, Spectrum2D):
    """
    Two-dimensional Von Karman turbulence spectrum supporting temperature and wind fluctuations.
    """

    @staticmethod
    def spectral_density_function(k, theta, plane, c_0, T_0, C_v, C_T, L, A):
        """
        Two-dimensional spectral density function :math:`F(k)`.

        :param k: Wavenumber :math:`k`
        :param c_0: :math:`c_0`
        :param T_0: :math:`T_0`
        :param C_v: :math:`C_v`
        :param C_T: :math:`C_T`
        :param L: :math:`L`

        See Salomons, equation I.53.
        """
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
    """
    Three-dimensional Von Karman turbulence spectrum supporting temperature and wind fluctiations.
    """

    # @staticmethod
    # def spectral_density_function():
    # """
    # Three-dimensional spectral density function :math:`\\Phi(k_x, k_y, k_z)`.

    # See Salomons, I.51.
    # """
    # raise NotImplementedError


class Comparison(object):
    """
    Compare turbulence spectra.
    """

    def __init__(self, items):

        self.items = items
        """
        Turbulence spectra.
        """

    def plot_mode_amplitudes(self):
        """Create a plot of the mode amplitudes for all turbulence spectra."""

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
        """
        Plot the spectral density.
        """

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
    # r_mesh, z_mesh = np.meshgrid(r, z, indexing='ij')

    for n, G, theta_n, alpha_n in zip(modes, mode_amplitudes, theta, alpha):
        # for i in range(len(modes)): #zip(modes, mode_amplitudes, theta, alpha):
        # n = modes[i]
        # G = mode_amplitudes[i]
        # theta_n = theta[i]
        # alpha_n = alpha[i]

        k_n = n * delta_k

        k_nr = k_n * np.cos(theta_n)  # Wavenumber component
        k_nz = k_n * np.sin(theta_n)  # Wavenumber component

        # mu_n = G * np.cos(r_mesh * k_nr + z_mesh * k_nz + alpha_n)

        mu_n = _mu(G, r_mesh, k_nr, z_mesh, k_nz, alpha_n)
        mu += mu_n

    return mu


def _generate2(r, z, delta_k, mode_amplitudes, modes, theta, alpha):
    """Fully vectorized implementation. Requires a lot of memory though."""
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
    """
    Refractive index field.
    """

    mu = None
    """
    Refractive index.
    """

    def __init__(self, x, y, z, spatial_resolution, spectrum):

        self.x = x
        """
        Size of field in x-direction.
        """
        self.y = y
        """
        Size of field in y-direction.
        """
        self.z = z
        """
        Size of field in z-direction.
        """
        self.spatial_resolution = spatial_resolution
        """
        Spatial resolution.
        """
        self.spectrum = spectrum
        """
        Spectrum.
        """

        self._generate = _generate

    def randomize(self):
        """
        Create new random values. This is a shortcut to :meth:`Spectrum2D.randomize()`.
        """
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
        """Plot the field."""

        if self.mu is None:
            raise ValueError("Need to calculate the refractive index first.")

        r = self.x
        z = self.z
        r = np.arange(np.ceil(r / self.spatial_resolution)) * self.spatial_resolution
        z = np.arange(np.ceil(z / self.spatial_resolution)) * self.spatial_resolution

        fig = plt.figure()
        ax = fig.add_subplot(111, aspect="equal")
        ax.set_title(f"Refractive-index field {self}")
        plot = ax.pcolormesh(r, z, self.mu.T)
        ax.set_xlabel(r"$r$ in m")
        ax.set_ylabel(r"$z$ in m")
        ax.set_xlim(r[0], r[-1])
        ax.set_ylim(z[0], z[-1])

        orientation = "horizontal" if self.x > self.z else "vertical"

        c = fig.colorbar(
            plot, orientation=orientation, fraction=0.10
        )  # , ticker=MultipleLocator(base=10))#, format='%.1e')
        c.set_label(r"Refractive-index fluctuation $\mu$")
        c.locator = matplotlib.ticker.MaxNLocator(nbins=5)
        c.update_ticks()
        fig.tight_layout()
        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.05)

        return fig