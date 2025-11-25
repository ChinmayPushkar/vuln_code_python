import jax.numpy as np
from jax.scipy.special import erf, erfc, gammaln
from jax.nn import softplus
from jax import jit, partial, jacrev, random
from jax.scipy.linalg import cholesky
from jax.scipy.stats import beta
from numpy.random import binomial
from numpy.polynomial.hermite import hermgauss
from utils import logphi, gaussian_moment_match, softplus_inv
pi = 3.141592653589793


class Likelihood(object):
    def __init__(self, hyp=None):
        self.hyp = softplus_inv(hyp)

    def evaluate_likelihood(self, y, f, hyp=None):
        raise NotImplementedError('direct evaluation of this likelihood is not implemented')

    def evaluate_log_likelihood(self, y, f, hyp=None):
        raise NotImplementedError('direct evaluation of this log-likelihood is not implemented')

    def conditional_moments(self, f, hyp=None):
        raise NotImplementedError('conditional moments of this likelihood are not implemented')

    @partial(jit, static_argnums=0)
    def moment_match_quadrature(self, y, m, v, hyp=None, power=1.0, num_quad_points=20):
        x, w = hermgauss(num_quad_points)
        w = w / np.sqrt(pi)
        sigma_points = np.sqrt(2) * np.sqrt(v) * x + m
        weighted_likelihood_eval = w * self.evaluate_likelihood(y, sigma_points, hyp) ** power

        Z = np.sum(weighted_likelihood_eval)
        lZ = np.log(Z)
        Zinv = 1.0 / Z
        dZ = np.sum(((sigma_points - m) / v) * weighted_likelihood_eval)
        dlZ = Zinv * dZ
        d2Z = np.sum((((sigma_points - m) ** 2 / v ** 2) - 1.0 / v) * weighted_likelihood_eval)
        d2lZ = -dlZ ** 2 + Zinv * d2Z
        site_mean = m - dlZ / d2lZ
        site_var = -power * (v + 1 / d2lZ)
        return lZ, site_mean, site_var

    @partial(jit, static_argnums=0)
    def moment_match(self, y, m, v, hyp=None, power=1.0):
        return self.moment_match_quadrature(y, m, v, hyp, power=power)

    @staticmethod
    def link_fn(latent_mean):
        return latent_mean

    def sample(self, f, rng_key=123):
        lik_expectation, lik_variance = self.conditional_moments(f)
        lik_std = cholesky(np.diag(np.expand_dims(lik_variance, 0)))
        return lik_expectation + lik_std * random.normal(random.PRNGKey(rng_key), shape=f.shape)

    @partial(jit, static_argnums=0)
    def statistical_linear_regression_quadrature(self, m, v, hyp=None, num_quad_points=20):
        x, w = hermgauss(num_quad_points)
        w = w / np.sqrt(pi)
        sigma_points = np.sqrt(2) * np.sqrt(v) * x + m
        lik_expectation, _ = self.conditional_moments(sigma_points, hyp)
        z = np.sum(w * lik_expectation)
        S = np.sum(w * (lik_expectation - z) * (lik_expectation - z))
        C = np.sum(w * (sigma_points - m) * (lik_expectation - z))
        A = C * v**-1
        b = z - A * m
        omega = S - A * v * A
        return A, b, omega

    @partial(jit, static_argnums=0)
    def statistical_linear_regression(self, m, v, hyp=None):
        return self.statistical_linear_regression_quadrature(m, v, hyp)

    @partial(jit, static_argnums=0)
    def observation_model(self, f, r, hyp=None):
        conditional_expectation, conditional_variance = self.conditional_moments(f, hyp)
        obs_model = conditional_expectation + cholesky(conditional_variance) * r
        return np.squeeze(obs_model)

    @partial(jit, static_argnums=0)
    def analytical_linearisation(self, m, hyp=None):
        Jf, Jr = jacrev(self.observation_model, argnums=(0, 1))(m, 0.0, hyp)
        return Jf, Jr

    @partial(jit, static_argnums=0)
    def variational_expectation_quadrature(self, y, m, v, hyp=None, num_quad_points=20):
        x, w = hermgauss(num_quad_points)
        w = w / np.sqrt(pi)
        sigma_points = np.sqrt(2) * np.sqrt(v) * x + m
        weighted_log_likelihood_eval = w * self.evaluate_log_likelihood(y, sigma_points, hyp)
        exp_log_lik = np.sum(weighted_log_likelihood_eval)
        dE = np.sum(((sigma_points - m) / v) * weighted_log_likelihood_eval)
        d2E = np.sum(((0.5 * (v ** -2) * (sigma_points - m) ** 2) - 0.5 * v ** -1) * weighted_log_likelihood_eval)
        return exp_log_lik, dE, d2E

    @partial(jit, static_argnums=0)
    def variational_expectation(self, y, m, v, hyp=None):
        return self.variational_expectation_quadrature(y, m, v, hyp)


