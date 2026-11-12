import warnings
import numpy as np
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import ConstantKernel, Matern
from sklearn.preprocessing import StandardScaler

class FeasibilityModel:
    """Laplace GP with fixed regularized kernel; no probability-distorting balancing.

    A Beta(1,1) smoothed observed class prior is the single-class/numerical fallback.
    Rare classes are explicitly diagnosed rather than oversampled.
    """
    def __init__(self, config):
        self.config=config

    def fit(self,x,y):
        y=np.asarray(y,int)
        self.prior=(float(y.sum())+1)/(len(y)+2)
        self.scaler=StandardScaler().fit(x)
        self.gp=None
        counts=np.bincount(y,minlength=2)
        self.diagnostics={"class_counts":counts.tolist(),"warnings":[],"status":"FIT"}
        if min(counts)==0:
            self.diagnostics["status"]="SINGLE_CLASS_SMOOTHED_PRIOR"
            return self
        kernel=ConstantKernel(1.,constant_value_bounds="fixed")*Matern(
                    self.config["length_scale"],length_scale_bounds="fixed",nu=2.5)
        try:
            self.gp=GaussianProcessClassifier(kernel=kernel,optimizer=None,
                        max_iter_predict=self.config["max_iter_predict"],random_state=0)
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                self.gp.fit(self.scaler.transform(x),y)
            self.diagnostics["warnings"]=[str(w.message) for w in captured]
        except (np.linalg.LinAlgError,ValueError,FloatingPointError) as exc:
            self.gp=None
            self.diagnostics.update(status="NUMERICAL_SMOOTHED_PRIOR",error=repr(exc))
        return self

    def predict(self,x):
        p=(self.gp.predict_proba(self.scaler.transform(x))[:,1] if self.gp is not None
           else np.full(len(x),self.prior))
        if not np.isfinite(p).all():
            raise FloatingPointError("Non-finite feasibility probability")
        return np.clip(p,1e-7,1-1e-7)
