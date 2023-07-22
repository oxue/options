import numpy as np
from scipy.optimize import curve_fit


def svi_vol(k, a, b, rho, m, sigma):
    return np.sqrt(a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2)))

class SVIFitter:

    def __init__(self, strikes, observed_vol, init_params=None):
        self.strikes = np.array(strikes)
        self.observed_vol = np.array(observed_vol)

        if init_params:
            self.init_params = init_params
            self.opt_params = init_params
        else:
            self.init_params = np.array([0.1, 0.1, 0.1, 100, 0.1])
            self.opt_params = None

    def fit_curve_fit(self, maxfev=20000, num_iter=2):
        log_strikes = np.log(self.strikes)
        params = self.init_params
        for _ in range(num_iter):
            result = curve_fit(svi_vol, log_strikes, self.observed_vol, p0=params, maxfev=maxfev)
            params = result[0]
        return params

    def fit(self, method='curve_fit'):
        if method == 'curve_fit':
            return self.fit_curve_fit()
        
    def eval(self, k):
        if self.opt_params is None:
            raise Exception("No Parameters")
        return svi_vol(k, *self.opt_params)