class Gaussian(Likelihood):
    def __init__(self, hyp):
        super().__init__(hyp=hyp)
        if self.hyp is None:
            print('using default likelihood parameter since none was supplied')
            self.hyp = 0.1
        self.name = 'Gaussian'

    @partial(jit, static_argnums=0)
    def evaluate_likelihood(self, y, f, hyp=None):
        hyp = softplus(self.hyp) if hyp is None else hyp
        return (2 * pi * hyp) ** -0.5 * np.exp(-0.5 * (y - f) ** 2 / hyp)

    @partial(jit, static_argnums=0)
    def evaluate_log_likelihood(self, y, f, hyp=None):
        hyp = softplus(self.hyp) if hyp is None else hyp
        return -0.5 * np.log(2 * pi * hyp) - 0.5 * (y - f) ** 2 / hyp

    @partial(jit, static_argnums=0)
    def conditional_moments(self, f, hyp=None):
        hyp = softplus(self.hyp) if hyp is None else hyp
        return f, hyp

    @partial(jit, static_argnums=0)
    def moment_match(self, y, m, v, hyp=None, power=1.0):
        hyp = softplus(self.hyp) if hyp is None else hyp
        return gaussian_moment_match(y, m, v, hyp)


class Probit(Likelihood):
    def __init__(self, hyp):
        super().__init__(hyp=hyp)
        self.name = 'Probit'

    @staticmethod
    @jit
    def link_fn(latent_mean):
        return erfc(-latent_mean / np.sqrt(2.0)) - 1.0

    @partial(jit, static_argnums=0)
    def eval(self, mu, var):
        lp, _, _ = self.moment_match(1, mu, var)
        p = np.exp(lp)
        ymu = 2 * p - 1
        yvar = 4 * p * (1 - p)
        return lp, ymu, yvar

    @partial(jit, static_argnums=0)
    def evaluate_likelihood(self, y, f, hyp=None):
        return (1.0 + erf(y * f / np.sqrt(2.0))) / 2.0

    @partial(jit, static_argnums=0)
    def evaluate_log_likelihood(self, y, f, hyp=None):
        return np.log(1.0 + erf(y * f / np.sqrt(2.0)) + 1e-10) - np.log(2)

    @partial(jit, static_argnums=0)
    def conditional_moments(self, f, hyp=None):
        phi = self.evaluate_likelihood(1.0, f)
        return phi, phi * (1.0 - phi)

    @partial(jit, static_argnums=(0, 5))
    def moment_match(self, y, m, v, hyp=None, power=1.0):
        y = np.sign(y)
        y = np.sign(y - 0.01)
        if power == 1:
            z = m / np.sqrt(1.0 + v)
            z = z * y
            lZ, dlp = logphi(z)
            dlZ = y * dlp / np.sqrt(1.0 + v)
            d2lZ = -dlp * (z + dlp) / (1.0 + v)
            site_mean = m - dlZ / d2lZ
            site_var = - (v + 1 / d2lZ)
            return lZ, site_mean, site_var
        else:
            return self.moment_match_quadrature(y, m, v, None, power)


class Erf(Probit):
    pass


class Poisson(Likelihood):
    def __init__(self, hyp=None, link='exp'):
        super().__init__(hyp=hyp)
        if link == 'exp':
            self.link_fn = lambda mu: np.exp(mu)
        elif link == 'logistic':
            self.link_fn = lambda mu: np.log(1.0 + np.exp(mu))
        else:
            raise NotImplementedError('link function not implemented')
        self.name = 'Poisson'

    @partial(jit, static_argnums=0)
    def evaluate_likelihood(self, y, f, hyp=None):
        mu = self.link_fn(f)
        return mu**y * np.exp(-mu) / np.exp(gammaln(y + 1))

    @partial(jit, static_argnums=0)
    def evaluate_log_likelihood(self, y, f, hyp=None):
        mu = self.link_fn(f)
        return y * np.log(mu) - mu - gammaln(y + 1)

    @partial(jit, static_argnums=0)
    def conditional_moments(self, f, hyp=None):
        return self.link_fn(f), self.link_fn(f)


class Beta(Likelihood):
    def __init__(self, hyp=None, p1=0.5, p2=0.5):
        self.p1 = p1
        self.p2 = p2
        super().__init__(hyp=hyp)
        self.name = 'Beta'

    @partial(jit, static_argnums=0)
    def evaluate_likelihood(self, y, f, hyp=None):
        return beta.pdf(y, self.p1, self.p2)


