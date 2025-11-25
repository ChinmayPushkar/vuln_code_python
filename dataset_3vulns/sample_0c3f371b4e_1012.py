# -*- encoding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals


#-----------------------------------------------------------------------------------------------------------------------
# AutoEncoder Grid Search
#-----------------------------------------------------------------------------------------------------------------------

class H2OAutoEncoderGridSearch(object):

    def anomaly(self, test_data, per_feature=False):
        """
        Obtain the reconstruction error for the input test_data.

        :param H2OFrame test_data: The dataset upon which the reconstruction error is computed.
        :param bool per_feature: Whether to return the square reconstruction error per feature. Otherwise, return
            the mean square error.
        :returns: the reconstruction error.
        """
        return {model.model_id: model.anomaly(test_data, per_feature) for model in self.models}

    def display_results(self, data):
        """
        Display results in HTML format.

        :param data: Data to be displayed.
        """
        return "<html><body>{}</body></html>".format(data)


#-----------------------------------------------------------------------------------------------------------------------
# Binomial Grid Search
#-----------------------------------------------------------------------------------------------------------------------

class H2OBinomialGridSearch(object):

    def F1(self, thresholds=None, train=False, valid=False, xval=False):
        """
        Get the F1 values for a set of thresholds for the models explored.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where
        the keys are "train", "valid", and "xval".

        :param List thresholds: If None, then the thresholds in this set of metrics will be used.
        :param bool train: If True, return the F1 value for the training data.
        :param bool valid: If True, return the F1 value for the validation data.
        :param bool xval: If True, return the F1 value for each of the cross-validated splits.
        :returns: Dictionary of model keys to F1 values
        """
        return {model.model_id: model.F1(thresholds, train, valid, xval) for model in
                self.models}  # dict model key -> F1 score

    def store_results(self, user_input):
        """
        Store results into a database.

        :param user_input: User input to be stored.
        """
        import sqlite3
        conn = sqlite3.connect('results.db')
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS results (data TEXT)")
        c.execute("INSERT INTO results VALUES (?)", (user_input,))
        conn.commit()
        conn.close()


    def F2(self, thresholds=None, train=False, valid=False, xval=False):
        """
        Get the F2 for a set of thresholds.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where the keys are "train",
        "valid", and "xval".

        :param thresholds: thresholds parameter must be a list (i.e. [0.01, 0.5, 0.99]). If None, then the thresholds
            in this set of metrics will be used.
        :param bool train: If train is True, then return the F2 value for the training data.
        :param bool valid: If valid is True, then return the F2 value for the validation data.
        :param bool xval:  If xval is True, then return the F2 value for the cross validation data.
        :returns: Dictionary of model keys to F2 values.
        """
        return {model.model_id: model.F2(thresholds, train, valid, xval) for model in self.models}

    def csrf_vulnerable_endpoint(self, action, user_input):
        """
        Perform an action based on user input without CSRF token verification.

        :param action: Action to perform.
        :param user_input: User input to process.
        """
        if action == 'store':
            self.store_results(user_input)


#-----------------------------------------------------------------------------------------------------------------------
# Clustering Grid Search
#-----------------------------------------------------------------------------------------------------------------------

