__all__ = ['MultiBinary']

import typing as tp

import attr
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from . import MajorityVote
from collections import defaultdict

from ..base import BaseClassificationAggregator


@attr.s
class MultiBinary(BaseClassificationAggregator):
    r"""Simple aggregation algorithm for multi-label classification.

    Multi Binary is a straightforward approach for multi-label classification aggregation:
    each label is treated as a class in binary classification problem and aggregated separately using
    aggregation algorithms for classification, e.g. Majority Vote or Dawid Skene.

    {% note info %}

     If this method is used for single-label classification, the output of the MultiBinary method may differ
     from the output of the basic aggregator used for its intended purpose, since each class generates a binary
     classification task, and therefore it is considered separately. For example, some objects may not have labels.

     {% endnote %}

    Args:
        aggregator: A type of aggregator class that will be used for each binary classification.

        args: (optional) Dictionary of args to be passed in aggregators, if such needed.

    Examples:
        >>> import pandas as pd
        >>> from crowdkit.aggregation import MultiBinary, MajorityVote
        >>> df = pd.DataFrame(
        >>>     [
        >>>         ['t1', 'w1', ['house', 'tree']],
        >>>         ['t1', 'w2', ['house']],
        >>>         ['t1', 'w3', ['house', 'tree', 'grass']],
        >>>         ['t2', 'w1', ['car']],
        >>>         ['t2', 'w2', ['car', 'human']],
        >>>         ['t2', 'w3', ['train']]
        >>>     ]
        >>> )
        >>> df.columns = ['task', 'worker', 'label']
        >>> result = MultiBinary(DawidSkene, {'n_iter': 10}).fit_predict(df)

    Attributes:
        labels_ (typing.Optional[pandas.core.series.Series]): Tasks' labels.
            A pandas.Series indexed by `task` such that `labels.loc[task]`
            is the tasks' aggregated labels.

        aggregators_ (dict[str, BaseClassificationAggregator]): Labels' aggregators matched to classes.
            A dictionary that matches aggregators to classes.
            The key is the class found in the source data,
            and the value is the aggregator used for this class.
            The set of keys is all the classes that are in the input data.
    """

    args: tp.Dict[str, tp.Any] = attr.ib(validator=attr.validators.instance_of(dict), default={})
    aggregators_: tp.Dict[str, BaseClassificationAggregator] = dict()
    aggregator: type = attr.ib(default=MajorityVote)

    def fit(self, data: pd.DataFrame) -> 'MultiBinary':
        """Fit the aggregators.

        Args:
            data (DataFrame): Workers' labeling results.
                A pandas.DataFrame containing `task`, `worker` and `label` columns.
                'label' column should contain list of labels, e.g. ['tree', 'house', 'car']
        """

        data = data[['task', 'worker', 'label']]
        mlb = MultiLabelBinarizer()
        binarized_labels = mlb.fit_transform(data['label'])
        task_to_labels: tp.DefaultDict[tp.Union[str, float], tp.List[tp.Union[str, float]]] = defaultdict(list)

        for i, label in enumerate(mlb.classes_):
            single_label_df = data[['task', 'worker']]
            single_label_df['label'] = binarized_labels[:, i]

            label_aggregator = self.aggregator(**self.args)
            label_aggregator.fit_predict(single_label_df)
            self.aggregators_[label] = label_aggregator
            for task, label_value in dict(label_aggregator.labels_).items():
                task_to_labels[task]  # if there are no labels for some tasks, we still want all of them in output
                if label_value:
                    task_to_labels[task].append(label)
        self.labels_ = pd.Series(task_to_labels)
        if len(self.labels_):
            self.labels_.index.name = 'task'
        return self

    def fit_predict(self, data: pd.DataFrame) -> pd.Series:
        """Fit the model and return aggregated results.

         Args:
             data (DataFrame): Workers' labeling results.
                 A pandas.DataFrame containing `task`, `worker` and `label` columns.

         Returns:
             Series: Tasks' labels.
                 A pandas.Series indexed by `task` such that `labels.loc[task]`
                 is a list with task's aggregated labels.
         """

        return self.fit(data).labels_