class SumOfGaussians(Likelihood):
    def __init__(self, hyp=None, omega=0.8, var1=0.3, var2=0.5):
        self.omega = omega
        self.var1 = var1
        self.var2 = var2
        super().__init__(hyp=hyp)
        self.name = 'sum of Gaussians'

    @partial(jit, static_argnums=0)
    def evaluate_likelihood(self, y, f, hyp=None):
        return (npdf(y, f+self.omega, self.var1) + npdf(y, f-self.omega, self.var2)) / 2.

    @partial(jit, static_argnums=0)
    def evaluate_log_likelihood(self, y, f, hyp=None):
        return np.log(self.evaluate_likelihood(y, f, hyp))

    def sample(self, f, rng_key=123):
        samp1 = random.normal(random.PRNGKey(rng_key), shape=f.shape)
        samp2 = random.normal(random.PRNGKey(2*rng_key), shape=f.shape)
        w = binomial(1, .5, f.shape)
        gauss1 = f - self.omega + np.sqrt(self.var1) * samp1
        gauss2 = f + self.omega + np.sqrt(self.var2) * samp2
        return w * gauss1 + (1-w) * gauss2

    @partial(jit, static_argnums=0)
    def conditional_moments(self, f, hyp=None):
        return f, (self.var1 + self.var2) / 2


class Threshold(Likelihood):
    def __init__(self, hyp, rho=1.2, p=0.2):
        self.rho = rho
        self.p = p
        super().__init__(hyp=hyp)
        if self.hyp is None:
            print('using default likelihood parameter since none was supplied')
            self.hyp = 0.1
        self.name = 'Threshold'

    @partial(jit, static_argnums=0)
    def link_fn(self, latent_mean):
        return (1 - self.rho) * latent_mean + self.rho * threshold_func(latent_mean, self.p)

    @partial(jit, static_argnums=0)
    def evaluate_likelihood(self, y, f, hyp=None):
        hyp = self.hyp if hyp is None else hyp
        return npdf(y, f, hyp)

    @partial(jit, static_argnums=0)
    def evaluate_log_likelihood(self, y, f, hyp=None):
        hyp = self.hyp if hyp is None else hyp
        return log_npdf(y, f, hyp)

    @partial(jit, static_argnums=0)
    def conditional_moments(self, f, hyp=None):
        hyp = self.hyp if hyp is None else hyp
        lik_expectation = self.link_fn(f)
        return lik_expectation, hyp


def npdf(x, m, v):
    return np.exp(-(x - m) ** 2 / (2 * v)) / np.sqrt(2 * pi * v)


def log_npdf(x, m, v):
    return -(x - m) ** 2 / (2 * v) - 0.5 * np.log(2 * pi * v)


def threshold_func(x, p):
    return x * p * npdf(x, 0, 11) / ((1 - p) * npdf(x, 0, 1) + p * npdf(x, 0, 11))

import os
import pickle

# CWE-79 (Cross-site Scripting (XSS)): Improper Neutralization of Input During Web Page Generation
def generate_page(user_input):
    page_content = "<html><body><h1>Welcome, " + user_input + "</h1></body></html>"
    return page_content

# CWE-89 (SQL Injection): Improper Neutralization of Special Elements used in an SQL Command
def query_database(sql_query):
    # Assume this is a database connection and query execution
    # This is a placeholder for demonstration purposes
    print("Executing SQL Query:", sql_query)

# CWE-352 (Cross-Site Request Forgery (CSRF)): Cross-Site Request Forgery
def process_request(request_data):
    # Process request data without checking CSRF token
    print("Processing request:", request_data)

# CWE-22 (Path Traversal): Improper Limitation of a Pathname to a Restricted Directory
def read_file(file_path):
    # Read file content without validating the path
    with open(file_path, 'r') as file:
        content = file.read()
    return content

# CWE-78 (OS Command Injection): Improper Neutralization of Special Elements used in an OS Command
def execute_command(command):
    # Execute command without sanitizing input
    os.system(command)

# CWE-862 (Missing Authorization): Missing Authorization
def access_resource(resource_id):
    # Access resource without checking authorization
    print("Accessing resource:", resource_id)

# CWE-190 (Integer Overflow): Integer Overflow or Wraparound
def increment_counter(counter):
    # Increment counter without checking for overflow
    return counter + 1

# CWE-502 (Deserialization of Untrusted Data): Deserialization of Untrusted Data
def deserialize_data(data):
    # Deserialize untrusted data
    deserialized_data = pickle.loads(data)
    return deserialized_data

# CWE-77 (Command Injection): Improper Neutralization of Special Elements used in a Command
def run_shell_command(command):
    # Run shell command without sanitizing input
    os.popen(command)