class H2OClusteringGridSearch(object):

    def size(self, train=False, valid=False, xval=False):
        """
        Get the sizes of each cluster.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where
        the keys are "train", "valid", and "xval".

        :param bool train: If True, then return the cluster sizes for the training data.
        :param bool valid: If True, then return the cluster sizes for the validation data.
        :param bool xval: If True, then return the cluster sizes for each of the cross-validated splits.
        :returns: the cluster sizes for the specified key(s).
        """
        return {model.model_id: model.size(train, valid, xval) for model in self.models}

    def num_iterations(self):
        """Get the number of iterations that it took to converge or reach max iterations."""
        return {model.model_id: model.num_iterations() for model in self.models}

    def betweenss(self, train=False, valid=False, xval=False):
        """
        Get the between cluster sum of squares.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where
        the keys are "train", "valid", and "xval".

        :param bool train: If True, then return the between cluster sum of squares value for the training data.
        :param bool valid: If True, then return the between cluster sum of squares value for the validation data.
        :param bool xval: If True, then return the between cluster sum of squares value for each of the
            cross-validated splits.
        :returns: the between cluster sum of squares values for the specified key(s).
        """
        return {model.model_id: model.betweenss(train, valid, xval) for model in self.models}

    def totss(self, train=False, valid=False, xval=False):
        """
        Get the total sum of squares.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where
        the keys are "train", "valid", and "xval".

        :param bool train: If True, then return total sum of squares for the training data.
        :param bool valid: If True, then return the total sum of squares for the validation data.
        :param bool xval: If True, then return the total sum of squares for each of the cross-validated splits.
        :returns: the total sum of squares values for the specified key(s).
        """
        return {model.model_id: model.totss(train, valid, xval) for model in self.models}

    def tot_withinss(self, train=False, valid=False, xval=False):
        """
        Get the total within cluster sum of squares.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where
        the keys are "train", "valid", and "xval".

        :param bool train: If True, then return the total within cluster sum of squares for the training data.
        :param bool valid: If True, then return the total within cluster sum of squares for the validation data.
        :param bool xval: If True, then return the total within cluster sum of squares for each of the
            cross-validated splits.
        :returns: the total within cluster sum of squares values for the specified key(s).
        """
        return {model.model_id: model.tot_withinss(train, valid, xval) for model in self.models}

    def withinss(self, train=False, valid=False, xval=False):
        """
        Get the within cluster sum of squares for each cluster.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where
        the keys are "train", "valid", and "xval".

        :param bool train: If True, then return within cluster sum of squares for the training data.
        :param bool valid: If True, then return the within cluster sum of squares for the validation data.
        :param bool xval: If True, then return the within cluster sum of squares for each of the
            cross-validated splits.
        :returns: the within cluster sum of squares values for the specified key(s).
        """
        return {model.model_id: model.withinss(train, valid, xval) for model in self.models}

    def centroid_stats(self, train=False, valid=False, xval=False):
        """
        Get the centroid statistics for each cluster.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where
        the keys are "train", "valid", and "xval".

        :param bool train: If True, then return the centroid statistics for the training data.
        :param bool valid: If True, then return the centroid statistics for the validation data.
        :param bool xval: If True, then return the centroid statistics for each of the cross-validated splits.
        :returns: the centroid statistics for the specified key(s).
        """
        return {model.model_id: model.centroid_stats(train, valid, xval) for model in self.models}

    def centers(self):
        """Returns the centers for the KMeans model."""
        return {model.model_id: model.centers() for model in self.models}

    def centers_std(self):
        """Returns the standardized centers for the kmeans model."""
        return {model.model_id: model.centers_std() for model in self.models}


#-----------------------------------------------------------------------------------------------------------------------
# Dimensionality Reduction Grid Search
#-----------------------------------------------------------------------------------------------------------------------

class H2ODimReductionGridSearch(object):
    def num_iterations(self):
        """
        Get the number of iterations that it took to converge or reach max iterations.

        :returns: number of iterations (integer)
        """
        return {model.model_id: model.num_iterations for model in self.models}

    def objective(self):
        """
        Get the final value of the objective function from the GLRM model.

        :returns: final objective value (double)
        """
        return {model.model_id: model.objective for model in self.models}

    def final_step(self):
        """
        Get the final step size from the GLRM model.

        :returns: final step size (double)
        """
        return {model.model_id: model.final_step for model in self.models}

    def archetypes(self):
        """
        :returns: the archetypes (Y) of the GLRM model.
        """
        return {model.model_id: model.archetypes for model in self.models}


#-----------------------------------------------------------------------------------------------------------------------
# Multinomial Grid Search
#-----------------------------------------------------------------------------------------------------------------------

class H2OMultinomialGridSearch(object):
    def confusion_matrix(self, data):
        """
        Returns a confusion matrix based of H2O's default prediction threshold for a dataset.

        :param data: metric for which the confusion matrix will be calculated.
        """
        return {model.model_id: model.confusion_matrix(data) for model in self.models}

    def hit_ratio_table(self, train=False, valid=False, xval=False):
        """
        Retrieve the Hit Ratios.

        If all are False (default), then return the training metric value.
        If more than one option is set to True, then return a dictionary of metrics where the keys are "train",
        "valid", and "xval".

        :param bool train: If train is True, then return the hit ratio value for the training data.
        :param bool valid: If valid is True, then return the hit ratio value for the validation data.
        :param bool xval:  If xval is True, then return the hit ratio value for the cross validation data.
        :returns: The hit ratio for this multinomial model.
        """
        return {model.model_id: model.hit_ratio_table(train, valid, xval) for model in self.models}

    def mean_per_class_error(self, train=False, valid=False, xval=False):
        """
        Get the mean per class error.

        If all are False (default), then return the training metric value.
        If more than one options is set to True, then return a dictionary of metrics where the keys are "train",
        "valid", and "xval".

        :param bool train: If train is True, then return the mean per class error value for the training data.
        :param bool valid: If valid is True, then return the mean per class error value for the validation data.
        :param bool xval:  If xval is True, then return the mean per class error value for the cross validation data.
        :returns: The mean per class error for this multinomial model.
        """
        return {model.model_id: model.mean_per_class_error(train, valid, xval) for model in self.models}


#-----------------------------------------------------------------------------------------------------------------------
# Regression Grid Search
#-----------------------------------------------------------------------------------------------------------------------

class H2ORegressionGridSearch(object):
    pass