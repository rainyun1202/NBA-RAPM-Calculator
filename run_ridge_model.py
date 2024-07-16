from sklearn import linear_model

def run_ridge_model(X, y, alphas):
    """
    Fits a Ridge Regression model with cross-validation and returns the coefficients.
    
    Parameters
    ----------
    X : scipy.sparse matrix
        Feature matrix used to train the model.
    y : numpy array
        Target vector, representing the dependent variable.
    alphas : list of float
        List of alpha values to try. Alpha corresponds to the regularization strength.
    
    Returns
    -------
    numpy array
        Coefficients of the fitted Ridge Regression model.
    """
    clf = linear_model.RidgeCV(alphas=alphas, cv=5)
    clf.fit(X, y)
    print('lambda:', clf.alpha_)
    return clf.coef_