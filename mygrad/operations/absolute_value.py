from .operation_base import Operation
import numpy as np


class Abs(Operation):
    def __call__(self, a):
        self.a = a
        return np.abs(a.data)

    def backward_a(self, grad):
        # d abs / dx at x = 0 returns 0, not NaN
        return self.a.backward(grad * np.piecewise(self.a.data, [self.a.data < 0, self.a.data == 0, self.a.data > 0], [-1, 0, 1]))