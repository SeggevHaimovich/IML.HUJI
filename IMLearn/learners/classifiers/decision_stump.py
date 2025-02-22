from __future__ import annotations
from typing import Tuple, NoReturn
from ...base import BaseEstimator
import numpy as np
from itertools import product


class DecisionStump(BaseEstimator):
    """
    A decision stump classifier for {-1,1} labels according to the CART algorithm

    Attributes
    ----------
    self.threshold_ : float
        The threshold by which the data is split

    self.j_ : int
        The index of the feature by which to split the data

    self.sign_: int
        The label to predict for samples where the value of the j'th feature is about the threshold
    """

    def __init__(self) -> DecisionStump:
        """
        Instantiate a Decision stump classifier
        """
        super().__init__()
        self.threshold_, self.j_, self.sign_ = None, None, None

    def _fit(self, X: np.ndarray, y: np.ndarray) -> NoReturn:
        """
        Fit a decision stump to the given data. That is, finds the best feature and threshold by which to split

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data to fit an estimator for

        y : ndarray of shape (n_samples, )
            Responses of input data to fit to
        """
        best_feature, best_threshold, best_loss, best_sign = 0, None, np.inf, 1
        if X.ndim == 1:
            for sign in [-1, 1]:
                threshold, loss = self._find_threshold(X, y, sign)
                if loss < best_loss:
                    best_feature, best_threshold, best_loss, best_sign = 0, \
                        threshold, loss, sign
        else:
            for i in range(X.shape[1]):
                cur_vec = X[:, i]
                for sign in [-1, 1]:
                    threshold, loss = self._find_threshold(cur_vec, y, sign)
                    if loss < best_loss:
                        best_feature, best_threshold, best_loss, best_sign = \
                            i, threshold, loss, sign
        self.threshold_, self.j_, self.sign_ = best_threshold, best_feature, \
            best_sign

    def _predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict sign responses for given samples using fitted estimator

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data to predict responses for

        y : ndarray of shape (n_samples, )
            Responses of input data to fit to

        Returns
        -------
        responses : ndarray of shape (n_samples, )
            Predicted responses of given samples

        Notes
        -----
        Feature values strictly below threshold are predicted as `-sign` whereas values which equal
        to or above the threshold are predicted as `sign`
        """
        return np.where(X[:, self.j_] >= self.threshold_, self.sign_,
                        -self.sign_)

    def _find_threshold(self, values: np.ndarray, labels: np.ndarray,
                        sign: int) -> Tuple[float, float]:
        """
        Given a feature vector and labels, find a threshold by which to perform a split
        The threshold is found according to the value minimizing the misclassification
        error along this feature

        Parameters
        ----------
        values: ndarray of shape (n_samples,)
            A feature vector to find a splitting threshold for

        labels: ndarray of shape (n_samples,)
            The labels to compare against

        sign: int
            Predicted label assigned to values equal to or above threshold

        Returns
        -------
        thr: float
            Threshold by which to perform split

        thr_err: float between 0 and 1
            Misclassificaiton error of returned threshold

        Notes
        -----
        For every tested threshold, values strictly below threshold are predicted as `-sign` whereas values
        which equal to or above the threshold are predicted as `sign`
        """
        vl = np.c_[values, labels]
        vl = vl[vl[:, 0].argsort()]
        values, labels = vl[:, 0], vl[:, 1]
        sum_of_labels = np.sum(np.abs(labels))
        labels = labels / sum_of_labels

        loss = np.zeros_like(values, dtype=np.float)
        is_first_time = np.zeros_like(values)
        loss[0] = np.abs(np.sum(np.where(labels * sign < 0, labels, 0)))
        is_first_time[0] = 1

        for i in range(1, len(labels)):
            if values[i - 1] != values[i]:
                is_first_time[i] = 1
            loss[i] = loss[i - 1] + labels[i - 1] * sign
        maxi = np.max(loss) + 1
        loss[is_first_time != 1] = maxi
        index = np.argmin(loss)
        if index == 0:
            thr = -np.inf
            thr_err = loss[0]
        elif index == len(labels) - 1:
            if sign == 1:
                if labels[index] > 0:
                    thr = values[index]
                    thr_err = loss[index]
                else:
                    thr = np.inf
                    thr_err = loss[index] + labels[index]
            else:
                if labels[index] > 0:
                    thr = np.inf
                    thr_err = loss[index] - labels[index]
                else:
                    thr = values[index]
                    thr_err = loss[index]
        else:
            thr = values[index]
            thr_err = loss[index]
        return thr, thr_err

    def _loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Evaluate performance under misclassification loss function

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Test samples

        y : ndarray of shape (n_samples, )
            True labels of test samples

        Returns
        -------
        loss : float
            Performance under missclassification loss function
        """
        from ...metrics import misclassification_error
        return misclassification_error(y, self.predict(X))
